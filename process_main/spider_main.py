# -*- coding: utf-8 -*-
import os
from douban.douban_spider.comments import Douban
from mafengwo.fengwo_spider import MafengWo
from maotuying.maotu_spider import MaoTu
from zhihu.zhihu_spider import ZhihuSpider
from douban.mtime_spider.mtime_coms import MtimeComs
from TweetScraper.TweetScraper.command import job
from logzero import logger
from concurrent import futures

class SpiderMain(object):

    def __init__(self, doubanarg=None, mafengwoarg=None, maotuyingarg=None, zhihuarg=None, mtimearg=None):
        self.douban_arg = doubanarg
        self.mafengwo_arg = mafengwoarg
        self.maotuying_arg = maotuyingarg
        self.zhihu_arg = zhihuarg
        self.mtime_arg= mtimearg
        self.main()

    def douban_run(self):
        logger.info('starting douban spider...')
        res = Douban(self.douban_arg)
        logger.info('douban finish!!!')

    def mafengwo_run(self):
        logger.info('starting mafengwo spider...')
        res = MafengWo(self.mafengwo_arg)
        logger.info('mafengwo finish!!!')

    def maotuying_run(self):
        logger.info('starting maotuying spider...')
        res = MaoTu(self.mafengwo_arg)
        logger.info('maotuying finish!!!')

    def zhihu_run(self):
        logger.info('starting zhihu spider...')
        res = ZhihuSpider(self.zhihu_arg)
        logger.info('zhihu finish!!!')

    # 时光网有问题，浏览器有时候也加载不出来
    def mtime(self):
        logger.info('starting mtime spider...')
        res = MtimeComs(self.mtime_arg)
        logger.info('mtime finish!!!')

    def tweet(self, words):
        # 进入scrapy目录执行
        os.chdir("/Users/zhangxin/Desktop/crawl/TweetScraper/")
        job(words)

    def main(self):
        with futures.ProcessPoolExecutor(max_workers=5) as excuter:
            # excuter.submit(self.douban_run())
            # excuter.submit(self.maotuying_run())
            # excuter.submit(self.mafengwo_run())
            excuter.submit(self.zhihu_run())
            # excuter.submit(self.mtime())
            pass

if __name__ == '__main__':
    res = SpiderMain(doubanarg='霸王别姬', mafengwoarg='大理', maotuyingarg='大理', zhihuarg='美国往事', mtimearg=10968)
    # 执行twitter
    res.tweet('scrapy crawl TweetScraper -a query=""tibet" since:2006-9-22 until:2013-12-13 " -a "crawl_user=True, lang=en"')
