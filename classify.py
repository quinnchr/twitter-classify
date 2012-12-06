from numpy import *
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.svm import LinearSVC


class SVM:

	def __init__(self, training, classes, vocabulary):	
		vocabulary = load(vocabulary)
		self.cv = CountVectorizer(vocabulary = vocabulary.tolist())
		self.samples = load(training).tolist()
		self.classes = load(classes)
		self.classifier = LinearSVC()
		self.classifier.fit(self.samples, self.classes)

	def classify(self, text):
		features = self.cv.transform([text])
		return self.classifier.predict(features)[0]


