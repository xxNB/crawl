# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup as bs
from random import choice
from logzero import logger
import time
import re
import traceback
from lxml import etree
from urllib import parse
import pymongo
from pymongo import MongoClient as mc
from utils.mail import send_mail
client = mc('127.0.0.1', 27017)
db = client['review']['douban']
db.ensure_index([('href', pymongo.ASCENDING)], unique=True, dropDups=True)

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
    def __init__(self, query):
        self.old_query = query
        self.query = parse.quote(query)
        self.s = requests.session()
        acount = ['2862590148@qq.com', 'zx19950101']
        self.formdata = {'redir': 'https://www.douban.com',
                         'form_email': acount[0],
                         'form_password': acount[1],
                         'user_login': u'登陆'}
        self.loginUrl = 'https://www.douban.com/accounts/login'
        self.main()


    def get_id(self):
        url = 'https://www.douban.com/search?q={}'.format(self.query)
        web_text = self.s.get(url, headers=self.headers()).text
        tree = etree.HTML(web_text)
        ids = tree.xpath('//h3/a[@target="_blank"]/@onclick')[0]
        pattern = re.compile(r'sid:\s(\d+)')
        id = pattern.search(ids).group(1)
        return id

    def headers(self):
        self.header = {
            'User-Agent': choice(user_agent_list)
        }
        return self.header

    def loginDB(self):
        r = self.s.get(self.loginUrl,headers=self.headers())
        my_page = r.text
        re_captchaId= r'<input type="hidden" name="captcha-id" value="(.*?)".*?>'
        captchaId=re.findall(re_captchaId, my_page)
        if captchaId:
            soup = bs(my_page, 'html.parser')
            captchaSrc = soup.find('img', id='captcha_image')['src']
            if captchaSrc:
                print('captchaSrc ip is :'+ captchaSrc)
                img = requests.get(captchaSrc)
                with open('1.jpg', 'wb') as f:
                    f.write(img.content)
                captcha = input('please input the captcha:')
                self.formdata['captcha-solution'] = captcha
                self.formdata['captcha-id'] = captchaId
            self.formdata["user_login"] = "登录"
            r = self.s.post(self.loginUrl, data=self.formdata, headers = self.headers())
            if r.url == "https://www.douban.com":
                logger.info('Login successfully!!!')
            else:
                logger.info('Login failed!')
        else:
            r = self.s.post(self.loginUrl, data=self.formdata, headers=self.headers())
            if r.url == "https://www.douban.com":
                logger.info('Login successfully!!!')
            else:
                logger.info('Login failed!')


    def get_all_pageurl(self):
        url = 'https://movie.douban.com/subject/{}/reviews'.format(self.get_id())
        total_data = self.s.get(url, headers=self.headers()).text
        soup = bs(total_data, 'lxml')
        total_pages = soup.select('#content > div > div.article > div.paginator > a')[-1].get_text()
        all_page_url =  [url + '?start=%s' % (v * 20) for v in range(int(total_pages) + 1)]
        return all_page_url

    def get_all_links(self):
        for page_url in self.get_all_pageurl():
            total_data = self.s.get(page_url, headers=self.headers()).text
            soup = bs(total_data, 'lxml')
            page_links_text = soup.find_all('a', {'class': 'title-link'})
            page_links = map(lambda x: x.get('href'), page_links_text)
            for item_url in page_links:
                yield item_url

    def parse_comment(self):
        while 1:
            try:
                for url in self.get_all_links():
                    self.worker(url)
            except:
                logger.error('crawl Douban bug %s' % traceback.format_exc())
                send_mail('Douban crawl error', traceback.format_exc(), '1195615991@qq.com')

    def worker(self, url):
        res = self.s.get(url, headers=self.headers())
        if res.status_code == 200:
            time.sleep(0.7)
            soup = bs(res.text, 'lxml')
            title = soup.find('span', {'property': 'v:summary'}).get_text()
            text = soup.select('#link-report > div.review-content.clearfix')[0].get_text()
            people = soup.find('span', {'property': 'v:reviewer'}).get_text()
            good = soup.find_all('button')[0].get_text()
            good = re.sub('\D', '', good)
            bad = soup.find_all('button')[1].get_text()
            bad = re.sub('\D', '', bad)
            item = {'good': good, 'bad': bad, 'people': people, 'title': title, 'text': text.strip(), 'href': url, 'movie': self.old_query}
            print(item)
            dbItem = db.find_one({'href': item['href']})
            if dbItem:
                pass
            else:
                db.insert(item)
                pass

    def main(self):
        self.loginDB()
        logger.info('%s%s%s' %('start grab...\t', self.old_query, '影评信息'))
        self.parse_comment()

if __name__ == '__main__':

    res = Douban('你的名字')
    # res.loginDB()

