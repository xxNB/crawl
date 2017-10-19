# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-import requests
import json
import time
import re
import redis
import requests
from concurrent import futures
from logzero import logger
ip_redis = redis.Redis(host='localhost', port=6379, db=5)


class GetIp(object):
    def __init__(self):
        self.header = {
                       'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}

    def get_xici(self):
        for page in range(1, 3):
            url = 'http://www.xicidaili.com/nn/{}'.format(page)
            html = requests.get(url, headers=self.header).text
            pattern = re.compile(r'<td>(\d+\.\d+\.\d+\.\d+)</td>\s+<td>(\d+)</td>', re.DOTALL)
            ips = pattern.findall(html)
            for ip in ips:
                new_ip = ip[0] + ':' + ip[1]
                ip_redis.sadd('ips', new_ip)

    def get_kuai(self):
        for i in range(1, 3):
            page = requests.get("http://www.xdaili.cn/ipagent//freeip/getFreeIps?page=%s&rows=10" % (i), headers=self.header)
            ips = json.loads(page.text)['RESULT']['rows']
            for trtag in ips:
                new_ip = trtag[0] + ':' + trtag[1]

                ip_redis.sadd('ips', new_ip)

    def get_kx(self):
        for page in range(1, 4):
            url = 'http://www.kxdaili.com/dailiip/1/{}.html#ip'.format(page)
            header = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
            }
            html = requests.get(url, headers=header).text
            pattern = re.compile(r'<td>(\d+\.\d+\.\d+\.\d+)</td>\s+<td>(\d+)</td>', re.S)
            ips = pattern.findall(html)
            for ip in ips:
                new_ip = ip[0] + ':' + ip[1]
                ip_redis.sadd('ips', new_ip)

    def get_181(self):
        url = 'http://www.ip181.com/'
        header = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        }
        html = requests.get(url, headers=header)
        html.encoding = 'gbk'
        html = html.text
        pattern = re.compile(u'<td>(\d+\.\d+\.\d+\.\d+)</td>\s+<td>(\d+)</td>\s+<td>高匿</td>', re.DOTALL)
        ips = pattern.findall(html)
        for ip in ips:
            new_ip = ip[0] +':' + ip[1]
            ip_redis.sadd('ips', new_ip)

    def collect_allips(self):
        with futures.ProcessPoolExecutor(max_workers=5) as excuter:
            # excuter.submit(self.get_xici)
            # excuter.submit(self.get_181)
            excuter.submit(self.get_kx)
            # excuter.submit(self.get_kuai)

    def check_ip(self, ip):
        check_url = 'https://movie.douban.com/review/1238558/'
        if isinstance(ip, bytes):
            ip_decode = ip.decode('utf-8')
            ip_ = {'http': ip_decode, 'https': ip_decode}
            try:
                text = requests.get(check_url, proxies=ip_, timeout=1)
                if text.status_code == 200:
                    ip_redis.sadd('ips_useful', ip)
                    logger.info('success!!!!, %s' % ip_)
                    return True
            except Exception as e:
                # print(traceback.format_exc())
                pass

    def ip_put(self):
        # ip = ip_redis.spop('ips')
        while 1:
            ip = ip_redis.spop('ips')
            if ip:
                yield ip
            else:
                break

    def check_collectip(self):
        with futures.ProcessPoolExecutor(max_workers=5) as excuter:
            for ip in self.ip_put():
                excuter.submit(self.check_ip, ip)

    def check_usefulip(self):
        logger.info('再次检测ip代理池里的ip')
        count = 0
        ips = ip_redis.scard('ips_useful')
        for i in range(ips):
            ip = ip_redis.spop('ips_useful')
            if self.check_ip(ip):
                count += 1
        if count < 2:
            logger.info('ip代理池里的ip不够了..重新收集')
            self.main()
        else:
            logger.info('ip代理池里的ip正常')


    def main(self):
        logger.info('开始收集所有ip...')
        self.collect_allips()
        logger.info('开始检测ip可用性...')
        self.check_collectip()

if __name__ == '__main__':
    res = GetIp()
    res.main()
    while 1:
        time.sleep(30)
        res.check_usefulip()


