# -*- coding: utf-8 -*-
"""
收集免费ip,不过貌似ip很烂，作用不大
"""
import requests
from bs4 import BeautifulSoup
import re
import os.path
import json

user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)'
headers = {'User-Agent': user_agent}


def getListProxies():
    session = requests.session()

    proxyList = []
    for i in range(1, 3):
        page = session.get("http://www.xdaili.cn/ipagent//freeip/getFreeIps?page=%s&rows=10" %(i), headers=headers)
        ips = json.loads(page.text)['RESULT']['rows']
        for trtag in ips:
            # proxy = 'http:\\' + trtag['ip'] + ':' + trtag['port']
            proxy = {'http': trtag['ip'] + ':' + trtag['port'],
                     'https': trtag['ip'] + ':' + trtag['port']}
            # proxies = {'proxy': proxy}
            url = "https://movie.douban.com/review/1238558/"  # 用来测试IP是否可用的url
            print(proxy)
            print(type(proxy))
            try:
                response = session.get(url, proxies=proxy, timeout=1)
                print(proxy)
                print(response.status_code == 200)
                proxyList.append(proxy)
            except Exception as e:
                print(e)
                continue

    return proxyList

if __name__ == '__main__':
    print(getListProxies())