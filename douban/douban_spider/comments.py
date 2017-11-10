# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup as bs
from random import choice
from utils.log import logger
import time
import re
import traceback
import pymongo
from pymongo import MongoClient as mc
from utils.mail import send_mail


user_agent_list = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
        "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
       ]


class Douban(object):
    def __init__(self, ):
        self.href = str()
        self.title = str()
        self.pub = str()
        self.rating_nums = float()
        self.pl = int()
        try:
            self.db_init()
        except:
            raise Exception('database error!!!')
        self.main()

    def db_init(self):
        client = mc('127.0.0.1', 27017)
        self.db1 = client['review']['douban']
        self.db1.ensure_index([('href', pymongo.ASCENDING)], unique=True, dropDups=True)
        self.db2 = client['review']['all_book_id']


    def headers(self):
        self.header = {
            'User-Agent': choice(user_agent_list)
        }
        return self.header


    def get_all_pageurl(self):
        url = self.href + 'reviews'
        total_data = requests.get(url, headers=self.headers()).text
        soup = bs(total_data, 'lxml')
        total_pages = soup.select('#content > div > div.article > div.paginator > a')[-1].get_text()
        all_page_url =  [url + '?start=%s' % (v * 20) for v in range(int(total_pages) + 1)]
        return all_page_url

    def get_all_links(self):
        for page_url in self.get_all_pageurl():
            total_data = requests.get(page_url, headers=self.headers()).text
            soup = bs(total_data, 'lxml')
            page_links_text = soup.find_all('a', {'class': 'title-link'})
            page_links = map(lambda x: x.get('href'), page_links_text)
            yield from page_links

    def parse_comment(self):
        for ix, url in enumerate(self.get_all_links()):
            try:
                self.worker(url)
            except Exception as e:
                if isinstance(e, requests.exceptions.ConnectionError):
                    continue
                else:
                    logger.error('crawl Douban bug %s' % traceback.format_exc())
                    send_mail('Douban crawl error', traceback.format_exc(), '1195615991@qq.com')
            finally:
                if ix % 20 == 0:
                    logger.info('has ben download %s' % ix)

    def worker(self, url):
        res = requests.get(url, headers=self.headers())
        if res.status_code == 200:
            time.sleep(0.8)
            soup = bs(res.text, 'lxml')
            title = soup.find('span', {'property': 'v:summary'}).get_text()
            text = soup.select('#link-report > div.review-content.clearfix')[0].get_text()
            people = soup.find('span', {'property': 'v:reviewer'}).get_text()
            good = soup.find_all('button')[0].get_text()
            good = re.sub('\D', '', good)
            bad = soup.find_all('button')[1].get_text()
            bad = re.sub('\D', '', bad)
            item = {'good': good, 'bad': bad, 'people': people, 'title': title, 'text': text.strip(),
                    'href': url, 'book': self.title, 'pub': self.pub, 'pl': self.pl, 'rating_nums': self.rating_nums}
            dbItem = self.db1.find_one({'href': item['href']})
            if dbItem:
                pass
            else:
                self.db1.insert(item)

    def gen_book(self, obj):
        yield from obj

    def main(self):
        book_item = self.db2.find({}, no_cursor_timeout=True)
        for item in self.gen_book(book_item):
            self.title = item['title']
            self.href = item['href']
            self.pub = item['pub']
            self.rating_nums = item['rating_nums']
            self.pl = re.sub("\D", "", item['pl'])
            logger.info('%s%s%s' %('start grab...\t', self.title, '影评信息'))
            while 1:
                try:
                    self.parse_comment()
                except:
                    print(traceback.format_exc())
                    continue
                else:
                    logger.info('%s%s%s' %('self.title', '影评信息', 'done!!!'))
                    self.db2.delete_one({'href': item['href']})
                    break


if __name__ == '__main__':
    res = Douban()

