import tornado.ioloop
import tornado.web
import json 
import classify
import redis
import time
import hashlib
import pickle
from multiprocessing import Pool

class MainHandler(tornado.web.RequestHandler):

	def prepare(self):
		# only rate limit if client isn't submiting data
		if self.get_argument('sentiment', False) == False:
			remaining = self.limit(self.request.remote_ip)
			if remaining <= 0:
				self.error(400, 'rate limit exceeded')

	def error(self,status,message):
			self.set_status(status)
			self.write(json.dumps({'error' : message}))
			self.finish()

	def get(self):
		self.error(400, 'method not implemented')

	def post(self):
		text = self.get_argument('text')
		user = self.request.remote_ip
		user_sentiment = self.get_argument('sentiment', False)
		remaining = self.limit(user)
		sentiment_key = {0: 'negative', 2: 'neutral', 4: 'positive'}
		if text != '':	
			if user_sentiment in ('positive', 'negative', 'neutral'):
				self.learn(user, text, user_sentiment)
				output = json.dumps({'ratelimit-remaining' : self.limit(user)})
			elif user_sentiment == False:
				score = classify(text)
				sentiment = {'sentiment' : sentiment_key[score]}
				db.zadd('requests:'+user, time.time(), time.time())
				self.limit(user)
				output = json.dumps(sentiment)
			else:
				self.error(400,'method not implemented')
		self.write(output)

	def learn(self, user, text, sentiment):
		md5 = hashlib.md5()
		md5.update(text)
		hash_key = md5.hexdigest()
		db.hset('api:'+sentiment, hash_key, text)
		db.zadd('api:'+user, time.time(), hash_key)
	
	def limit(self, user):
		current_time = time.time()
		# delete old requests
		db.zremrangebyscore('requests:'+user, '-inf', current_time - 3600)
		db.zremrangebyscore('api:'+user, '-inf', current_time - 3600)
		# look at requests in the past hour
		requests = db.zcard('requests:'+user)
		contributions = db.zcard('api:'+user)
		remaining = min((100 + 10*contributions) - requests, 1000)

		self.set_header('X-Ratelimit-Limit', 100 + 10*contributions)
		self.set_header('X-Ratelimit-Remaining', remaining)

		return remaining

application = tornado.web.Application([
	(r"/", MainHandler),
])

def init(obj):
	global svm
	svm = obj

def f(x):
	global svm
	return svm.classify(x)

if __name__ == "__main__":
	print 'Initializing Support Vector Machine...'
	svm = pickle.load(open('data/svm-reduced.pickle','r'))
	pool = Pool(initializer=init,initargs=(svm,))
	def classify(x):
		return pool.apply(f,(x,)) 
	print 'SVM Initialized'
	db = redis.StrictRedis(host='localhost', port=6379, db=0)
	application.listen(8000)
	tornado.ioloop.IOLoop.instance().start()
