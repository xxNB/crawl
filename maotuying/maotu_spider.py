import requests
import json
from bs4 import BeautifulSoup as bs
import re
from utils.log import logger
from utils.mail import send_mail
from utils.config import citys_name
import redis
import traceback
from pymongo import MongoClient as mc

client = mc('127.0.0.1', 27017)
db = client['travel']['maotu']
job_redis = redis.Redis(host='localhost', port=6379, db=3)

class MaoTu(object):
    def __init__(self, dest):
        self.headjson_url = 'https://www.tripadvisor.cn/TypeAheadJson'
        self.dest = dest
        self.headers = {
          'Host': 'www.tripadvisor.cn',
          'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
          'Referer': 'https://www.tripadvisor.cn/Lvyou'
        }
        self.redis_idname = self.dest + 'coms'
        self.main()

    def get_headurl(self):
        params = {
            'action': 'API',
            'uiOrigin': 'PTPT-dest',
            'types': 'geo, dest',
            'hglt': 'true',
            'global': 'true',
            'query': self.dest,
            'legacy_format': 'true',
            '_ignoreMinCount': 'true'
        }
        web_json = requests.post(self.headjson_url, params=params).text
        web_text = json.loads(web_json)
        head_url = web_text[0].get('urls')[0].get('url')
        self.dest_id = head_url.split('-')[1]
        self.dest_name = head_url.split('-')[2]
        self.scenicurl = 'https://www.tripadvisor.cn/' + 'Attractions-{0}-Activities-{1}.html'.format(self.dest_id, self.dest_name)

    def get_area_links(self):
        web_text = requests.get(self.scenicurl, headers=self.headers).text
        web_soup = bs(web_text, 'lxml')
        if web_soup.select('a.pageNum.taLnk'):
            max_page = web_soup.select('a.pageNum.taLnk')[-1].get_text()
        else:
            max_page = 0
        pattern = re.compile(r'(/Attraction_Review\S+.html#REVIEWS)')
        for page in range(int(max_page)+1):
            if page == 0:
                araelink = pattern.findall(web_text)
                new_araelink = map(lambda x: 'https://www.tripadvisor.cn/'+x, araelink)
            else:
                url = 'https://www.tripadvisor.cn/Attractions-{0}-Activities-oa{1}-{2}.html#ATTRACTION_LIST'.format(self.dest_id, page*30, self.dest_name)
                next_web_text = requests.get(url, headers=self.headers).text
                araelink = pattern.findall(next_web_text)
                new_araelink = map(lambda x: 'https://www.tripadvisor.cn/'+x, araelink)
            for url in new_araelink:
                job_redis.sadd(self.redis_idname, url)

    def get_comment(self):
        url = job_redis.spop(self.redis_idname)
        while url:
            try:
                self.worker(url)
            except:
                logger.error('crawl maotu bug %s' % traceback.format_exc())
                send_mail('maotu error', traceback.format_exc(), '1195615991@qq.com')
                job_redis.sadd(self.redis_idname)
            url = job_redis.spop(self.redis_idname)
        job_redis.delete(self.redis_idname)

    def worker(self, url):
        web_text = requests.get(url, headers=self.headers).text
        web_soup = bs(web_text, 'lxml')
        area = web_soup.find('h1', {'id': 'HEADING'}).get_text()
        if web_soup.select('span.pageNum.last.taLnk'):
            max_page = web_soup.select('span.pageNum.last.taLnk')[-1].get_text()
        else:
            max_page = 0
        logger.info('%s地点: %s%s', '\n', area, '\n')
        for i in range(int(max_page) + 1):
            new_url = url.decode('utf-8')
            new_url = '-'.join(new_url.split('-')[:-3]) + '-or{}-'.format(i * 10) + '-'.join(new_url.split('-')[-2:])
            web_text = requests.get(new_url, headers=self.headers).text
            web_soup = bs(web_text, 'lxml')
            authors = web_soup.select('div.username.mo > span')
            titles = web_soup.find_all('span', {'class': 'noQuotes'})
            comments = web_soup.select('div.prw_rup.prw_reviews_text_summary_hsx > div > p')
            for author, title, comment in zip(authors, titles, comments):
                data = {
                    'city': self.dest,
                    'author': author.get_text().strip(),
                    'title': title.get_text().strip(),
                    'comment': comment.get_text().strip(),
                    'area': area
                }
                print(data)
                db.insert(data)

    def main(self):
        self.get_headurl()
        logger.info('获取 %s url编码完毕' % self.dest)
        if not job_redis.exists(self.redis_idname):
            self.get_area_links()
        logger.info("开始爬取 %s 精彩点评 " % self.dest)
        self.get_comment()
        logger.info('该%s所有景点点评采集完毕' % self.dest)



if __name__ == '__main__':
    for dest in citys_name:
        res = MaoTu(dest)
        send_mail('maotuying', '完成%s' % dest, '1195615991@qq.com')
