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

    # @staticmethod
    # def calculate_frequencies(doc_col, inv_index):  #TODO: überflüssig
    #     keyfigures = {}
    #     # cf [collection frequency] = total number of occurrences of a term in the collection
    #     # df [document frequency] = number of documents in the collection that contain a term
    #     # idf [inverse document frequency] =
    #     # tf-idf = importance of terms in a document based on how frequently they appear across multiple documents
    #     #
    #
    #     docnum = len(doc_col)
    #     for term, (cf, pl) in zip(inv_index.keys(), inv_index.values()):
    #         df = len(pl)
    #         idf = math.log10(docnum / df)
    #
    #         # for doc in pl:
    #         #     tf = self.collection[doc].norm_tf[term]
    #         #     tf_idf = tf * idf
    #         for doc_id in pl:
    #             doc_col[doc_id].calc_weight(term, idf)
    #
    #         keyfigures[term] = (cf, df, idf)
    #     return keyfigures

    @staticmethod
    def get_idf(word, docnum, inv_index):  # TODO: überflüssig?
        # docnum = len(doc_col)
        (cf, pl) = inv_index[word]
        df = len(pl)
        idf = math.log10(docnum / df)
        return idf

    @staticmethod
    def get_score(queryterms, doc_id, docnum, inv_index):
        summe = 0
        for word in queryterms:
            tf_idf = Indexer.get_tfidf(word, doc_id, docnum, inv_index)
            summe += tf_idf

        summe = sum(Indexer.get_tfidf(word, doc_id, docnum, inv_index) for word in queryterms)

        return summe

    @staticmethod
    def get_tfidf(word, doc_id, docnum, inv_index):
        # tf-idf pro term und dokument (Zelle in Matrix)

        # cf [collection frequency] = total number of occurrences of a term in the collection
        # df [document frequency] = number of documents in the collection that contain a term
        # idf [inverse document frequency] =
        # tf-idf = importance of terms in a document based on how frequently they appear across multiple documents

        pl = inv_index[word][1]
        df = len(pl)
        idf = math.log10(docnum / df)
        if doc_id in pl:
            tf = pl[doc_id]
        else:
            tf = 0
        tf_idf = tf * idf
        return tf_idf
