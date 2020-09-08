# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import mysql.connector
from scrapy.exceptions import DropItem

class SpidersPipeline(object):

    def __init__(self):
        self.create_connection()
        self.ids_seen = set()

    def create_connection(self):
        # Account settings for AWS RDS
        self.conn = mysql.connector.connect(
            host ='mooqledb.cs2xbuollx3x.ap-southeast-1.rds.amazonaws.com',
            user = 'admin',
            passwd = 'mooqledb',
            database = 'mooqledb',
            use_pure = True
        )
        self.curr = self.conn.cursor()
    
    def process_item(self, item, spider):
        try:
            if item['url_from'] in self.ids_seen:
                # Remove duplicate URL
                raise DropItem("Duplicate item found: %s" % item)
            else:
                self.ids_seen.add(item['url_from'])    
                self.store_db(item)
                self.del_duplicate(item)
                return item
        # if database connection lost, close spider
        except mysql.connector.Error:
            spider.crawler.engine.close_spider(self, reason='error')
            print("Database connection lost")

    def store_db(self,item):
        self.curr.execute("""insert into webcontent (text, webLinks) values (%s,%s) """,(
            item['text'],
            item['url_from']
        ))
        self.conn.commit()

    def del_duplicate(self,item):
        # Remove duplicate that was missed by deltafetch
         self.curr.execute('delete t1 from mooqledb.webcontent t1 inner join mooqledb.webcontent t2 where t2.id > t1.id and t1.webLinks = t2.webLinks;')
         self.conn.commit()
