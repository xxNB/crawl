# -*- coding: utf-8 -*-
import requests
import json
import re
import traceback
import time
from bs4 import BeautifulSoup as bs
from urllib import parse
from utils.log import logger
from utils.mail import send_mail
from lxml import etree
from random import choice
from utils.config import citys_name
from pymongo import MongoClient as mc
import redis

client = mc('127.0.0.1', 27017)
db = client['travel']['mafengwo']
job_redis = redis.Redis(host='localhost', port=6379, db=2)

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
class MafengWo(object):
    def __init__(self, dest, proxy=None):
        self.old_dest = dest
        self.dest = parse.quote(dest)
        self.trip_url = 'http://www.mafengwo.cn/search/s.php?q={}&t=info&seid=&mxid=0&mid=0&mname=&kt=1'.format(self.dest)
        self.comments_url = 'http://www.mafengwo.cn/search/s.php?q={}&p=1&t=poi&kt=1'.format(self.dest)
        self.proxy = proxy
        self.redis_idname = self.old_dest + 'coms'
        self.redis_urlname = self.old_dest + 'travelnotes'
        self.main()

    def headers(self):
        self.header = {
            'User-Agent': choice(user_agent_list)
        }
        return self.header

    def get_maxpage(self, start_url):
        web_html = requests.get(start_url, headers=self.headers(), proxies=self.proxy)
        web_html.encoding = 'utf-8'
        web_soup = bs(web_html.text, 'lxml')
        counts_text = web_soup.select('.ser-result-primary')[0].get_text()
        totalCount = int(re.sub("\D", "", counts_text))
        max_page = 50 if totalCount > 750 else int(totalCount / 15)+1
        return max_page

    def get_scenic_id(self):
        pattern = re.compile(u'http://www.mafengwo.cn/poi/(\d+).html.+>点评\((\d+)\)<')
        self.scenic_id = []
        max_page = self.get_maxpage(self.comments_url)
        for page in range(max_page+1):
            url = 'http://www.mafengwo.cn/search/s.php?q={}&p={}&t=poi&kt=1'.format(self.dest, str(page+1))
            web_text = requests.get(url, headers=self.headers(), proxies=self.proxy)
            web_text.encoding = 'utf-8'
            parm_id = pattern.findall(web_text.text)
            for x, y in parm_id:
                if int(y) > 0:
                    job_redis.sadd(self.redis_idname, int(x))


    def get_travel_url(self):
        max_page = self.get_maxpage(self.trip_url)
        for page in range(max_page + 1):
            if page == 0:
                url = 'http://www.mafengwo.cn/search/s.php?q={}&p={}&t=info&kt=1'.format(self.dest, str(page))
            else:
                url = 'http://www.mafengwo.cn/search/s.php?q={}&p={}&t=info&kt=1'.format(self.dest, str(page+1))
            web_text = requests.get(url, headers=self.headers()).text
            web_soup = bs(web_text, 'lxml')
            parm_url = web_soup.select('#_j_search_result_left > div > div > ul > li > div > div.ct-text > h3 > a')
            parm_urls = [i.get('href') for i in parm_url]
            for url in parm_urls:
                job_redis.sadd(self.redis_urlname, url)


    def get_travel_notes(self):
        logger.info('抓取游记: %s%s',  self.old_dest, '\n')
        url = job_redis.spop(self.redis_urlname)
        count = 0
        while url:
            try:
               self.note_worker(url)
            except :
                logger.error('crawl maotu bug %s' % traceback.format_exc())
                send_mail('maotu error', traceback.format_exc(), '1195615991@qq.com')
                job_redis.sadd(self.redis_urlname, url)
            url = job_redis.spop(self.redis_urlname)
            count += 1
            if count % 20 == 0:
                logger.info('has been download %s travel_notes' % count )
        job_redis.delete(self.redis_urlname)

    def note_worker(self, url):
        if isinstance(url, bytes):
            url = url.decode('utf-8')
        web_data = requests.get(url, headers=self.headers())
        web_data.encoding = 'utf-8'
        tree = None
        try:
            tree = etree.HTML(web_data.text)
        except Exception as e:
            pass
        if tree is not None:
            title_pattern = re.compile(u'<title>(.+)\s-\s蚂蜂窝</title>', re.DOTALL)
            title = title_pattern.search(web_data.text).group(1)[:-7]
            data = tree.xpath('//div[@class="vc_article"]')
            if data:
                info = data[0].xpath('string(.)').strip()
                info = re.sub('\s+', ' ', info)
            else:
                data = tree.xpath('//div[@class="a_con_text cont"]')
                if data:
                    info = data[0].xpath('string(.)').strip()
                    info = re.sub('\s+', ' ', info)
                else:
                    data = tree.xpath('//div[@class="p_con"]')
                    info = data[0].xpath('string(.)').strip()
                    info = re.sub('\s+', ' ', info)
            # print(info)
            db.insert({'type': '游记','area': self.old_dest,'title': title, 'content': info})

    def get_comments(self):
        id = job_redis.spop(self.redis_idname)
        while id:
            try:
                self.coms_worker(id)
            except:
                logger.error('crawl mafengwo bug %s' % traceback.format_exc())
                send_mail('mafengwo error', traceback.format_exc(), '1195615991@qq.com')
                job_redis.sadd(self.redis_idname, id)
            id = job_redis.spop(self.redis_idname)
        job_redis.delete(self.redis_idname)
        logger.info('景点点评爬取完毕')

    def coms_worker(self, id):
        if isinstance(id, bytes):
            id = id.decode('utf-8')
        area_url = 'http://www.mafengwo.cn/poi/{}.html'.format(id)
        web_text = requests.get(area_url, proxies=self.proxy)
        web_text.encoding = 'utf-8'
        web_soup = bs(web_text.text, 'lxml')
        pattern = re.compile(u'data-title="([\u4e00-\u9fa5]+)"')
        pattern_ = pattern.search(web_text.text)
        counts_text_ = web_soup.select('#poi-navbar > ul > li > a > span')
        if pattern_ and counts_text_:
            area = pattern_.group(1)
            counts_text = counts_text_[0].get_text()
            totalCount = int(re.sub("\D", "", counts_text))
            if totalCount != 0:
                max_page = 50 if totalCount > 750 else int(totalCount / 15) + 1
                logger.info('地点 : %s%s%s' % (area, '\n', '=' * 100))
                for ix, page in enumerate(range(max_page + 1)):
                    time.sleep(1)
                    comment_url = 'http://pagelet.mafengwo.cn/poi/pagelet/poiCommentListApi?params={"poi_id": %s,"page": %s,"just_comment":1}' % (
                    str(id), page + 1)
                    web_json = json.loads(requests.get(comment_url, headers=self.headers(), proxies=self.proxy).text)
                    web_html = web_json["data"].get("html")
                    web_soup = bs(web_html, 'lxml')
                    authors = web_soup.select('a.name')
                    comments = web_soup.select('p.rev-txt')
                    for author, comment in zip(authors, comments):
                        data = {'city': self.old_dest, 'type': '点评', 'area': area,'author': author.get_text().strip(), 'comment': comment.get_text().strip()}
                        # print(data)
                        db.insert(data)
                    logger.info('has been download %s page' % ix)

    def main(self):
        logger.info('开始爬取 %s 各景点精彩点评' % self.old_dest)
        if not job_redis.exists(self.redis_idname):
            self.get_scenic_id()
        self.get_comments()
        logger.info('开始爬取 %s 精彩游记：' % self.old_dest)
        if not job_redis.exists(self.redis_urlname):
            self.get_travel_url()
        self.get_travel_notes()
        logger.info('该%s所有景点点评采集完毕' % self.old_dest)


if __name__ == '__main__':
    # dest_list = ['大理', '安庆', '六安']
    # for dest in citys_name:
    res = MafengWo('北京')
    # send_mail('mafengwo', '完成%s' % dest, '1195615991@qq.com')

