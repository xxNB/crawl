import requests
from random import choice
from lxml import etree
import time
import re
import traceback
from urllib import parse
from logzero import logger
from utils.mail import send_mail
import aiohttp
import asyncio

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

    @asyncio.coroutine
    def get_all_links(self):
        page = 1
        while 1:
            if page == 1:
                url = self.movie_url+'comment.html'
            else:
                url = self.movie_url + 'comment-{}.html'.format(page)
            with aiohttp.ClientSession() as session:
                web_text = yield from session.get(url, headers=self.headers)
                if web_text.status == 200:
                    web_text = yield from web_text.read()
                    tree = etree.HTML(web_text)
                    hrefs = tree.xpath('//h3/a[@target="_blank"]/@href')
                    page += 1
                    if hrefs:
                        to_do = [self.parse_link(url) for url in hrefs]
                        # asyncio.as_completed，通过它可以获取一个协同程序的列表，
                        # 同时返回一个按完成顺序生成协同程序的迭代器，因此当你用它迭代时，会尽快得到每个可用的结果
                        # 返回一个协程迭代器。
                        to_od_iter = asyncio.as_completed(to_do)
                        for future in to_od_iter:
                            try:
                                res = yield from future
                            except Exception as e:
                                print(e)
                                continue
                    else:
                        logger.info('no page!!!!!')
                        break

    @asyncio.coroutine
    def parse_link(self, url):
        with aiohttp.ClientSession() as session:
            web = yield from session.get(url, headers=self.headers)
            web_text = yield from web.read()
            tree = etree.HTML(web_text)
            if tree.xpath('//h2[@class="px38 mt30 c_000"]/text()'):
                title = tree.xpath('//h2[@class="px38 mt30 c_000"]/text()')[0]
                people = tree.xpath('//p[@class="pt3"]/a[@target="_blank"]/text()')[0]
                text = tree.xpath('//div[@class="db_mediacont db_commentcont"]')
                info = text[0].xpath('string(.)').strip()
                info = re.sub('\s+', ' ', info)
                item = {'peopel': people, 'title': title, 'text': info, 'movie': self.query}
                print(item)

    def main(self):
        try:
            self.get_id()
            loop = asyncio.get_event_loop()
            coro = self.get_all_links()
            counts = loop.run_until_complete(coro)
            loop.close()
            return counts
        except:
            logger.error('mtime crawl bug!!! %s' % traceback.format_exc())

if __name__ == '__main__':
    st = time.time()
    res = MtimeComs('我是传奇')
    print(time.time() - st)
