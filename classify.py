from numpy import *
from scikits.learn.feature_extraction.text import CountVectorizer
from scikits.learn.svm.sparse import LinearSVC


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


