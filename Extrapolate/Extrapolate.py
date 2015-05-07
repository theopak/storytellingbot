#!/usr/bin/python3


#import nltk
from nltk import word_tokenize
from nltk import pos_tag
from nltk import NaiveBayesClassifier
from nltk.corpus import wordnet
from nltk.corpus import names
from nltk.stem.wordnet import WordNetLemmatizer as wnl
from re import sub
import string
import random
#from genderPredictor import genderPredictor
#nltk.download()
# nltk downloads: maxent_ne_chunker, maxent_treebank_pos_tagger, punkt, wordnet
# install numpy
# WordNetLemmatizer().lemmatize(word,'v')


class Extrapolate:

    def __init__(self):
        self.gender_prediction_init()

    def change_gender(self, pnoun, gender):
        pnlist = [(("her", "female"), ("him", "male")),
                  (("she", "female"), ("he", "male")),
                  (("hers", "female"), ("his", "male")),
                  (("herself", "female"), ("himself", "male"))]
        for pair in pnlist:
            for i in range(len(pair)):
                if pair[i][0] == pnoun:
                    if pair[i][1] == gender:
                        return pnoun
                    else:
                        if i == 0:
                            return pair[1][0]
                        else:
                            return pair[0][0]
        else:
            return pnoun

    def gender_features(self, word):
        return {'last_letter': word[-1], 'last_two': word[-2:],
                'last_vowel': word[-1] in 'AEIOUY'}

    def gender_prediction_init(self):
        labeled_names = ([(name, 'male') for name in names.words('male.txt')] +
                         [(name, 'female') for name in names.words('female.txt')])

        random.shuffle(labeled_names)
        featuresets = [(self.gender_features(n), gender) for (n, gender) in labeled_names]
        train_set, test_set = featuresets[500:], featuresets[:500]
        self.classifier = NaiveBayesClassifier.train(train_set)

    def find_synonyms(self, w, wpos):
        syn_words = []
        synsets = wordnet.synsets(w, pos=wpos)
        #print("Synsets for", w, "are:", synsets)
        for s in synsets:
            for l in s.lemmas():
                syn_words.append(l.name())
        return syn_words

    def replace_proper_nouns(self, o_sent, n_sent):
        o_i = []
        n_i = []

        o_tagged = pos_tag(word_tokenize(o_sent))
        n_tagged = pos_tag(word_tokenize(n_sent))

        #name = "Jane"
        #print(name, self.classifier.classify(self.gender_features(name)))

        for o in o_tagged:
            if o[1] == 'NNP' and o not in o_i:
                o_i.append(o)

        for n in n_tagged:
            if n[1] == 'PRP' and n not in n_i:
                n_i.append(n)

        for o in o_i:
            print(o, self.classifier.classify(self.gender_features(o)))

        # hand waving here for the moment
        if len(o_i) == 1 and len(n_i) > 0:
            #for i in n_i:
            n_sent = sub(r"\b%s\b" %n_i[0][0] , o_i[0][0], n_sent, 1)
        elif len(o_i) < 1:
            print("No proper nouns to replace")
        else:
            print("Not yet implemented, :P")

        return n_sent

    def strip_pos_copy(self, tag):
        new_tag = []
        
        for item in tag:
            new_tag.append(item[0])
        
        return new_tag
        
    def extrapolate(self, sent):

        # tags the part of speech in each word
        tagged = pos_tag(word_tokenize(sent))
        
        tag_list = []
        for item in tagged:
            tag_list.append(list(item))
        
        # puts nouns and verbs in their base form
        for idx, item in enumerate(tag_list):
            if item[1][0] == 'V':
                tag_list[idx][0] = wnl().lemmatize(item[0],'v')
            elif item[1] == 'NN' or item[1] == 'NNS':
                tag_list[idx][0] = wnl().lemmatize(item[0],'n')
                
        synonyms = [[] for i in range(len(tag_list))]
        
        # finds synonyms for each wnoun, verb, adj in tag_list -> puts in corresponding index in synonyms
        for idx, item in enumerate(tag_list):
            if item[1][0] == 'V':
                synonyms[idx] = self.find_synonyms(item[0], wordnet.VERB)
            elif item[1] == 'NN' or item[1] == 'NNS':
                synonyms[idx] = self.find_synonyms(item[0], wordnet.NOUN)
            elif item[1][0] == 'J':
                synonyms[idx] = self.find_synonyms(item[0], wordnet.ADJ)

        # gets rid of duplicates
        for s in synonyms:
            s = list(set(s))
            print(s)
        
        search_sent = []
        # creates a list of similar sentences to search for
        for idx, item in enumerate(tag_list):
            # looks for synonyms at the corresponding index, 
            for s in synonyms[idx]:
                temp = self.strip_pos_copy(tag_list)
                temp[idx] = s
                search_sent.append(temp)
        
        #need to combine sentence parts into a sentence
        
        # will get rid of duplicates once i make it hashable
        #search_sent = list(set(search_sent))
        
        for s in search_sent:
            print(s)
        return search_sent


if __name__ == '__main__':
    #list of pretend sentences to search through
    sent_list = []
    sent_list.append("She danced with the prince and they fell in love.")
    sent_list.append("The emperor realized he was swindled but continues the parade anyway.")
    sent_list.append("He and his wife were very poor.")
    sent_list.append("She promised anything if he would get it for her. ")
    sent_list.append("The bears came home and frightened her and she ran away.")
    sent_list.append("They came upon a house made of sweets and they ate some. ")
    sent_list.append("He climbed the beanstalk and found a giant there who had gold coins. ")
    sent_list.append("The rats followed him and he led them into the harbor and they died.")
    sent_list.append("He begged to be spared and told him about his poor father.")
    sent_list.append("The two were married and lived happily everafter.")
    sent_list.append("The good fairies made another spell so that she would only sleep for 100 years and a prince would awaken her. ")
    sent_list.append("The stepmother ordered her to be killed but the huntsman spared her life.")
    sent_list.append("The wolf fell into it and died.")
    sent_list.append("A fairy granted her wish and gave her a seed to plant. ")
    sent_list.append("He decided to run away and came across a cottage. ")
    
    #instantiating extrapolate class, TAKES NOTHING
    e = Extrapolate()
    
    #expected input from storytellingbot
    o_sent = "John took a sharp sword"
    print("\nInput:" + o_sent)
    #o_sent = raw_input("Enter a sentence: ")

    search_sent = e.extrapolate(o_sent)
    
    #MAGIC OF FINDING A SENTENCE IN THE DATABASE GO!!!!!
    
    index = 11
    #index = random.randint(0, len(sent_list)-1)
    print("Test index: "+ str(index+1))
    
   #output = customize(sent_list[index])
    
    #this would be the post

    
