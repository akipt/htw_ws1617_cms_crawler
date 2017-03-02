# coding: utf8
from langprocessor import LangProcessor


class Document:
    title = ''
    text = ''
    indexliste = []
    abs_tf = {}
    norm_tf = {}
    tf_idf = {}
    encoding = ''

    def __init__(self, title='', text='', encoding=''):
        self.title = title
        self.text = text
        self.encoding = encoding

    def calc_term_frequencies(self):  # TODO: überflüssig?

        for token in self.indexliste:
            if token in self.abs_tf:
                self.abs_tf[token] += 1
            else:
                self.abs_tf[token] = 1

        # normalisieren
        termcount = len(self.indexliste)
        for term, freq in zip(self.abs_tf.keys(), self.abs_tf.values()):
            f = freq / termcount
            self.norm_tf[term] = f

    def do_language_processing(self, l=LangProcessor()):  # TODO: überflüssig
        # self.indexliste = [token for token, d in l.get_index(self.text, 0)]
        self.indexliste = l.get_index(self.text)

    def calc_weight(self, token, idf):  # TODO: überflüssig?
        tf = self.norm_tf[token]
        self.tf_idf[token] = tf * idf
