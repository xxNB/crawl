# -*- coding: utf-8 -*-
import requests
from lxml import etree
import json
import re
import traceback
from bs4 import BeautifulSoup as bs
from pymongo import MongoClient as mc
client = mc('127.0.0.1', 27017)
db = client['xireport']['xireport']

class JinReport(object):
    def __init__(self):
        self.strt_url = 'http://jhsjk.people.cn/'
        self.items = {'经济':101, '政治':102, '文化':103, '社会':104, '生态':105, '党建':106, '国防':107, '外交':108}
        self.itemlist = [ '经济', '政治', '文化', '社会', '生态', '党建', '国防', '外交']
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
            'Host': 'jhsjk.people.cn',
            # 'Cookie': 'PHPSESSID=o57ia3gvkjssoubb9gnlv16pk4; wdcid=56b33d465eff3b4b; wdlast=1506606309; wdses=6b029b02d220dcf9; csrf_cookie_name=bf69d64695c58c2857a5bab5f6cbd170',
            # 'Cache-Control': 'Cache-Control: max-age=0'
        }

    def parse_pagelinks(self, n, type_):
        num = self.items.get(type_)
        twice_url = []
        if n == 1:
            url = 'http://jhsjk.people.cn/result?type={}'.format(num)
        else:
            url = 'http://jhsjk.people.cn/result/{}?type={}'.format(n, num)
        print(url)
        web_text = requests.get(url, headers=self.header).text
        twice_url.append(url)
        tree = etree.HTML(web_text)
        url_list = tree.xpath('//ul[@class="list_14 p1_2 clearfix"]/li/a/@href')
        if url_list:
            print(url_list)
            url_list = map(lambda x: 'http://jhsjk.people.cn/'+ x, url_list)
            for url in url_list:
                yield url
        else:
            raise Exception('no page!!!')

    def item_parse(self, url, type_):
        # print(url)
        item_dict = {}
        web_text = requests.get(url, headers=self.header, timeout=2).text
        web_soup = bs(web_text, 'lxml')
        tree = etree.HTML(web_text)
        item_dict['标题'] = tree.xpath('//div[@class="d2txt clearfix"]/h1/text()')[0]
        item_dict['内容类型'] = type_
        info = tree.xpath('//div[@class="d2txt_1 clearfix"]/text()')[0]
        pattern = re.compile(r'\d+-\d+-\d+')
        item_dict['出版时间'] = pattern.search(info).group()
        text = tree.xpath('//div[@class="d2txt_con clearfix"]')
        text = text[0].xpath('string(.)').strip()
        text = re.sub('\s+', ' ', text)
        item_dict['内容'] = text
        where = web_soup.select('.d2txt_con > p')[-2].get_text().strip()
        if where:
            patterns = re.compile(u'.+电')
            if patterns.search(where):
                item_dict['出版1'] = where
            else:
                item_dict['出版1'] = '无'
        else:
            item_dict['出版1'] = '无'
        which = tree.xpath('//span[@id="paper_num"]/text()')
        if which:
            item_dict['出版2'] = which[0].strip()
        else:
            item_dict['出版2'] = '无'
        print('出版1', item_dict['出版1'])
        print('出版2', item_dict['出版2'])
        print(item_dict)
        db.insert(item_dict)


    def get_links(self):
        last_url = []
        for type_ in self.itemlist:
            n = 1
            print(type_)
            while 1:
                try:
                    for url in self.parse_pagelinks(n, type_):
                        if url:
                            try:
                                self.item_parse(url, type_)
                            except:
                                with open('url.txt', 'a') as f:
                                    f.write(url+'\n')
                                continue
                except Exception as e:
                    print(traceback.format_exc())
                    break
                n += 1




if __name__ == '__main__':
    res = JinReport()
    res.get_links()
    import pandas as pd
    res = db.find({},{'_id': 0})
    # print(res)
    df = pd.DataFrame(list(res))
    df = df[['标题', '内容类型', '出版时间', '内容', '出版1', '出版2']]
    # print()
    # print(df)
    df.to_excel('report.xls')

