import requests
from random import choice
from lxml import etree
import re
import traceback
from utils.log import logger
from utils.mail import send_mail

session = requests.session()
agent = ["Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.94 Safari/537.36",
         "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36",
         'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)']



class MtimeComs(object):
    def __init__(self, id):
        self.start_url = 'http://www.mtime.com/{}/'.format(id)

        agent = [
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.94 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36",
            'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)']

        self.headers = {
            'Host': 'movie.mtime.com',
            'user-agent': choice(agent),
        }
        self.main()

    def get_all_links(self):
        href_list = []
        page = 1
        while 1:
            if page == 1:
                url = self.start_url+'comment.html'
            else:
                url = self.start_url + 'comment-{}.html'.format(page)
            print(url)
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
            title = tree.xpath('//h2[@class="px38 mt30 c_000"]/text()')[0]
            people = tree.xpath('//p[@class="pt3"]/a[@target="_blank"]/text()')[0]
            text = tree.xpath('//div[@class="db_mediacont db_commentcont"]')
            info = text[0].xpath('string(.)').strip()
            info = re.sub('\s+', ' ', info)
            item = {'peopel': people, 'title': title, 'text': info}
            print(item)

    def main(self):
        try:
            self.parse_link()
        except:
            logger.error('mtime crawl bug!!! %s' % traceback.format_exc())
            send_mail('mtime crawl bug', traceback.format_exc(), '1195615991@qq.com')

if __name__ == '__main__':
    res = MtimeComs(10968)
    # res.parse_link()
