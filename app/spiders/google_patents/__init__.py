# -*- coding: utf-8 -*-

from scrapy.http import Request
from scrapy.spiders import Spider
from scrapy.selector import Selector

from app.loaders import GooglePatentsLoader


class GooglePatentsSpider(Spider):
    allowed_domaines = ['patents.google.com']
    patent_url = 'https://patents.google.com/xhr/result?lang=en&patent_id={id}'

    def parse(self, response):
        loader = GooglePatentsLoader(response=response)

        references = self.parse_html(loader)

        loader.add_value('depth', response.meta['depth'])

        self.logger.info('{}/{}: Found {} patents to explore in {}'.format(
            response.meta['depth'],
            self.settings.get('MAX_DEPTH', 0),
            len(references),
            loader.get_output_value('publication_number')
        ))

        if response.meta['depth'] < self.settings.get('MAX_DEPTH', 0):
            for patent_id in references:
                yield Request(
                    url=self.patent_url.format(id=patent_id),
                    callback=self.parse,
                    meta={'depth': response.meta['depth'] + 1}
                )

        yield loader.load_item()

    def parse_html(self, loader):
        loader.add_css('publication_number', 'dl dd[itemprop=publicationNumber]::text')
        loader.add_css('title', 'h1[itemprop=title]::text')

        self.logger.info('Parsing patent {}: {}'.format(
            loader.get_output_value('publication_number'),
            loader.get_output_value('title')
        ))

        loader.add_css('pdf', 'a[itemprop=pdfLink]::attr("href")')

        loader.add_css('priority_date', 'dd time[itemprop=priorityDate]::text')
        loader.add_css('filing_date', 'dd time[itemprop=filingDate]::text')
        loader.add_css('publication_date', 'dd time[itemprop=publicationDate]::text')
        loader.add_css('grant_date', 'dd time[itemprop=grantDate]::text')

        loader.add_css('inventors', 'dd[itemprop=inventor]::text')
        loader.add_css('assignees', 'dd[itemprop=assigneeOriginal]::text')

        loader.add_css('external_links', 'li[itemprop=links] a[href^=http]::attr("href")')
        loader.add_css('images', 'li[itemprop=images] meta[itemprop=full]::attr("content")')

        classifications = loader.get_css('ul[itemprop=cpcs] li:last-child')
        for classification in classifications:
            html = Selector(text=classification)
            code = html.css('*[itemprop=Code]::text').extract_first()
            desc = html.css('*[itemprop=Description]::text').extract_first()
            loader.add_value('classifications', u'{}: {}'.format(code, desc))

        legal_events = loader.get_css('tr[itemprop=legalEvents]')
        for legal_event in legal_events:
            html = Selector(text=legal_event)
            date = html.css('*[itemprop=date]::text').extract_first()
            code = html.css('*[itemprop=code]::text').extract_first()
            title = html.css('*[itemprop=title]::text').extract_first()
            loader.add_value('legal_events', u'({}) {}: {}'.format(date, code, desc))

        loader.add_css('abstract', 'section[itemprop=abstract] .abstract::text')
        loader.add_css('description', 'section[itemprop=description] .description-line::text')
        loader.add_css('claims', 'section[itemprop=claims] .claim-text::text')

        loader.add_css('citations', 'tr[itemprop=backwardReferences] span[itemprop=publicationNumber]::text')
        loader.add_css('cited_by', 'tr[itemprop=forwardReferences] span[itemprop=publicationNumber]::text')

        return loader.get_output_value('citations') + loader.get_output_value('cited_by')
