# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging
import pymongo
from requests.exceptions import ConnectionError
from scrapy.exceptions import DropItem, CloseSpider
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
        patent_args = {'size': 10, 'red': 0, 'green': 0, 'blue': 1}
        patent_node = Node(item['publication_number'], **patent_args)
        patent_node.property['title'] = item.get('title')
        patent_node.property['filing_date'] = item.get('filing_date')
        patent_node.property['publication_date'] = item.get('publication_date')
        patent_node.property['priority_date'] = item.get('priority_date')
        patent_node.property['grant_date'] = item.get('grant_date')
        patent_node.property['pdf'] = item.get('pdf')

        for citation in item.get('citations', []):
            citation_node = Node(citation, **patent_args)
            self.gephi.add_node(citation_node)
            self.gephi.add_edge(Edge(patent_node, citation_node, True))

        for cited_by in item.get('cited_by', []):
            cited_by_node = Node(cited_by, **patent_args)
            self.gephi.add_node(cited_by_node)
            self.gephi.add_edge(Edge(cited_by_node, patent_node, True))

        inventor_args = {'size': 5, 'red': 1, 'green': 0, 'blue': 0}
        for inventor in item.get('inventors', []):
            inventor_node = Node(inventor, **inventor_args)
            self.gephi.add_node(inventor_node)
            self.gephi.add_edge(Edge(inventor_node, patent_node, True))

        assignee_args = {'size': 5, 'red': 0, 'green': 1, 'blue': 0}
        for assignee in item.get('assignees', []):
            assignee_node = Node(assignee, **assignee_args)
            self.gephi.add_node(assignee_node)
            self.gephi.add_edge(Edge(assignee_node, patent_node, True))

        try:
            self.gephi.commit()
        except ConectionError, e:
            logger.error(e)

        return item


class MongoPipeline(object):

    collection_name = 'items'

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

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[self.collection_name].insert(dict(item))
        return item
