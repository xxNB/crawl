# -*- coding: utf-8 -*-
"""
Created on 01/11/2017 3:50 PM
@author: SimbaZhang
"""
import requests
from random import choice
from lxml import etree
from bs4 import BeautifulSoup as bs
import re
import traceback
from urllib import parse
from utils.log import logger
from utils.mail import send_mail
from pymongo import MongoClient as mc
client = mc('127.0.0.1', 27017)
db = client['review']['mtime']

session = requests.session()
agent = ["Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.94 Safari/537.36",
         "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36",
         'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)']



class MtimeComs(object):
    def __init__(self, query):
        self.query = query
        self.parse_query = parse.quote(query)
        self.start_url = 'http://www.mtime.com/{}/'.format(parse.quote(query))

        agent = [
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.94 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36",
            'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)']

        self.headers = {
            'Host': 'movie.mtime.com',
            'user-agent': choice(agent),
        }
        self.main()

    def get_id(self):
        headers = {
            'Host': 'service.channel.mtime.com',
            'User-Agent': 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:56.0) Gecko/20100101 Firefox/56.0',
        }
        url = 'http://service.channel.mtime.com/Search.api?Ajax_CallBack=true&Ajax_CallBackType=Mtime.Channel.Services&Ajax_CallBackMethod=GetSearchResult&Ajax_CrossDomain=1&Ajax_RequestUrl=http://search.mtime.com/search/?q={}&t=2017102016135964257&Ajax_CallBackArgument0={}&Ajax_CallBackArgument1=0&Ajax_CallBackArgument2=997&Ajax_CallBackArgument3=0&Ajax_CallBackArgument4=1'.format(self.parse_query, self.parse_query)
        web_text = requests.get(url, headers=headers).text
        pattern = re.compile(r'"movieId":(\d+)')
        id =  pattern.search(web_text).group(1)
        self.movie_url = 'http://movie.mtime.com/{}/'.format(id)

    def get_all_links(self):
        href_list = []
        page = 1
        while 1:
            if page == 1:
                url = self.movie_url+'comment.html'
            else:
                url = self.movie_url + 'comment-{}.html'.format(page)
            web_text = requests.get(url, headers=self.headers)
            if web_text.status_code == 200:
                tree = etree.HTML(web_text.text)
                hrefs = tree.xpath('//h3/a[@target="_blank"]/@href')
                page += 1
                if hrefs:
                    for href in hrefs:
                        yield href
                else:
                    break
        return href_list


    def parse_link(self):
        for url in self.get_all_links():
            web = requests.get(url, headers=self.headers, timeout=10)
            tree = etree.HTML(web.text)
            if tree.xpath('//h2[@class="px38 mt30 c_000"]/text()'):
                title = tree.xpath('//h2[@class="px38 mt30 c_000"]/text()')[0]
                people = tree.xpath('//p[@class="pt3"]/a[@target="_blank"]/text()')[0]
                text = tree.xpath('//div[@class="db_mediacont db_commentcont"]')
                info = text[0].xpath('string(.)').strip()
                info = re.sub('\s+', ' ', info)
                item = {'peopel': people, 'title': title, 'text': info, 'movie': self.query}
                db.insert(item)
                print(item)

    def main(self):
        try:
            self.get_id()
            self.parse_link()
        except:
            logger.error('mtime crawl bug!!! %s' % traceback.format_exc())
            send_mail('mtime crawl bug', traceback.format_exc(), '1195615991@qq.com')

if __name__ == '__main__':
    import time
    st = time.time()
    res = MtimeComs('我是传奇')
    print(db.find({}).count())
    print(time.time() - st)
