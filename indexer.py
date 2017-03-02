# coding: utf8
from langprocessor import LangProcessor
import pickle
from document import Document


class Indexer:
    @staticmethod
    def get_inverse_index(doc_col):
        inv_index = {}

        for doc_id in doc_col.keys():
            # docnum = len(doc_col)
            termnum = len(doc_col[doc_id].indexliste)
            for token in doc_col[doc_id].indexliste:
                if token in inv_index:
                    colfreq, pl = inv_index[token]
                    #     colfreq += 1
                    #     if doc_id in pl:
                    #         pl[doc_id] += 1
                    #     else:
                    #         pl[doc_id] = 1
                    # else:
                    #     colfreq = 1
                    #     pl = {doc_id: 1}
                    colfreq += 1  # absolute termfrequenz in collection
                    if doc_id in pl:
                        pl[doc_id] += (1 / termnum)  # relative termfrequenz
                    else:
                        pl[doc_id] = (1 / termnum)
                else:
                    colfreq = 1
                    pl = {doc_id: (1 / termnum)}
                inv_index[token] = (colfreq, pl)

        return inv_index

    @staticmethod
    def get_inverse_posindex(doc_col):
        inv_posindex = {}

        for doc_id in doc_col.keys():
            termnum = len(doc_col[doc_id].indexliste)
            for i, token in enumerate(doc_col[doc_id].indexliste):
                if token in inv_posindex:
                    colfreq, postinglist = inv_posindex[token]
                    colfreq += 1  # absolute termfrequenz in collection
                    if doc_id in postinglist:
                        tf, positions = postinglist[doc_id]
                        tf += (1 / termnum)  # relative termfrequenz
                        positions.append(i)
                    else:
                        tf = (1 / termnum)
                        positions = [i]
                    postinglist[doc_id] = (tf, positions)

                else:
                    colfreq = 1
                    postinglist = {doc_id: ((1 / termnum), [i])}
                inv_posindex[token] = (colfreq, postinglist)

        return inv_posindex

if __name__ == "__main__":
    l = LangProcessor()
    with open('helpers/docs.pickle', 'rb') as d:
        docs = pickle.load(d)
    csvfile = "out/word_lemma_mapping.csv"

    print("Start Indexing...")
    fobj_out = open(csvfile, "w")
    fobj_out.close()

    for docid in docs.keys():
        doc = docs[docid]
        print(docid)
        doc.indexliste = l.get_index(doc.text, False, csvfile)

    inv_index = Indexer.get_inverse_index(docs)
    inv_posindex = Indexer.get_inverse_posindex(docs)

    # Todo: Export des inv. Positionsindexes als JSON
    # import json
    # json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}])
    # '["foo", {"bar": ["baz", null, 1.0, 2]}]'

    # Todo: Hier erfolgt der Aufruf von TokenList und der Export der CSV-Datei

    with open('helpers/invertierter_index.pickle', 'wb') as invf:
        pickle.dump(inv_index, invf, protocol=2)
    with open('helpers/invertierter_posindex.pickle', 'wb') as invpf:
        pickle.dump(inv_posindex, invpf, protocol=2)