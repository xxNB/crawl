# coding:utf-8

# 从mongo拿数据导入xlsx
import  re, time
import pandas as pd
from pymongo import MongoClient
client = MongoClient('127.0.0.1', 27017)
db = client['tibet']['tweet']
def monitor():
    data = db.find({'datetime': {'$gte': '2016-10-00 00:00:00', '$lt': '2017-10-00 00:00:00'}}, {'_id': 0})
    df = pd.DataFrame(list(data))
    df = df.drop_duplicates(['ID'])
    df = df.reset_index(drop=True)
    df.to_excel('/Users/zhangxin/Desktop/tibet/1_year.xlsx', encoding='utf-8')

def filter_tweet(tweet):
    # 替换twitter特殊字符
    tweet1 = tweet.lower()
    tweet2 = re.sub(r"(http[s:…]*(//\S*)?)", "", tweet1)
    return tweet2


def rechina_match(data):
    pattern = re.compile(u'[\u30a0-\u30ff]+|[\u3040-\u309f]+|[\uac00-\ud7ff]+|[\u4e00-\u9fa5]+')
    if pattern.search(data):
        return True

    return False


if __name__ == '__main__':
    # monitor()
    while 1:
        time.sleep(2)
        res = db.find().sort([('datetime', 1)]).limit(1)
        df = pd.DataFrame(list(res))
        count = db.find().count()
        print(df['datetime'])
        print(df['text'])
        print(count)
