# coding: utf8
import math


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

