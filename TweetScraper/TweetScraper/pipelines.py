# coding:utf-8
from scrapy.conf import settings
import logging
import pymongo
import json
import os

from TweetScraper.items import Tweet, User
from TweetScraper.utils import mkdirs


logger = logging.getLogger(__name__)

class SaveToMongoPipeline(object):
    # 存储到数据库
    def __init__(self):
        connection = pymongo.MongoClient(settings['MONGODB_SERVER'], settings['MONGODB_PORT'])
        db = connection[settings['MONGODB_DB']]
        self.tweetCollection = db[settings['MONGODB_TWEET_COLLECTION']]
        self.userCollection = db[settings['MONGODB_USER_COLLECTION']]
        self.tweetCollection.ensure_index([('ID', pymongo.ASCENDING)], unique=True, dropDups=True)
        self.userCollection.ensure_index([('ID', pymongo.ASCENDING)], unique=True, dropDups=True)


    def process_item(self, item, spider):
        if isinstance(item, Tweet):
            dbItem = self.tweetCollection.find_one({'ID': item['ID']})
            if dbItem:
                pass
            else:
                self.tweetCollection.insert_one(dict(item))
                logger.debug("add tweet:%s" %item['url'])

        elif isinstance(item, User):
            dbItem = self.userCollection.find_one({'ID': item['ID']})
            if dbItem:
                pass
            else:
                self.userCollection.insert_one(dict(item))
                logger.debug("add user:%s" %item['screen_name'])

        else:
            logger.info("not confuse！ type = %s" %type(item))



class SaveToFilePipeline(object):
    ''' 存储数据到本地 '''
    def __init__(self):
        self.saveTweetPath = settings['SAVE_TWEET_PATH']
        self.saveUserPath = settings['SAVE_USER_PATH']
        mkdirs(self.saveTweetPath) # 确保路径存在
        mkdirs(self.saveUserPath)


    def process_item(self, item, spider):
        if isinstance(item, Tweet):
            savePath = os.path.join(self.saveTweetPath, item['ID'])
            if os.path.isfile(savePath):
                pass
            else:
                self.save_to_file(item, savePath)
                logger.debug("add tweet:%s" %item['url'])

        elif isinstance(item, User):
            savePath = os.path.join(self.saveUserPath, item['ID'])
            if os.path.isfile(savePath):
                pass
            else:
                self.save_to_file(item, savePath)
                logger.debug("add user:%s" %item['screen_name'])

        else:
            logger.info(" not confuse! type = %s" %type(item))


    def save_to_file(self, item, fname):

        with open(fname,'w') as f:
            json.dump(dict(item), f)
