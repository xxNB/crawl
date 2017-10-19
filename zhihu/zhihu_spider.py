# -*- coding: utf-8 -*-
import requests
import json
import re
import time
from urllib import parse
from utils.log import logger
from utils.mail import send_mail
from bs4 import BeautifulSoup as bs
from lxml import etree
import traceback
import redis
from pymongo import MongoClient as mc
client = mc('127.0.0.1', 27017)
db = client['answers']['zhihu']

class ZhihuSpider(object):

    def __init__(self,  query, ):
        self.query = parse.quote(query)
        self.header = {
            # 'host': ' www.zhihu.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            # 'Cookie': 'd_c0="AAACcB3kzguPTjsiOu3piV6TK_L9BJJBD0U=|1495642785"; _zap=cec4c224-ad6a-40fd-80d5-c60ca0977c87; _ga=GA1.2.1483651519.1495642786; q_c1=964a43ab196841faa561b8c64c90dd43|1498554346000|1495611709000; _xsrf=d17ea8284c0ba2bc98fc8bd15eb025d9; q_c1=964a43ab196841faa561b8c64c90dd43|1507344600000|1495611709000; r_cap_id="ZDJkOTc3NGMxMzgyNDQ2Y2I1NDk4ZjA5YmU1NGNlMGM=|1507626715|5b4c6be60abc1735b16f6e33fc5fba540bcc3def"; cap_id="YTQ3MjY0N2UxYmZhNDJmYmE5ZGRiZTg2ZWE0OTllYWE=|1507626715|7ced2cfe359c57d8cf579a84dc274737e56e762e"; l_cap_id="YTZlMGM1MmQ2NTc1NDcyNjgxZjAzZjc2OTExYTFiY2M=|1507626715|8ff0b789477396490fc904699d90f0da1823688d"; capsion_ticket="2|1:0|10:1507626957|14:capsion_ticket|44:NjAzNjVlNDcwZWUwNDgwOTk5YTRmMGUyZjk4Mjg1NTI=|30696bbddfb7f7cf0c6d0a37967f7fb97169c465fb0dfb9884042491a894add4"; z_c0="2|1:0|10:1507626958|4:z_c0|92:Mi4xWUdzSUFnQUFBQUFBQUFKd0hlVE9DeVlBQUFCZ0FsVk56aHdFV2dCTGt3eGVJOEFlWHMzd3NtT2tHMnlnd3Y5WGN3|296453f86bf56b076b5518b4df7fa1fd4ad42da1f58c0f2ea7e2bca4fe78bc3a"; __utma=51854390.1642964529.1507717776.1507717776.1507858926.2; __utmz=51854390.1507858926.2.2.utmcsr=zhihu.com|utmccn=(referral)|utmcmd=referral|utmcct=/people/xi-xi-8-3/collections; __utmv=51854390.100-1|2=registration_date=20150829=1^3=entry_date=20150829=1; aliyungf_tc=AQAAABopxGPC2gcAAJ7idE6qVf+pMXOB; _xsrf=d17ea8284c0ba2bc98fc8bd15eb025d9'
            'Cookie': '_zap=555083a8-acd2-4e48-9533-939968218e4a; d_c0="AAACcB3kzguPTjsiOu3piV6TK_L9BJJBD0U=|1495642785"; _zap=cec4c224-ad6a-40fd-80d5-c60ca0977c87; _ga=GA1.2.1483651519.1495642786; q_c1=964a43ab196841faa561b8c64c90dd43|1498554346000|1495611709000; q_c1=964a43ab196841faa561b8c64c90dd43|1507344600000|1495611709000; r_cap_id="ZDJkOTc3NGMxMzgyNDQ2Y2I1NDk4ZjA5YmU1NGNlMGM=|1507626715|5b4c6be60abc1735b16f6e33fc5fba540bcc3def"; cap_id="YTQ3MjY0N2UxYmZhNDJmYmE5ZGRiZTg2ZWE0OTllYWE=|1507626715|7ced2cfe359c57d8cf579a84dc274737e56e762e"; l_cap_id="YTZlMGM1MmQ2NTc1NDcyNjgxZjAzZjc2OTExYTFiY2M=|1507626715|8ff0b789477396490fc904699d90f0da1823688d"; capsion_ticket="2|1:0|10:1507626957|14:capsion_ticket|44:NjAzNjVlNDcwZWUwNDgwOTk5YTRmMGUyZjk4Mjg1NTI=|30696bbddfb7f7cf0c6d0a37967f7fb97169c465fb0dfb9884042491a894add4"; z_c0="2|1:0|10:1507626958|4:z_c0|92:Mi4xWUdzSUFnQUFBQUFBQUFKd0hlVE9DeVlBQUFCZ0FsVk56aHdFV2dCTGt3eGVJOEFlWHMzd3NtT2tHMnlnd3Y5WGN3|296453f86bf56b076b5518b4df7fa1fd4ad42da1f58c0f2ea7e2bca4fe78bc3a"; aliyungf_tc=AQAAAK3HGW9ZtwQAAJ7idJIFVJzFE+rG; s-q=%E8%80%83%E7%A0%94%E8%8B%B1%E8%AF%AD; s-i=3; sid=4j6pa75o; __utma=51854390.1483651519.1495642786.1508209415.1508329859.2; __utmc=51854390; __utmz=51854390.1508329859.2.2.utmcsr=qq|utmccn=(not%20set)|utmcmd=social; __utmv=51854390.100-1|2=registration_date=20150829=1^3=entry_date=20150829=1; _xsrf=d17ea8284c0ba2bc98fc8bd15eb025d9'
        }
        self.main()

    def paser_data(self):
        if self.work():
            for ques in self.work():
                pages_text  = requests.get('https://www.zhihu.com/question/{}'.format(ques[0]), headers=self.header).text
                soup = bs(pages_text, 'lxml')
                page = soup.find('h4', {'class': 'List-headerText'})
                if page:
                    page = re.sub('\D', '', page.get_text())
                    logger.info('%s%s' %('回答数', page))
                    for n in range(0, int(page)+20, 20):
                        time.sleep(1)
                        url = 'https://www.zhihu.com/api/v4/questions/{}/answers?include=data[*].is_normal,admin_closed_comment,reward_info,is_collapsed,annotation_action,annotation_detail,collapse_reason,is_sticky,collapsed_by,suggest_edit,comment_count,can_comment,content,editable_content,voteup_count,reshipment_settings,comment_permission,created_time,updated_time,review_info,question,excerpt,relationship.is_authorized,is_author,voting,is_thanked,is_nothelp,upvoted_followees;data[*].mark_infos[*].url;data[*].author.follower_count,badge[?(type=best_answerer)].topics&offset={}&limit=20&sort_by=default'.format(ques[0], n)
                        json_ = self.get_json(url)
                        length = len(json_['data'])
                        for i in range(length):
                            json_text = json_['data'][i]
                            agree = json_text['voteup_count']
                            question_info = json_text.get('content')
                            author = json_text.get('author').get('name')
                            content = re.sub(r'(<.{1,2}>)', '', question_info)
                            data = {'question': ques[1], 'Approval number':agree, 'author': author, 'content': content, }
                            print(data)
                            db.insert(data)
                else:
                    print('Comment by folding!!!')

        logger.info('Related questions and answers information collection completed!!!')

    def get_json(self, url):
        return json.loads(requests.get(url, headers=self.header).text)

    def work(self):
        n = -10
        while 1:
            try:
                   n += 10
                   for res in self.parse_old_link(n):
                       yield res[0], res[1]
            except:
                logger.debug('%s%s%s' %('have no pageing!!!', '\t', traceback.format_exc()))
                yield None
                break

    def parse_old_link(self, n):
        url = 'https://www.zhihu.com/r/search?q={}&correction=1&type=content&offset={}'.format(self.query, n)
        text_json = json.loads(requests.get(url, headers=self.header).text)
        htmls = text_json['htmls']
        for html in htmls:
            try:
                tree = etree.HTML(html)
                title = tree.xpath('//a[@class="js-title-link"]')
                title = title[0].xpath('string(.)').strip()
                total_answer = tree.xpath('//span[@class="label"]/text()')[0]
                total_answer = re.sub('\D', '', total_answer)
                answer_url = tree.xpath('//link[@itemprop="url"]/@href')[0]
                num_id = answer_url.split('/')[2]
                id = int(num_id)
                logger.info('%s%s%s%s%s' % (title, '评论数', total_answer, '\n', '=' * 100))
                yield id, title
            except Exception:
                continue

    def main(self):
        try:
            self.paser_data()
        except:
            logger.error('%s%s%s' % ('have no pageing!!!', '\t', traceback.format_exc()))
            send_mail('zhihu crawl bug!', traceback.format_exc(), '1195615991@qq.com')


if __name__ == '__main__':
    # 填入你想查找的问答
    res = ZhihuSpider(query='武林外传')
