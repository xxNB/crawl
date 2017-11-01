# -*- coding: utf-8 -*-
"""
Created on 2017/10/28 下午12:56
@author: SimbaZhang
"""

import requests
from pymongo import MongoClient as mc
import json
import time
from utils.log import logger
client = mc('127.0.0.1', 27017)
db = client['review']['all_movie_id']


class MoveId(object):
    def __init__(self):
        self.url = 'https://movie.douban.com/j/new_search_subjects?sort=T&range=%s, %s&tags=电影&start=%s'
        self.header = {'User-Agent':"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
                        'Referer':'https://movie.douban.com/tag/'}

    def process(self):
        ix = 0
        for i in range(10):
            page = 0
            logger.info('抓取%s-%s分' % (i, i + 1))
            while True:
                url = self.url % (i, i + 1, page)
                json_text = json.loads(requests.get(url, headers=self.header).text)
                print(json_text)
                if json_text['data']:
                    for items in json_text['data']:
                        item = {'movie': items['title'], 'id': items['id'], 'content': items}
                        dbItem = db.find_one({'id': items['id']})
                        ix += 1
                        if dbItem:
                            pass
                        else:
                            db.insert(item)
                    time.sleep(1)
                    page += 20
                    if ix % 100 == 0:
                        logger.info('has been inserted %s' % ix)
                    return
                break

if __name__ == '__main__':
    res = MoveId()
    res.process()
