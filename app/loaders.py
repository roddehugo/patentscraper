# -*- coding: utf-8 -*-

from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose


class GooglePatentLoader(ItemLoader):

    default_input_processor = MapCompose(unicode.strip)
    default_output_processor = TakeFirst()
