# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging
import pymongo
from requests.exceptions import ConnectionError
from scrapy.exceptions import DropItem
from GephiStreamer import Node, Edge, GephiStreamerManager


logger = logging.getLogger(__name__)


class DuplicatesPipeline(object):

    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        if item['publication_number'] in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.ids_seen.add(item['publication_number'])
            return item


class GephiPipeline(object):

    def __init__(self, gephi_uri, gephi_ws):
        self.gephi_uri = gephi_uri
        self.gephi_ws = gephi_ws
        self.nodes = set()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            gephi_uri=crawler.settings.get('GEPHI_URI'),
            gephi_ws=crawler.settings.get('GEPHI_WS')
        )

    def open_spider(self, spider):
        self.gephi = GephiStreamerManager(iGephiUrl=self.gephi_uri, iGephiWorkspace=self.gephi_ws)
        logger.info('GephiStream connected %s', self.gephi)

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        patent_args = {'size': 5, 'red': 1, 'green': 0, 'blue': 0}
        patent_node = Node(item['publication_number'], **patent_args)
        patent_node.property['type'] = 'patent'
        patent_node.property['title'] = item.get('title')
        patent_node.property['filing_date'] = item.get('filing_date')
        patent_node.property['publication_date'] = item.get('publication_date')
        patent_node.property['priority_date'] = item.get('priority_date')
        patent_node.property['grant_date'] = item.get('grant_date')
        patent_node.property['pdf'] = item.get('pdf')
        if item['publication_number'] in self.nodes:
            self.gephi.change_node(patent_node)
        else:
            self.gephi.add_node(patent_node)

        link_args = {'size': 5, 'red': 0, 'green': 0, 'blue': 1}
        for citation in item.get('citations', []):
            citation_node = Node(citation, **link_args)
            citation_node.property['type'] = 'link'
            self.gephi.add_node(citation_node)
            self.gephi.add_edge(Edge(patent_node, citation_node, True))
            self.nodes.add(citation)

        for cited_by in item.get('cited_by', []):
            cited_by_node = Node(cited_by, **link_args)
            cited_by_node.property['type'] = 'link'
            self.gephi.add_node(cited_by_node)
            self.gephi.add_edge(Edge(cited_by_node, patent_node, True))
            self.nodes.add(cited_by)

        entity_args = {'size': 5, 'red': 0, 'green': 1, 'blue': 0}
        entities = set(item.get('inventors', []) + item.get('assignees', []))
        for entity in entities:
            entity_node = Node(entity, **entity_args)
            entity_node.property['type'] = 'entity'
            self.gephi.add_node(entity_node)
            self.gephi.add_edge(Edge(entity_node, patent_node, True))

        try:
            self.gephi.commit()
        except ConnectionError, e:
            logger.error(e)

        self.nodes.add(item['publication_number'])
        return item


class MongoPipeline(object):

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.collection_name = spider.name
        if self.collection_name in self.db.collection_names():
            self.db[self.collection_name].drop()

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[self.collection_name].insert(dict(item))
        return item
