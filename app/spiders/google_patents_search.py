# -*- coding: utf-8 -*-
import json
import logging
import urllib
from scrapy.spiders import Spider
from scrapy.http import Request

from app.loaders import GooglePatentsLoader


logger = logging.getLogger(__name__)


class GooglePatentsSearchSpider(Spider):
    name = 'google_patents_search'
    allowed_domaines = ['patents.google.com']
    search_url = 'https://patents.google.com/xhr/query?%s'
    patent_url = 'https://patents.google.com/xhr/result?lang=en&patent_id=%s'
    image_url = 'https://patentimages.storage.googleapis.com/%s'
    query = {
        'q': {
            'kg': [
                {'kw': [
                    {'text': 'stirling engine'},
                    {'text': 'heat and power unit'},
                {'kw': [
                    {'text': 'domestic'}]},
                {'kw': [
                    {'text': '1kW'}]},
                {'kw': [
                    {'text': 'dchp'}]},
                {'kw': [
                    {'text': '-vehicle'}]},
                {'kw': [
                    {'text': '-plant'}]}
            ],
            'clustered_restrict': False,
            'page': 0
        }
    }

    def query_string(self, query):
        return urllib.urlencode(query).replace('%27', '%22').replace('+', '').replace('False', 'false')

    def start_requests(self):
        for page in range(0, 100):
            query = self.query
            query['q']['page'] = page
            yield self.make_requests_from_url(self.search_url % self.query_string(query))

    def parse(self, response):
        try:
            results = json.loads(response.body_as_unicode())['results']
            logger.info('Parsing page %d', results['num_page'])
        except KeyError, e:
            logger.error(e)
            yield None

        clusters = results.pop('cluster')
        for cluster in clusters:
            try:
                patents = cluster['result']
            except KeyError, e:
                logger.error(e)
                continue

            for patent in patents:
                try:
                    patent = patent['patent']
                    patent_number = patent['publication_number']
                except KeyError, e:
                    logger.error(e)
                    continue

                if patent_number:
                    yield Request(
                        url=self.patent_url % patent_number,
                        callback=self.parse_patent
                    )

    def parse_patent(self, response):
        loader = GooglePatentsLoader(response=response)

        loader.add_css('publication_number', '.knowledge-card h2::text')
        loader.add_css('title', '#title::text')
        logger.info('Parsing patent %s', loader.get_output_value('publication_number'))

        dates = loader.get_css('.key-dates dd *::text')
        try:
            loader.add_value('filing_date', dates[0])
            loader.add_value('publication_date', dates[3])
            loader.add_value('priority_date', dates[4])
            loader.add_value('grant_date', dates[5])
        except IndexError:
            pass

        loader.add_css('inventors', '.important-people a[add-inventor]::text')
        loader.add_css('assignees', '.important-people a[add-assignee]::text')
        loader.add_css('pdf', '.knowledge-card-action-bar a[href]::attr("href")')
        loader.add_css('external_links', '.links dd a[href^=http]::attr("href")')

        images = loader.get_css('#figures *::attr("images")')
        try:
            images = json.loads(images[0])
            for img in images:
                loader.add_value('images', self.image_url % img)
        except (IndexError, ValueError):
            pass

        classes = loader.get_css('#classifications *::attr("classes")')
        try:
            classes = json.loads(classes[0])
            for classification in classes:
                leaf = classification[-1]
                loader.add_value('classifications', (leaf['Code'], leaf['Description']))
        except (IndexError, ValueError):
            pass

        loader.add_css('citations', '#patentCitations+table tbody td a::text')
        loader.add_css('cited_by', '#citedBy+table tbody td a::text')
        loader.add_css('legal_events', '#legalEvents+table tbody td.nowrap::text')

        loader.add_css('abstract', '#abstract .abstract::text')
        loader.add_css('description', '#descriptionText *::text')
        loader.add_css('claims', '#claimsText *::text')

        patents_linked = \
            loader.get_output_value('citations') + \
            loader.get_output_value('cited_by')

        for patent_number in patents_linked:
            yield Request(
                url=self.patent_url % patent_number,
                callback=self.parse_patent
            )

        yield loader.load_item()
