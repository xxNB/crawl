
进入本地TweetScraper目录执行下面命令
query:高级查询(关键字，日期，是否采集user信息，语言选择)
scrapy crawl TweetScraper -a query="'kung fu' OR 'kungfu' OR 'shaoling' OR 'Wushu' since:2017-1-22 until:2017-8-24 " -a "crawl_user=True, lang=en"