# -*- coding: utf-8 -*-
import json
import logging
from scrapy.spiders import Spider
from scrapy.http import Request

from app.loaders import GooglePatentsLoader


logger = logging.getLogger(__name__)


class GooglePatentsInitialSpider(Spider):
    name = 'google_patents_initial'
    allowed_domaines = ['patents.google.com']
    patent_url = 'https://patents.google.com/xhr/result?lang=en&patent_id=%s'
    image_url = 'https://patentimages.storage.googleapis.com/%s'
    # interesting_patents = [
        # 'US20110025055A1',
        # 'CA2468459A1',
        # 'US7459799',
        # 'US20050052029',
        # 'EP1456590B1',
        # 'US6971236',
        # 'US6161381'
    # ]
    interesting_patents = [
        # Piston
        'US4458489',
        'US4036018',
        'US4669736',
        'US8215112',
        'US20150167567',
        'WO2015138953',
        'WO1983002300',
        # Rhombic
        'US3520285',
        'US3431788',
        'US20060283186',
        # Vilebrequin
        'US5816201',
    ]
    MAX_DEPTH = 1

    def start_requests(self):
        for patent_number in self.interesting_patents:
            yield Request(
                url=self.patent_url % patent_number,
                callback=self.parse,
                meta={'depth': 0}
            )

    def parse(self, response):
        loader = GooglePatentsLoader(response=response)

        loader.add_css('publication_number', '.knowledge-card h2::text')
        loader.add_css('title', '#title::text')

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

        loader.add_css('legal_events', '#legalEvents+table tbody td.nowrap::text')

        loader.add_css('abstract', '#abstract .abstract::text')
        loader.add_css('description', '#descriptionText *::text')
        loader.add_css('claims', '#claimsText *::text')
        loader.add_value('depth', response.meta['depth'])

        if response.meta['depth'] < self.MAX_DEPTH:
            loader.add_css('citations', '#patentCitations+table tbody td a::text')
            loader.add_css('cited_by', '#citedBy+table tbody td a::text')
            patents_linked = \
                loader.get_output_value('citations') + \
                loader.get_output_value('cited_by')

            for patent_number in patents_linked:
                yield Request(
                    url=self.patent_url % patent_number,
                    callback=self.parse,
                    meta={'depth': response.meta['depth'] + 1}
                )

        logger.error('Patent %s at depth %d',
                    loader.get_output_value('publication_number'),
                    loader.get_output_value('depth'))
        yield loader.load_item()
