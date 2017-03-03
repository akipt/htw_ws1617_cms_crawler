# coding: utf8
import pickle
import TokenList
from langprocessor import LangProcessor
from itertools import groupby


class Indexer:
    @staticmethod
    def get_inverse_index(doc_col):
        '''
        Calculates the inverse index of a collection from all token lists (indexliste of each document).
        For each Token the absolute cf (collection frequency) is given and
        for each token/document the normalized tf (term frequency) is given
        :param doc_col: dictionary of documents {docid:Documentobject}
        :return: dictionary containing the inverse index {token: (cf, {docid: tf})}
        '''
        inv_index = {}

        for doc_id in doc_col.keys():
            print('\tIndiziere ' + doc_id)
            doc = doc_col[doc_id]
            if len(doc.indexliste) == 0:
                doc.indexliste, doc.wordlemmadict = l.get_index(doc.text)
            if len(doc.index) == 0:
                doc.index = {k: doc.indexliste.count(k) for k, g in groupby(sorted(doc.indexliste))}
            # termnum = sum(doc.index.values())
            termnum = len(doc.indexliste)
            maxtf = max(doc.index.values())
            for token in doc.index:
                abs_tf = doc.index[token]  # absolute termfrequenz in collection
                rel_tf = abs_tf / termnum  # relative termfrequenz
                norm_tf = abs_tf / maxtf  # normalisierte termfrequenz
                if token in inv_index:
                    colfreq, pl = inv_index[token]
                else:
                    colfreq = 0
                    pl = {}
                colfreq += abs_tf
                pl[doc_id] = norm_tf
                inv_index[token] = (colfreq, pl)

        return inv_index

    @staticmethod
    def get_inverse_posindex(doc_col):
        '''
        Calculates the inverse index with positions of a collection from all token lists (indexliste of each document).
        For each Token the absolute cf (collection frequency) and
        for each token/document the relative tf (term frequency) is given
        :param doc_col: dictionary of documents {docid:Documentobject}
        :return: dictionary containing the inverse index {token: (cf, {docid: (tf, [positions])})}
        '''
        inv_posindex = {}

        for doc_id in doc_col.keys():
            doc = doc_col[doc_id]
            if len(doc.indexliste) == 0:
                doc.indexliste, doc.wordlemmadict = l.get_index(doc.text)
            # if len(doc.index) == 0:
            #    doc.index = {k: doc.indexliste.count(k) for k, g in groupby(sorted(doc.indexliste))}
            if len(doc.posindex) == 0:
                posliste = [(k, i) for i, k in enumerate(doc.indexliste)]
                posliste = sorted(posliste)
                doc.posindex = {k: [ind for t, ind in g] for k, g in groupby(posliste, lambda x: x[0])}

            # termnum = sum(len(v) for v in doc.posindex.values())
            termnum = len(doc.indexliste)
            maxtf = max([len(v) for v in doc.posindex.values()])
            for token in doc.posindex:
                abs_tf = len(doc.posindex[token])  # absolute termfrequenz in collection
                rel_tf = abs_tf / termnum  # relative termfrequenz
                norm_tf = abs_tf / maxtf  # normalisierte termfrequenz

                if token in inv_posindex:
                    colfreq, postinglist = inv_posindex[token]
                else:
                    colfreq = 0
                    pl = {}
                colfreq += abs_tf
                positions = doc.posindex[token]
                pl[doc_id] = (norm_tf, positions)
                inv_posindex[token] = (colfreq, pl)

        return inv_posindex

    @staticmethod
    def write_lemma_csv(doc_col, csv_file="out/word_lemma_mapping.csv"):
        '''
        Retrieves the word-lemma mappings of each document, merges them and writes them into a csv file (sorted alphabetically)
        :param doc_col: dictionary of documents {docid:Documentobject}
        :param csv_file: path to csv file with word-lemma mapping
        :return: dictionary with word-lemma mapping for all documents
        '''
        mappingdict = {}
        for doc_id in doc_col.keys():
            doc = doc_col[doc_id]
            if len(doc.wordlemmadict) == 0 or len(doc.indexliste) == 0:
                doc.indexliste, doc.wordlemmadict = l.get_index(doc.text)

            gesdict_set = set(mappingdict)
            docdict_set = set(doc.wordlemmadict)
            for k in gesdict_set.intersection(docdict_set):
                if mappingdict[k] != doc.wordlemmadict[k]:
                    v1 = mappingdict[k]
                    v2 = doc.wordlemmadict[k]
                    raise ValueError('Error: Different lemmata assigned to ' + k + ' (' + v1 + ', ' + v2 + ')')
            mappingdict.update((k, v) for (k, v) in doc.wordlemmadict.items() if v)

        try:
            fobj_out = open(csv_file, "w")
            fobj_out.write('TOKEN\tLEMMA\n')
            for k, v in sorted(mappingdict.items()):
                fobj_out.write(k + '\t' + v + '\n')
            fobj_out.close()
        except:
            print(csv_file + ' could not be written.')

        return mappingdict


if __name__ == "__main__":
    l = LangProcessor()
    with open('helpers/docs.pickle', 'rb') as d:
        docs = pickle.load(d)
    csvfile = "out/word_lemma_mapping.csv"

    print("Starte Indizierung...")

    inv_ind = Indexer.get_inverse_index(docs)
    inv_posind = Indexer.get_inverse_posindex(docs)

    # Todo: Export des inv. Positionsindexes als JSON
    # import json
    # json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}])
    # '["foo", {"bar": ["baz", null, 1.0, 2]}]'

    # Todo: Hier erfolgt der Aufruf von TokenList und der Export der CSV-Datei
    Indexer.write_lemma_csv(docs, "out/word_lemma_mapping.csv")
    # my_token_list = TokenList(docs)

    with open('helpers/invertierter_index.pickle', 'wb') as invf:
        pickle.dump(inv_ind, invf, protocol=2)
    with open('helpers/invertierter_posindex.pickle', 'wb') as invpf:
        pickle.dump(inv_posind, invpf, protocol=2)
