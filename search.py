#!/usr/bin/python3

import sys, getopt
import pickle
from shyard import ShYard
from pythonds import Stack
from functools import reduce
from langprocessor import LangProcessor
import math


def get_score(queryterms, doc_id, docnum, inv_index):
    '''
    Calculate the Score for a query and a document by adding up the TF-IDF of each query token
    :param queryterms: list of query tokens (nlp-processed)
    :param doc_id: ID of the document to be scored
    :param docnum: number of documents in collection
    :param inv_index: dictionary containing the inverse index
    :return: score as double value
    '''
    summe = 0
    for word in queryterms:
        tf_idf = get_tfidf(word, doc_id, docnum, inv_index)
        summe += tf_idf

    summe = sum(get_tfidf(word, doc_id, docnum, inv_index) for word in queryterms)

    return summe


def get_tfidf(word, doc_id, docnum, inv_index):
    '''
    Calculate TF-IDF per token and document
    :param word: token (nlp-prcessed)
    :param doc_id: ID of the document
    :param docnum: number of documents in collection
    :param inv_index: dictionary containing the inverse index
    :return: TF-IDF as double value
    '''
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


class Search3:
    @staticmethod
    def process(argv):
        '''
        Reads in the parameters, starts one of the available searches and return the search result
        :param argv: search terms and options (-b for boolean search, -p for phrase search)
        :return: list of document IDs mathcing the query
        '''
        erg = []

        with open('helpers/invertierter_index.pickle', 'rb') as f:
            inv_ind = pickle.load(f)
        with open('helpers/invertierter_posindex.pickle', 'rb') as f:
            inv_posind = pickle.load(f)

        optlist, args = getopt.getopt(argv, 'bpk:')

        if len(optlist) == 0:
            # Freie Suche oder Keyword Search
            args = list(set(args))  # doppelte Eingaben filtern
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
        '''
        Conducts a Boolean Retrieval for a query containig logical expressions.
        First, the expression is parsed and converted to inverse polish notation.
        Afterwards, the search result for each token is retrieved and results are merged
        :param query: String containing logical expression (AND, OR, NOT supported)
        :param inv_ind: dictionary containing inverse index
        :return: list of matching document IDs, sorted by document ID
        '''
        l = LangProcessor()
        query_postfix = ShYard.get_postfix(query).split()

        st = Stack()
        for term in query_postfix:
            if term not in ['AND', 'OR', 'NOT']:
                token = l.get_index(term)[0]
                if token in inv_ind:
                    docs = inv_ind[token][1]
                else:
                    docs = {}
                st.push(set(docs.keys()))
            else:
                q2 = st.pop()
                q1 = st.pop()
                bool_ergebnis = {}
                if term == 'AND':
                    bool_ergebnis = reduce(lambda s1, s2: s1 & s2, [q1, q2])
                elif term == 'OR':
                    bool_ergebnis = set(doc for docs in [q1, q2] for doc in docs)
                elif term == 'NOT':
                    st.push(q1)  # zurücklegen
                    q1 = set(doc for d, docs in inv_ind.values() for doc in docs)
                    bool_ergebnis = q1.difference(q2)

                st.push(bool_ergebnis)

        bool_ergebnis = st.pop()
        bool_ergebnis = sorted(list(bool_ergebnis))
        return bool_ergebnis

    @staticmethod
    def vector_search(query, inv_index):
        '''
        Conducts a vector retrieval
        :param query: String with query term(s)
        :param inv_index: dictionary containing inverse index
        :return: list of matching document IDs, sorted by TF-IDF
        '''
        l = LangProcessor()
        docids = set(doc for d, docs in inv_index.values() for doc in docs)
        queryterms = l.get_index(query)
        vec_ergebnis = []
        for docid in docids:
            score = get_score(queryterms, docid, len(docids), inv_index)
            if score > 0:
                vec_ergebnis.append((docid, score))

        vec_ergebnis = sorted(vec_ergebnis, key=lambda el: (-el[1], el[0]))
        vec_ergebnis = list(map(lambda x: x[0], vec_ergebnis))
        # nach score (absteigend) und dann docID (aufsteigend)

        return vec_ergebnis

    @staticmethod
    def phrase_search(query, inv_posindex):
        '''
        Conducts a phrase search (boolean retrieval with positions).
        First, a temporary list is constucted, containing the token list (dictionary) for each token in the phrase
        (only documents, which contain all words of the phrase are included -> each posting list contains the same document IDs!)
        These posting lists are then reduced to a list of document IDs
        :param query: String containg the query phrase
        :param inv_posindex: dictionary containing inverse index
        :return: list of matching document IDs, sorted by position of phrase appearance
        '''
        l = LangProcessor()
        queryterms = l.get_index(query)
        templiste = []

        def filter_near(s1, s2):
            '''
            Custom Reduce Function: two postings are merged, if they contain at least one consecutive position - if not, the posting is deleted
            :param s1: posting list and positions of actual word (order is important!) {docid1:{1, 3}, docid2:{5}}
            :param s2: posting list of next word {docid1:{4, 8}, docid2:{7}}
            :return: merged posting list {docid1:{4}} -> will be used as s1 in next call
            '''
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

        #phrase_ergebnis = (list(reduce(filter_near, templiste)))
        phrase_ergebnis = reduce(filter_near, templiste)

        # umwandeln in Liste und sortieren nach Position
        phrase_ergebnis = [(k, v) for k, v in phrase_ergebnis.items()]
        phrase_ergebnis = sorted(phrase_ergebnis, key=lambda el: (el[1], el[0]))
        phrase_ergebnis = list(map(lambda x: x[0], phrase_ergebnis))
        return phrase_ergebnis


if __name__ == "__main__":
    ergebnis = Search3.process(sys.argv[1:])

    if len(ergebnis) > 0:
        # print('Suchergebnisse für Ihre Suche nach "' + query + '":\n')
        print('Suchergebnisse für Ihre Suche:\n')
        for e in ergebnis:
            print(e)
    else:
        print("Nichts gefunden.")
