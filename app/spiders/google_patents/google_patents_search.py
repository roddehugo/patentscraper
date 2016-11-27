# -*- coding: utf-8 -*-

import json
import urllib
from scrapy.spiders import Spider
from scrapy.http import Request

from app.loaders import GooglePatentsLoader
from app.spiders.google_patents import GooglePatentsSpider


class GooglePatentsSearchSpider(GooglePatentsSpider):
    name = 'GooglePatentsSearch'
    search_url = 'https://patents.google.com/xhr/query?{qs}'
    query = {
        'q': {
            'kg': [
                {'kw': [
                    {'text': 'stirling engine'},
                    {'text': 'heat and power unit'}]},
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
            yield Request(
                url=self.search_url.format(qs=self.query_string(query)),
                callback=self.parse_search,
                meta={'depth': 0}
            )

    def parse_search(self, response):
        try:
            results = json.loads(response.body_as_unicode())['results']
            self.logger.info('Parsing page %d', results['num_page'])
        except KeyError, e:
            self.logger.error(e)
            yield None

        clusters = results.pop('cluster')
        for cluster in clusters:
            try:
                patents = cluster['result']
            except KeyError, e:
                self.logger.error(e)
                continue

            for patent in patents:
                try:
                    patent = patent['patent']
                    patent_id = patent['publication_number']
                except KeyError, e:
                    self.logger.error(e)
                    continue

                yield Request(
                    url=self.patent_url.format(id=patent_id),
                    callback=self.parse
                )
