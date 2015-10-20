# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class GooglePatentsItem(Item):
    uid = Field()
    title = Field()
    inventor = Field()
    assignee = Field()
    legal_status = Field()
    pdf = Field()
    priority_date = Field()
    filing_date = Field()
    publication_date = Field()
    grant_date = Field()
    external_links = Field()
    abstract = Field()
    images = Field()
    classifications = Field()
    description = Field()
    claims = Field()
    citations = Field()
    cited_by = Field()
    legal_events = Field()
