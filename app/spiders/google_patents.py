# -*- coding: utf-8 -*-
import json
import logging
from scrapy.spiders import Spider
from scrapy.http import Request

from app.loaders import GooglePatentsLoader


logger = logging.getLogger(__name__)


class GooglePatentsSpider(Spider):
    name = "google_patents"
    allowed_domaines = ['patents.google.com']
    start_urls = [
        'https://patents.google.com/xhr/query?q=%7B%22kg%22%3A%5B%7B%22kw%22%3A%5B%7B%22text%22%3A%22'
        'stirling%20engine%22%7D%5D%7D%5D%2C%22clustered_restrict%22%3Afalse%7D&exp='
    ]
    query = {
        'kg':[
            { 'kw':[
                { 'text':'stirling'
                 },{ 'text':'heating' }
            ]
            },{ 'kw':[
                { 'text':'engine'
                 },{ 'text':'generator'
                    },{ 'text':'machine'
                       },{ 'text':'system'}
            ]
            },{ 'kw':[
                { 'text':'home'
                 },{ 'text':'house'
                    },{ 'text':'habitat'
                       },{ 'text':'domestic' }
            ]
            },{ 'kw':[
                { 'text':'energy'
                 },{ 'text':'electricity'
                    },{ 'text':'electric'
                       },{ 'text':'current supply'}
            ]
            },{ 'kw':[
                { 'text':'kilowatt'
                 },{ 'text':'1kW'}
            ]
            },{
                'kw':[
                    {
                        'text':'independant'
                    }
                ]
            },{
                'kw':[
                    {
                        'text':'-vehicle'
                    }
                ]
            }
        ],
        'clustered_restrict':false,
        'page':1
    }

    def parse(self, response):
        try:
            results = json.loads(response.body_as_unicode())['results']
        except KeyError, e:
            logger.exception(e)
            return

        clusters = results.pop('cluster')
        for cluster in clusters:
            try:
                patents = cluster['result']
            except KeyError, e:
                logger.exception(e)
                continue

            for patent in patents:
                try:
                    patent = patent['patent']
                    patent_number = patent['publication_number']
                except KeyError, e:
                    logger.exception(e)
                    continue

                if patent_number:
                    yield Request(
                        url="https://patents.google.com/xhr/result?patent_id=%s&lang=en&exp=" % patent_number,
                        callback=self.parse_patent,
                        meta={'patent': patent}
                    )

    def parse_patent(self, response):
        patent = response.meta['patent']
        loader = GooglePatentsLoader(response=response)

        try:
            loader.add_value('language', patent['language'])
            loader.add_value('country_code', patent['country_code'])
            loader.add_value('publication_number', patent['publication_number'])
            loader.add_value('title', patent['title'])
            loader.add_value('filing_date', patent['filing_date'])
            loader.add_value('publication_date', patent['publication_date'])
            loader.add_value('priority_date', patent['priority_date'])
            loader.add_value('grant_date', patent['grant_date'])
        except KeyError, e:
            logger.error(e)
            return

        loader.add_css('inventors', '.important-people a[add-inventor]::text')
        loader.add_css('assignees', '.important-people a[add-assignee]::text')
        loader.add_css('pdf', '.knowledge-card-action-bar a[href]::attr("href")')
        loader.add_css('external_links', '.links dd a[href^=http]::attr("href")')

        images = loader.get_css('#figures *::attr("images")')
        try:
            images = json.loads(images[0])
            for img in images:
                loader.add_value('images', 'https://patentimages.storage.googleapis.com/%s' % img)
        except (IndexError, ValueError), e:
            pass

        classes = loader.get_css('#classifications *::attr("classes")')
        try:
            classes = json.loads(classes[0])
            for classification in classes:
                leaf = classification[-1]
                loader.add_value('classifications', (leaf['Code'], leaf['Description']))
        except (IndexError, ValueError), e:
            pass

        loader.add_css('citations', '#patentCitations+table tbody td a::text')
        loader.add_css('cited_by', '#citedBy+table tbody td a::text')
        loader.add_css('legal_events', '#legalEvents+table tbody td.nowrap::text')

        loader.add_css('abstract', '#abstract .abstract::text')
        loader.add_css('description', '#descriptionText *::text')
        loader.add_css('claims', '#claimsText *::text')

        return loader.load_item()

