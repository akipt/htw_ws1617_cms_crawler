#!/usr/bin/python3

import sys, getopt
from indexer import Indexer
from langprocessor import LangProcessor
import pickle

## Suche und Ranking mittels TF-IDF ###
def main(argv):
    with open('pickle/invertierter_index.pickle', 'rb') as f:
        inv_ind = pickle.load(f)

    search_term = argv[0]
    docids = set(doc for d, docs in inv_ind.values() for doc in docs)
    docnum = len(docids)

    ergebnis = do_search(search_term, docids, inv_ind)

    print("\nSuche nach " + search_term)
    highscore = 0
    if len(ergebnis) > 0:
        for e in ergebnis:
            doc, score = e
            if highscore < score:
                highscore = score
            score = score / highscore * 100
            print(doc + "  (Relevanz {}%)".format(round(score,0)))
    else:
        print("Nichts gefunden.")

def do_search(query, docids, inv_index):
    l = LangProcessor()

    queryterms = l.get_index(query)
    ergebnis = []
    for docid in docids:
        score = Indexer.get_score(queryterms, docid, len(docids), inv_index)
        if score > 0:
            ergebnis.append((docid, score))

    ergebnis = sorted(ergebnis, key=lambda el: el[1], reverse=True)
    # TODO: erst nach score und dann nach DocID sortieren
    return ergebnis

def tf_normalisieren(inv_index, docids):    # TODO: erstmal nur als Merker, mal sehen wozu man das braucht
    # alle weights normalisieren: jeden teilen durch das maximale Gewicht in diesem Dokument
    for doc_id in docids:
        # tf normalisieren
        maxdtf = max([tf for cf, pl in inv_index.values() for i, tf in zip(pl.keys(), pl.values()) if doc_id == i])
        for cf, pl in inv_index.values():
            if doc_id in pl:
                pl[doc_id] /= maxdtf

if __name__ == "__main__":
    main(sys.argv[1:])
