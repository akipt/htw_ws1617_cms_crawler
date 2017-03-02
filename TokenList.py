# -*- coding: utf-8 -*-
#
# Class contains all tokens + idf + tf_idf

from math import log

abs_tf = {}  # absolute term frequency
norm_tf = {}  # augmented term frequency
idf = {}  # inverse document frequency
tf_idf = {}

documents = {}


class TokenList:
    def __init__(self, documents):
        self.documents = documents
        self.calc_term_frequencies_inverse_document_frequencies()
        self.tf_idf = {}

    def collect_abs_tf(self):
        for document in documents:
            for token in document.abs_tf.keys():
                self.abs_tf[token].append(document.abs_tf[token])

    def collect_norm_tf(self):
        for document in documents:
            for token in document.norm_tf.keys():
                self.norm_tf[token].append(document.norm_tf[token])

    # Todo: Folgende beide Funktionen müssen noch an die neue Datenstruktur angepasst werden
    def calc_inverse_document_frequencies(self):
        documents_including_token = 0
        for token in self.abs_tf.keys():
            for current_doc in self.documents:
                if token in current_doc.abs_tf:
                    documents_including_token += 1
            self.idf[token] = log(len(self.documents) / documents_including_token)

    def calc_term_frequencies_inverse_document_frequencies(self):
        if (self.abs_tf is None) or (self.norm_tf is None):
            self.calc_term_frequencies()
        if self.idf is None:
            self.calc_inverse_document_frequencies()
        for token in self.abs_tf.keys():
            self.tf_idf = self.norm_tf[token] * self.idf[token]
