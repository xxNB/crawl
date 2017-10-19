import time
import os


from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
# 输出时间
def job1():
    os.system('scrapy crawl TweetScraper -a query=""tibet" since:2006-9-22 until:2014-7-17 " -a "crawl_user=True, lang=en"')
# BlockingScheduler

# words = 'scrapy crawl TweetScraper -a query=""tibet" since:2006-9-22 until:2014-7-17 " -a "crawl_user=True, lang=en"'
def job(words):
    os.system(words)


# scheduler = BlockingScheduler()
# scheduler.add_job(job2, 'interval', seconds=5)
# scheduler.start()

# job1()
# job('scrapy crawl TweetScraper -a query=""tibet" since:2006-9-22 until:2014-7-17 " -a "crawl_user=True, lang=en"')