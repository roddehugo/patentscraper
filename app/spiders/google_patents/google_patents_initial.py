# -*- coding: utf-8 -*-

from scrapy.http import Request

from app.spiders.google_patents import GooglePatentsSpider


class GooglePatentsInitialSpider(GooglePatentsSpider):
    name = 'GooglePatentsInitial'
    patents = [
        'US8735773B2',
        # 'US8377129B2',
        # 'US4904268A'
    ]

    def start_requests(self):
        for patent_id in self.patents:
            yield Request(
                url=self.patent_url.format(id=patent_id),
                callback=self.parse,
                meta={'depth': 0}
            )
