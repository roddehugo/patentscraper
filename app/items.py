# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class GooglePatentsItem(Item):
    publication_number = Field()
    title = Field()
    filing_date = Field()
    publication_date = Field()
    priority_date = Field()
    grant_date = Field()
    inventors = Field()
    assignees = Field()
    pdf = Field()
    external_links = Field()
    images = Field()
    classifications = Field()
    citations = Field()
    cited_by = Field()
    legal_events = Field()
    leget_status = Field()
    abstract = Field()
    description = Field()
    claims = Field()
    depth= Field()
