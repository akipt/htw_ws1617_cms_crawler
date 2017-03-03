# coding: utf8
from langprocessor import LangProcessor


class Document:
    title = ''
    text = ''
    indexliste = []
    wordlemmadict = {}
    index = {}
    posindex = {}
    abs_tf = {}  # absolute term frequency
    norm_tf = {}  # augmented term frequency

    def __init__(self, title='', text=''):
        self.title = title
        self.text = text

    def calc_term_frequencies(self):

        for token in self.indexliste:
            if token in self.abs_tf:
                self.abs_tf[token] += 1
            else:
                self.abs_tf[token] = 1

        # augmented term frequency
        maximum_term_count_in_document = max(self.abs_tf.values())
        for token in self.abs_tf:
            self.norm_tf[token] = self.abs_tf[token] / maximum_term_count_in_document

        ''' # relative token frequence

        termcount = len(self.indexliste)
        for term, freq in zip(self.abs_tf.keys(), self.abs_tf.values()):
            f = freq / termcount
            self.rel_tf[term] = f
        '''