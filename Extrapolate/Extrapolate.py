#!/usr/bin/python3


#import nltk
from nltk import word_tokenize
from nltk import pos_tag
from nltk.corpus import wordnet
#import nltk.fuf.linearizer
from nltk.stem.wordnet import WordNetLemmatizer as wnl
from re import sub
import string
import random
from genderPredictor import genderPredictor
#nltk.download()
# nltk downloads: maxent_ne_chunker, maxent_treebank_pos_tagger, punkt, wordnet
# install numpy
# WordNetLemmatizer().lemmatize(word,'v')


class Extrapolate:

    def __init__(self):
        print("Setting up Gender Predictor: ")
        self.gp = genderPredictor.genderPredictor()
        accuracy=self.gp.trainAndTest()
        print("Accuracy:", accuracy)
        print ('Most Informative Features')
        feats=self.gp.getMostInformativeFeatures(10)
        
        for feat in feats:
            print (feat)

    def change_gender(self, pnoun, gender):
        pnlist = [(("her", "F"), ("him", "M")),
                  (("she", "F"), ("he", "M")),
                  (("hers", "F"), ("his", "M")),
                  (("herself", "F"), ("himself", "M"))]
        for pair in pnlist:
            for pi, p in enumerate(pair):
                if p[0] == pnoun:
                    return pair[(pi-1)%2][0]
        else:
            return pnoun

    def find_synonyms(self, w, wpos):
        syn_words = []
        synsets = wordnet.synsets(w, pos=wpos)
        for s in synsets:
            for l in s.lemmas():
                syn_words.append(l.name())
        return syn_words

    def replace_proper_nouns(self, o_sent, n_sent):
        proper_nouns = []
        p_pnouns = []

        o_tagged = pos_tag(word_tokenize(o_sent))
        n_tagged = pos_tag(word_tokenize(n_sent))
        
        print("\nTransforming the output:")
        print("Input sentence:", o_sent)
        print("Found sentence:", n_sent)
        print("Input sentence tagged:", o_tagged)
        print("Found sentence tagged:", n_tagged)

        for o in o_tagged:
            if o[1] == 'NNP' and o not in proper_nouns:
                proper_nouns.append(o)

        for n in n_tagged:
            if n[1] == 'PRP' and n not in p_pnouns:
                p_pnouns.append(n)

        print("")

        if (len(proper_nouns) == 1) and (len(p_pnouns) > 0):
            n_sent = sub(r"\b%s\b" %p_pnouns[0][0] , proper_nouns[0][0], n_sent, 1)
            gender = self.gp.classify(proper_nouns[0][0])
            print(proper_nouns[0][0], "is classified as", gender)
            for pnoun in p_pnouns:
                n_pnoun = self.change_gender(pnoun[0], gender)
                n_sent = sub(r"\b%s\b" %pnoun[0] , n_pnoun, n_sent, 1)
        elif len(proper_nouns) < 1:
            print("No proper nouns to replace")
        else:
            print("Not yet implemented, :P")

        return n_sent

    def transform(self, o_sent, n_sent):
        n_sent = self.replace_proper_nouns(o_sent, n_sent)
        return(n_sent)
        
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
        for si, s in enumerate(synonyms):
            s = list(set(s))
            print(tag_list[si][0], ": ", s)
            
        
        search_sent = []
        # creates a list of similar sentences to search for
        for idx, item in enumerate(tag_list):
            # looks for synonyms at the corresponding index, 
            for s in synonyms[idx]:
                temp = self.strip_pos_copy(tag_list)
                temp[idx] = s
                search_sent.append(temp)
        
        for sdx, s in enumerate(search_sent):
            result = ' '.join(s).replace(' ,',',').replace(' .','.').replace(' !','!')
            result = result.replace(' ?','?').replace(' : ',': ').replace(' \'', '\'').replace('_',' ')
            search_sent[sdx] = result
        
        # will get rid of duplicates once i make it hashable
        search_sent = list(set(search_sent))
        
        print("\nSample list of synonymous sentences:")
        for i in range(min(len(search_sent), 20)):
            print(search_sent[i])
            
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
    o_sent = "Stephen took a sharp sword"
    print("\nInput:" + o_sent)
    #o_sent = raw_input("Enter a sentence: ")

    search_sent = e.extrapolate(o_sent)
    
    #MAGIC OF FINDING A SENTENCE IN THE DATABASE GO!!!!!
    
    index = 10
    #index = random.randint(0, len(sent_list)-1)
    #print("\nTest index: "+ str(index+1))
    #print(sent_list[index])
    
    output = e.transform(o_sent, sent_list[index])
    print(output)
    
    #this would be the post

    
