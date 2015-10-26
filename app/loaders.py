# -*- coding: utf-8 -*-

from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Identity, Join

from app.items import GooglePatentsItem


class GooglePatentsLoader(ItemLoader):
    default_item_class = GooglePatentsItem

    default_input_processor = MapCompose(unicode.strip)
    default_output_processor = TakeFirst()

    inventors_out = Identity()
    assignees_out = Identity()
    external_links_out = Identity()
    images_out = Identity()
    classifications_out = Identity()
    citations_out = Identity()
    cited_by_out = Identity()
    legal_events_out = Identity()

    abstract_out = Join()
    description_out = Join()
    claims_out = Join()
