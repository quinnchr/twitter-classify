import os
import redis
import json
import time
import classify
import pickle
from multiprocessing import Pool
from pymongo import Connection

queue = 'process:queue'

def init(obj):
	global svm
	svm = obj

def f(x):
	global svm
	return svm.classify(x)

def read_queue():
	time_stamp = db.brpop(queue)[1]
	while(time_stamp):
		time_stamp = db.brpop(queue)[1]
		yield time_stamp

print 'Initializing Support Vector Machine...'
svm = pickle.load(open(os.path.dirname(__file__) + '/data/kernel-reduced-0.11.pickle','r'))
#pool = Pool(initializer=init,initargs=(svm,))
def classify(x):
	return pool.apply(f,(x,)) 
print 'SVM Initialized'

db = redis.StrictRedis(host='localhost', port=6379, db=0)
mongo = Connection('localhost', 27017).ml
sentiment = {0: 'negative', 2: 'neutral', 4: 'positive'}
sentiment_key = lambda keyword : {0: keyword + ':negative', 2: keyword + ':neutral', 4: keyword + ':positive'}

for time_stamp in read_queue():
	time_stamp = json.loads(time_stamp)
	data_time = time_stamp[u'time'] * 10**6
	keyword = time_stamp[u'source']
	source_prefix = ':'.join([time_stamp[u'user'], time_stamp[u'stream'], time_stamp[u'source']])
	stream_prefix = ':'.join([time_stamp[u'user'], time_stamp[u'stream']])
	# do the classification
	score = svm.classify(time_stamp[u'text'])
	print 'Classified: ' + sentiment[score]
	time_stamp[u'sentiment'] = sentiment[score]
	# throw it in mongo for permanent storage and add the id to redis for stats
	obj_id = mongo[time_stamp[u'user']].data.insert(time_stamp)
	data_id = str(obj_id)
	db.zadd(source_prefix + ':ids', data_time, data_id)
	db.zadd(sentiment_key(source_prefix)[score], data_time, data_id)
	db.publish(stream_prefix,time_stamp[u'source'])

