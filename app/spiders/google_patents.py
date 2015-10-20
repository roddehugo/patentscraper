# -*- coding: utf-8 -*-

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Spider
from scrapy.selector import Selector


class GooglePatentsSpider(Spider):
    name = "google_patents"
    allowed_domaines = ['patents.google.com']
    start_urls = [
        'https://patents.google.com/?q=stirling+engine&clustered=false'
    ]

    def parse(self, response):
        """
        The lines below is a spider contract. For more info see:
        http://doc.scrapy.org/en/latest/topics/contracts.html
        @url https://patents.google.com/?q=stirling+engine&clustered=false
        @scrapes item url
        """
        sel = Selector(response)
        patents_urls = sel.xpath('//search-result-item//a/@href').extract()
        import ipdb; ipdb.set_trace() ### XXX BREAKPOINT

        for purl in patents_urls:
            print purl


        return items
