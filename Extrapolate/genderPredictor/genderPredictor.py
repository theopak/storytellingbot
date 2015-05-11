#!/usr/bin/env python
# encoding: utf-8
"""
genderPredictor.py
"""

from nltk import NaiveBayesClassifier,classify
from nltk.corpus import names
import random

class genderPredictor():
    
    def getFeatures(self):
        maleNames = (name for name in names.words('male.txt'))
        femaleNames = (name for name in names.words('female.txt'))
        
        featureset = list()
        for name in maleNames:
            features = self._nameFeatures(name)
            featureset.append((features,'M'))
        
        for name in femaleNames:
            features = self._nameFeatures(name)
            featureset.append((features,'F'))
    
        return featureset
    
    def trainAndTest(self,trainingPercent=0.80):
        featureset = self.getFeatures()
        random.shuffle(featureset)
        
        name_count = len(featureset)
        
        cut_point=int(name_count*trainingPercent)
        
        train_set = featureset[:cut_point]
        test_set  = featureset[cut_point:]
        
        self.train(train_set)
        
        return self.test(test_set)
        
    def classify(self,name):
        feats=self._nameFeatures(name)
        print(name, feats)
        for male in names.words('male.txt'):
            if name == male:
                return 'M'
        for female in names.words('female.txt'):
            if name == female:
                return 'F'
        
        return self.classifier.classify(feats)
        
    def train(self,train_set):
        self.classifier = NaiveBayesClassifier.train(train_set)
        return self.classifier
        
    def test(self,test_set):
       return classify.accuracy(self.classifier,test_set)
        
    def getMostInformativeFeatures(self,n=5):
        return self.classifier.most_informative_features(n)

    def _nameFeatures(self,name):
        return {
            'last_letter': name[-1],
            'last_two' : name[-2:],
            'last_is_vowel' : (name[-1] in 'AEIOUY')
        }

if __name__ == "__main__":
    gp = genderPredictor()
    accuracy=gp.trainAndTest()
    print ('Accuracy:', accuracy)
    print ('Most Informative Features')
    feats=gp.getMostInformativeFeatures(10)
    for feat in feats:
        print (feat)
    
    print ('\nStephen is classified as', gp.classify('Stephen'))