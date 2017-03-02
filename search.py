#!/usr/bin/python3

import sys, getopt
import pickle
from shyard import ShYard
from pythonds import Stack
from functools import reduce
from langprocessor import LangProcessor
import math

'''TODO:
Ranking für Boolsches IR
Aufruf vereinheitlichen (Options wieder raus, Logikanfragen erkennt man auch so)
    3 Modi:
        - Keywords (mehrere Suchbegriffe übergeben) -> Vektorraum-Retrieval
        - Logik -> Boolsches Retrieval
        - NEAR -> Boolsches Retrieval über PosIndex (Abstand 1)
'''


class Search3:
    @staticmethod
    def process(argv):
        erg = []

        with open('helpers/invertierter_index.pickle', 'rb') as f:
            inv_ind = pickle.load(f)
        with open('helpers/invertierter_posindex.pickle', 'rb') as f:
            inv_posind = pickle.load(f)

        optlist, args = getopt.getopt(argv, 'bpk:')

        if len(optlist) == 0:
            # Freie Suche oder Keyword Search
            query = reduce(lambda x, y: x + ' ' + y, args)
            query = query.replace('"', '')
            query = query.replace("'", "")

            erg = Search3.vector_search(query, inv_ind)
        else:
            query = args[0]
            if optlist[0][0] == '-b':
                # boolean logic expression
                erg = Search3.boolean_search(query, inv_ind)

            elif optlist[0][0] == '-p':
                # phrase
                erg = Search3.phrase_search(query, inv_posind)

        return erg

    @staticmethod
    def boolean_search(query, inv_ind):
        l = LangProcessor()
        query_postfix = ShYard.get_postfix(query).split()

        st = Stack()
        for teilquery in query_postfix:
            # print(teilquery)
            if teilquery not in ['AND', 'OR', 'NOT']:
                term = l.get_index(teilquery)[0]  # wieder herausgenommen: Autokorrektur zerstört Such-Terms
                # term = teilquery
                if term in inv_ind:
                    docs = inv_ind[term][1]
                else:
                    docs = {}
                st.push(set(docs.keys()))
                # print(st)
            else:
                q2 = st.pop()
                q1 = st.pop()
                bool_ergebnis = {}
                if teilquery == 'AND':
                    bool_ergebnis = reduce(lambda s1, s2: s1 & s2, [q1, q2])
                elif teilquery == 'OR':
                    bool_ergebnis = set(doc for docs in [q1, q2] for doc in docs)
                elif teilquery == 'NOT':
                    st.push(q1)  # zurücklegen
                    q1 = set(doc for d, docs in inv_ind.values() for doc in docs)
                    bool_ergebnis = q1.difference(q2)

                st.push(bool_ergebnis)

        bool_ergebnis = st.pop()
        bool_ergebnis = sorted(list(bool_ergebnis))
        return bool_ergebnis

    @staticmethod
    def vector_search(query, inv_index):
        l = LangProcessor()
        docids = set(doc for d, docs in inv_index.values() for doc in docs)
        queryterms = l.get_index(query)
        vec_ergebnis = []
        for docid in docids:
            score = Search3.get_score(queryterms, docid, len(docids), inv_index)
            if score > 0:
                vec_ergebnis.append((docid, score))

        vec_ergebnis = sorted(vec_ergebnis, key=lambda el: (-el[1], el[0]))
        vec_ergebnis = list(map(lambda x: x[0], vec_ergebnis))
        # nach score (absteigend) und dann docID (aufsteigend)

        return vec_ergebnis

    @staticmethod
    def phrase_search(query, inv_posindex):
        l = LangProcessor()
        queryterms = l.get_index(query)
        templiste = []

        def filter_near(s1, s2):
            erg = {}
            for docid in s1:
                if docid in s2:
                    pos1 = s1[docid]
                    pos2 = s2[docid]

                    newpositions = []
                    for pos in pos1:
                        if (pos + 1) in pos2:
                            newpositions.append(pos + 1)
                    if len(newpositions) > 0:
                        erg[docid] = set(newpositions)

            return erg

        relevant_doc_ids = reduce(lambda x, y: x & y,
                                  [set(inv_posindex[k][1].keys()) for k in queryterms if k in inv_posindex])

        for word in queryterms:
            if word not in inv_posindex.keys():  # es müssen alle Wörter der Phrase enthalten sein
                return []
            else:
                df, pl = inv_posindex[word]
                doc_pos_mapping = {}
                for doc_id in pl:
                    if doc_id in relevant_doc_ids:
                        posliste = set(pl[doc_id][1])
                        doc_pos_mapping[doc_id] = posliste
                templiste.append(doc_pos_mapping)
        # templiste = [{'d1': {5, 13}, 'd5': {1, 27}}, {'d1': {14}, 'd5': {5, 28}}, {'d1': {33}, 'd5': {3, 7, 29, 44}}]

        phrase_ergebnis = (list(reduce(filter_near, templiste)))

        phrase_ergebnis = sorted(phrase_ergebnis)
        return phrase_ergebnis

    @staticmethod
    def get_score(queryterms, doc_id, docnum, inv_index):
        summe = 0
        for word in queryterms:
            tf_idf = Search3.get_tfidf(word, doc_id, docnum, inv_index)
            summe += tf_idf

        summe = sum(Search3.get_tfidf(word, doc_id, docnum, inv_index) for word in queryterms)

        return summe

    @staticmethod
    def get_tfidf(word, doc_id, docnum, inv_index):
        # tf-idf pro term und dokument (Zelle in Matrix)

        # tf [term frequency] = ? -> relativ, absolut und normiert
        # cf [collection frequency] = total number of occurrences of a term in the collection
        # df [document frequency] = number of documents in the collection that contain a term
        # idf [inverse document frequency] = Bedeutung des Terms in der Gesamtmenge der Dokumente
        # tf-idf = importance of terms in a document based on how frequently they appear across multiple documents

        if word not in inv_index:
            return 0
        pl = inv_index[word][1]
        df = len(pl)
        idf = math.log10(docnum / df)
        if doc_id in pl:
            tf = pl[doc_id]
        else:
            tf = 0
        tf_idf = tf * idf
        return tf_idf


if __name__ == "__main__":
    ergebnis = Search3.process(sys.argv[1:])

    if len(ergebnis) > 0:
        # print('Suchergebnisse für Ihre Suche nach "' + query + '":\n')
        print('Suchergebnisse für Ihre Suche:\n')
        for e in ergebnis:
            print(e)
    else:
        print("Nichts gefunden.")
