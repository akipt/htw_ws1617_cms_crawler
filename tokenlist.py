# -*- coding: utf-8 -*-
#
# Class contains all the tokens absolute term frequence + relative tf + idf + tf_idf
#
# when instanciated, the idf & tf_idf values get calculated via the given document dictionary
# absolute and relative tf are already calculated in the document class

from math import log
import operator


class TokenList:

    abs_tf = {}  # absolute term frequency
    norm_tf = {}  # augmented term frequency
    idf = {}  # inverse document frequency
    tf_idf = {}

    documents = {}

    def __init__(self, documents):
        self.documents = documents
        self.collect_norm_tf()
        self.collect_abs_tf()
        self.calc_inverse_document_frequencies()
        self.calc_term_frequencies_inverse_document_frequencies()
        self.export_csv()

    def collect_norm_tf(self):
        for document in self.documents.values():
            for key, value in document.norm_tf.items():
                self.norm_tf[key] = value
        print (self.norm_tf)
        print ("Klappt")

    def collect_abs_tf(self):
        for document in self.documents.values():

            for token in document.abs_tf.keys():
                self.abs_tf[token] = document.abs_tf[token]
        print(self.abs_tf)

    def calc_inverse_document_frequencies(self):
        for token in self.abs_tf.keys():
            self.idf[token] = log(len(self.documents) / self.abs_tf[token]) # das ist falsch! es muss durch df geteilt werden, nicht durch abs_tf!
        print(self.idf)

    def calc_term_frequencies_inverse_document_frequencies(self):
        for token in self.abs_tf.keys():
            for document in self.documents.values():
                self.tf_idf[token] = self.norm_tf[token] * self.idf[token]
        print(self.tf_idf)
    def export_csv(self):


        # sort an dictionary by value in descending order and return as list
        sorted_idf_list = sorted(self.idf.items(), key=operator.itemgetter(1), reverse=True)
        print(sorted_idf_list)

        # now we have a ordered token:idf list

        # ##
        # build csv head
        # ##

        sep = ";"
        column_titles = ""

        # add column title for token name
        column_titles += ("token" + sep)

        # column title for tf_idf
        column_titles += ("(idf)" + sep)

        for document in self.documents.values():
            column_titles += (document.title + " (absolute tf)" + sep) # column titles tf_abs
            column_titles += (document.title + " (normalized tf)" + sep) # column titles tf_abs
            column_titles += (document.title + " (tf-idf)" + sep) # column titles tfidf


        column_titles += "\n"

        out = open('out/out.csv', 'w')

        out.write(column_titles)
        out.write('\n')
        # TODO: Der Inhalt fehlt noch!
        out.close()

        print ("Export of TF-CSV done.")