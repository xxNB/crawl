import requests
import json
from bs4 import BeautifulSoup as bs
import time
from lxml import etree
import collections
import pandas
import traceback

class Spider(object):

    def __init__(self):
        self.start_url = 'http://liuyan.people.com.cn/forum/list?fid=266'
        self.header = {
            'Host': 'liuyan.people.com.cn',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
        }
        self.fid = []


    def get_fid(self):
        web_text = requests.get(self.start_url, headers=self.header, timeout=5).text
        web_soup = bs(web_text, 'lxml')
        hrefs = web_soup.select('ul.clearfix > li > b > a')
        href_list = map(lambda x: x.get('href').split('=')[1], hrefs)
        for fid in href_list:
            self.fid.append(fid)
        self.fids = set(self.fid)
        for fid_ in self.fids:
            yield fid_

    def get_content_json(self, fid, res, lastItem=0):
        url = 'http://liuyan.people.com.cn/threads/queryThreadsList'
        param = {
            'fid': fid,
            'lastItem': lastItem
        }
        self.header1 = {
            'Host': 'liuyan.people.com.cn',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:56.0) Gecko/20100101 Firefox/56.0',
            'Referer': 'http://liuyan.people.com.cn/threads/list?fid={}'.format(fid)
        }
        web_text = requests.post(url, data=param,  headers=self.header1)
        web_json = json.loads(web_text.text)
        if web_json['responseData']:
            last_tid = web_json['responseData'][-1]['tid']
            for item in web_json['responseData']:
                result = collections.OrderedDict()
                tid = item['tid']
                url = 'http://liuyan.people.com.cn/threads/content?tid={}'.format(tid)
                res_tree = etree.HTML(requests.get(url).text)
                result['地区'] = item['forumName']
                result['网址'] = url
                result['标题'] = item['subject']
                result['回复情况'] = item['stateInfo']
                result['领域'] = item['domainName']
                result['类别'] = item['typeName']
                result['区域'] = item['forumName']
                result['发布日期'] = self.timestamp_datatime(item['dateline'])
                result['发布内容'] = res_tree.xpath('//div/p[@class="zoom"]')[0].xpath('string(.)').strip()
                result['回复日期'] = self.timestamp_datatime(item.get('answerDateline', ''))
                try:
                    result['回复内容'] = res_tree.xpath('//li/p[@class="zoom"]')[0].xpath('string(.)').strip()
                except:
                    result['回复内容'] = ''
                print(result)
                res.append(result)
                res_ = res
            self.get_content_json(fid, res=res_, lastItem=last_tid)
        else:
            return res


    def timestamp_datatime(self, value):
        format = '%Y-%m-%d %H:%M'
        values = time.localtime(value)
        dt = time.strftime(format, values)
        return dt

    def main(self):
        last_res = []
        for fid in self.get_fid():
            global res
            res = []
            try:
                self.get_content_json(fid, res)
                last_res.extend(res)
            except IndexError as e:
                print(traceback.format_exc())
                continue
        df = pandas.DataFrame(last_res)
        df.to_excel('留言.xls')


if __name__ == '__main__':
    res = Spider()
    res.main()
