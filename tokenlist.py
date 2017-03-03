# -*- coding: utf-8 -*-
#
# Class contains all the tokens absolute term frequence + relative tf + idf + tf_idf
#
# when instanciated, the idf & tf_idf values get calculated via the given document dictionary
# absolute and relative tf are already calculated in the document class

from math import log
import csv


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

    def collect_norm_tf(self):
        for document in self.documents.values():
            for token in document.norm_tf.values():
                self.norm_tf[token][document.title] = document.norm_tf[token]

    def collect_abs_tf(self):
        for document in self.documents.values():
            for token in document.abs_tf.keys():
                self.abs_tf[token][document.title] = document.abs_tf[token]

    def calc_inverse_document_frequencies(self):
        for token in self.abs_tf.keys():
            self.idf[token] = log(len(self.documents) / len(self.abs_tf[token]))

    def calc_term_frequencies_inverse_document_frequencies(self):
        for token in self.abs_tf.keys():
            for document in self.documents.values():
                self.tf_idf[token][document.title] = self.norm_tf[token][document.title] * self.idf[token]

    def export_csv(self):
        f = open("out/frequencies.txt", 'wt')
        writer = csv.writer(f)
        writer.writerow()
        f.close()