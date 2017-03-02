# -*- coding: utf-8 -*-
#
# Class contains all tokens + idf + tf_idf
# when instanciated, all the values get calculated via the given document dictionary

from math import log


class TokenList:

    abs_tf = {}  # absolute term frequency
    norm_tf = {}  # augmented term frequency
    idf = {}  # inverse document frequency
    tf_idf = {}

    documents = {}

    def __init__(self, documents):
        self.documents = documents
        self.calc_term_frequencies_inverse_document_frequencies()

    def collect_norm_tf(self):
        for document in self.documents:
            for token in document.norm_tf.keys():
                self.norm_tf[token].append(document.norm_tf[token])

    def collect_abs_tf(self):
        for document in self.documents:
            for token in document.abs_tf.keys():
                self.abs_tf[token].append(document.abs_tf[token])

    # Todo: Folgend Funktion muss noch an die neue Datenstruktur angepasst werden
    def calc_inverse_document_frequencies(self):
        documents_including_token = 0
        for token in self.abs_tf.keys():
            for current_doc in self.documents:
                if token in current_doc.abs_tf:
                    documents_including_token += 1
            self.idf[token] = log(len(self.documents) / documents_including_token)

    def calc_term_frequencies_inverse_document_frequencies(self):
        if self.norm_tf is None:
            self.collect_norm_tf()
        if self.abs_tf is None:
            self.collect_abs_tf()
        if self.idf is None:
            self.calc_inverse_document_frequencies()
        for token in self.abs_tf.keys():
            token_total_norm_tf = 0
            for entry in self.norm_tf[token]:
                token_total_norm_tf += entry.pop()
            self.tf_idf = token_total_norm_tf * self.idf[token]
