# -*- coding: utf-8 -*-
"""
Created on 2017/10/28 下午12:57
@author: SimbaZhang
"""

import requests
import time
import re
from utils.log import logger
from pymongo import MongoClient as mc
from bs4 import BeautifulSoup as bs
client = mc('127.0.0.1', 27017)
db = client['review']['all_book_id']

class BookId(object):
    def __init__(self):
        self.start_url = 'https://book.douban.com/tag/?view=type&icn=index-sorttags-hot'
        self.header1 = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
        }
        self.header2 = {
            'Host': 'book.douban.com',
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
        }

    def get_book_type(self):
        html = requests.get(self.start_url, headers=self.header1).text
        soup = bs(html, 'lxml')
        types = soup.select('#content > div > div.article > div > div > table > tbody > tr > td > a')
        types = map(lambda x: x.get_text().strip(), types)
        select = True
        for type in types:
            if select:
                if re.match(r'管理', type):
                    select = False
                    yield type
            else:
                yield type

    def process(self):
        count = 0
        for type in self.get_book_type():
            print(type, '\n')
            page = 0
            while True:
                url = 'https://www.douban.com/tag/{}?start={}'.format(type, page)
                html = requests.get(url, headers=self.header2).text
                soup = bs(html, 'lxml')
                title = soup.select('div.info > h2 > a')
                if title:
                    pub = soup.select('div.info > div.pub')
                    rating_nums = soup.select('div.star.clearfix > span.rating_nums')
                    pl = soup.select('div.star.clearfix > span.pl')
                    items = zip(title, pub, rating_nums, pl)
                    for item in items:
                        item = {'title': self.get_item(item[0]), 'href': item[0].get('href'), 'pub': self.get_item(item[1]),
                                'rating_nums': self.get_item(item[2]),
                                'pl': self.get_item(item[3])}
                        if count % 100 == 0:
                            logger.info('已抓取%s' % count)
                        dbItem = db.find_one({'href': item['href']})
                        if dbItem:
                            pass
                        else:
                            db.insert(item)
                        count += 1
                    page += 20
                    time.sleep(1)
                else:
                    break

    def get_item(self, obj):
        return obj.get_text().strip()

if __name__ == '__main__':
    res = BookId()
    res.process()
    # res.get_book_type()
    # 已爬到校园