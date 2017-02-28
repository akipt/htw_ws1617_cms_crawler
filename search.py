#!/usr/bin/python3

import sys, getopt
import pickle
from shyard import ShYard
from pythonds import Stack
from functools import reduce
from langprocessor import LangProcessor
import math

'''TODO:
NEAR-Suche implementieren (inv_posindex)
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

        with open('pickle/invertierter_index.pickle', 'rb') as f:
            inv_ind = pickle.load(f)
        with open('pickle/invertierter_posindex.pickle', 'rb') as f:
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
                term = l.get_index(teilquery)[0]   # wieder herausgenommen: Autokorrektur zerstört Such-Terms
                #term = teilquery
                if term in inv_ind:
                    docs = inv_ind[term][1]
                else:
                    docs = {}
                st.push(set(docs.keys()))
                # print(st)
            else:
                q2 = st.pop()
                q1 = st.pop()
                ergebnis = {}
                if teilquery == 'AND':
                    ergebnis = reduce(lambda s1, s2: s1 & s2, [q1, q2])
                elif teilquery == 'OR':
                    ergebnis = set(doc for docs in [q1, q2] for doc in docs)
                elif teilquery == 'NOT':
                    st.push(q1)  # zurücklegen
                    q1 = set(doc for d, docs in inv_ind.values() for doc in docs)
                    ergebnis = q1.difference(q2)

                st.push(ergebnis)

        ergebnis = st.pop()
        ergebnis = sorted(list(ergebnis))
        return ergebnis

    @staticmethod
    def vector_search(query, inv_index):
        l = LangProcessor()
        docids = set(doc for d, docs in inv_index.values() for doc in docs)
        queryterms = l.get_index(query)
        ergebnis = []
        for docid in docids:
            score = Search3.get_score(queryterms, docid, len(docids), inv_index)
            if score > 0:
                ergebnis.append((docid, score))

        ergebnis = sorted(ergebnis, key=lambda el: (-el[1], el[0]))
        # nach score (absteigend) und dann docID (aufsteigend)

        return ergebnis

    @staticmethod
    def filter_near(s1, s2):
        doc_id_1, positions_1 = s1
        doc_id_2, positions_2 = s2
        if doc_id_1 == doc_id_2:

            for p in positions_1:
                if (p + 1) in positions_2:
                    return doc_id_1



    @staticmethod
    def phrase_search(query, inv_posindex):
        l = LangProcessor()
        docids = set(doc for d, docs in inv_posindex.values() for doc in docs)
        queryterms = l.get_index(query)
        tempdict = {}

        for word in queryterms:
            if word in inv_posindex.keys():
                df, pl = inv_posindex[word]
                templiste = []
                #for (doc_id, posliste) in zip(pl.keys(), pl.values()[1]):
                for doc_id in pl:
                    posliste = pl[doc_id][1]
                    templiste.append((doc_id, posliste))
                tempdict[word] = templiste

        s1 = tempdict[queryterms[0]]
        s2 = tempdict[queryterms[1]]
        ergebnis = list(filter(lambda x: x != None, map(Search3.filter_near, s1, s2)))

        ergebnis = sorted(ergebnis)
        return ergebnis

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
        #print('Suchergebnisse für Ihre Suche nach "' + query + '":\n')
        print('Suchergebnisse für Ihre Suche:\n')
        for e in ergebnis:
            print(e)
    else:
        print("Nichts gefunden.")

