# -*- coding: utf-8 -*-
"""
Created on 2017/10/28 下午2:43
@author: SimbaZhang
"""
import time
from pymongo import MongoClient as mc
client = mc('127.0.0.1', 27017)
db = client['travel']['maotu']


count = db.find({}).count()
while 1:
    print(count)
    time.sleep(3)
