#!/usr/bin/python2.7


#import nltk
from nltk import word_tokenize
from nltk import pos_tag
from nltk.corpus import wordnet
from nltk.stem.wordnet import WordNetLemmatizer as wnl
import string
import random
#nltk.download()
#nltk downloads: maxent_ne_chunker, maxent_treebank_pos_tagger, punkt, wordnet
#install numpy
#WordNetLemmatizer().lemmatize(word,'v')


class Extrapolate:
    def __init__(self):
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
        sent_list.append("The stepmom ordered her to be killed but the huntsman spared her life.")
        sent_list.append("The wolf fell into it and died.")
        sent_list.append("A fairy granted her wish and gave her a seed to plant. ")
        sent_list.append("He decided to run away and came across a cottage. ")
        self.sentences = sent_list

    # returns all the verbs, nouns, and adjs found in a given sentence
    def tag_sent(self, sent):
        tverbs = []
        tnouns = []
        tadjs = []

        tagged = pos_tag(word_tokenize(sent))

        for item in tagged:
                if item[1][0] == 'V':
                    tverbs.append(item[0])
                elif item[1] == 'NN' or item[1] == 'NNS':
                    tnouns.append(item[0])
                elif item[1][0] == 'J':
                    tadjs.append(item[0])

        return tverbs, tnouns, tadjs

    def find_synonyms(self, words, wpos):
        syn_words = []
        for w in words:
            synsets = wordnet.synsets(w, pos=wpos)
            #print("Synsets for", w, "are:", synsets)
            for s in synsets:
                for l in s.lemmas():
                    syn_words.append(l.name())
        return syn_words

    def replace_word(self, sent, o_word, n_word):
        print("Sent:", sent)
        print("O word:", o_word)
        print("N word:", n_word)

        #newsent = []
        cont = True

        while(cont):
            for i in range(len(sent)):
                print("sent", sent[i])
                if sent[i] == o_word[0]:
                    for j in range(1, len(o_word)):
                        if sent[i+j] != o_word[j]:
                            break
                    else:
                        #check at i-1 and i+len(o_word)
                        if(i-1>0 and i+len(o_word) < len(sent) and not sent[i-1].isalpha() and not sent[i+len(o_word)].isalpha()):
                            sent = sent[:i] + n_word + sent[i+len(o_word)]
                    break
            else:
                cont = False
        print(sent)

    def replace_proper_nouns(self, o_sent, n_sent):
        o_i = []
        n_i = []

        o_tagged = pos_tag(word_tokenize(o_sent))
        n_tagged = pos_tag(word_tokenize(n_sent))

        for o in o_tagged:
            if o[1] == 'NNP' and o not in o_i:
                o_i.append(o)

        for n in n_tagged:
            if n[1] == 'PRP' and n not in n_i:
                n_i.append(n)

        #o_sent_strp = o_sent.translate(string.maketrans("",""), string.punctuation)
        #n_sent_strp = n_sent.translate(string.maketrans("",""), string.punctuation)

        #print(o_i)
        #print(n_i)

        # hand waving here for the moment
        if len(o_i) == 1 and len(n_i) > 0:
            #for i in n_i:
            n_sent = n_sent.replace(n_i[0][0], o_i[0][0], 1)
                #n_sent = replace_word(n_sent, i[0], o_i[0][0])
        elif len(o_i) < 1:
            print("No proper nouns to replace")
        else:
            print("Not yet implemented, :P")

        return n_sent

    def extrapolate(self, o_sent="Joan took a sharp sword", sentences=[], index=0):
        print("Test sent:" + o_sent)
        base_o_verbs = []
        base_o_nouns = []
        if sentences == []:
            sentences = self.sentences
        if index < 1:
            index = random.randint(0, len(sentences)-1)

        (o_verbs, o_nouns, o_adjs) = self.tag_sent(o_sent)

        print("\nShowing all verbs, nouns and adjctives in the sentence: \n" + o_sent)
        print("Verbs:", o_verbs)
        print("Nouns:", o_nouns)
        print("Adjectives:", o_adjs)

        print("\nShowing nouns and verbs in base form: ")
        for v in range(len(o_verbs)):
            base_o_verbs.append(wnl().lemmatize(o_verbs[v],'v'))
            print(o_verbs[v]+"-->"+base_o_verbs[v])
        for n in range(len(o_nouns)):
            base_o_nouns.append(wnl().lemmatize(o_nouns[n],'n'))
            print(o_nouns[n]+"-->"+base_o_nouns[n])

        s_verbs = self.find_synonyms(base_o_verbs, wordnet.VERB)
        s_nouns = self.find_synonyms(base_o_nouns, wordnet.NOUN)
        s_adjs = self.find_synonyms(o_adjs, wordnet.ADJ)

        s_verbs = list(set(s_verbs))
        s_nouns = list(set(s_nouns))
        s_adjs = list(set(s_adjs))

        print("\nVerb synonyms list:")
        for a in s_verbs:
            print(a),

        print("\n\nNoun synonyms list:")
        for b in s_nouns:
            print(b),

        print("\n\nAdjective synonyms list:")
        for c in s_adjs:
            print(c),

        print("\nThe original sentence is:")
        print(self.sentences[index])
        n_sent = self.replace_proper_nouns(o_sent, self.sentences[index])
        print("\nThe modified sentence is:")
        print(n_sent)

        return n_sent


if __name__ == '__main__':
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
    sent_list.append("The stepmom ordered her to be killed but the huntsman spared her life.")
    sent_list.append("The wolf fell into it and died.")
    sent_list.append("A fairy granted her wish and gave her a seed to plant. ")
    sent_list.append("He decided to run away and came across a cottage. ")

    # test sentence for now is "She took a sharp sword"
    # all that really matters is that it contains sword actually
    o_sent = raw_input("Enter a sentence: ")

    index = random.randint(0, len(sent_list)-1)
    print("\n\nTest index: "+ str(index+1))
    index = int(raw_input("Enter a number between 1 and "+str(len(sent_list))+": "))-1
    #index = random.randint(0, len(sent_list)-1)

    e = Extrapolate()
    e.extrapolate(o_sent, sent_list, index)
