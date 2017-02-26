#!/usr/bin/python3

import sys
from functools import reduce
import pickle
from langprocessor import LangProcessor


def main(argv):
    with open('pickle/invertierter_index.pickle', 'rb') as f:
        inv_ind = pickle.load(f)

    l = LangProcessor()
    search_term = argv[0]
    print("Suche nach: " + search_term)
    mode = ''
    results = []

    ###### NLP ######

    # remove hyphens
    search_term = l.remove_hyphens(search_term)

    # tokenize
    query_tokens = search_term.split(' ')

    # POS Tagging
    query_tags = l.do_pos_tagging(query_tokens)

    # Bindestrich-Substantive?
    l.find_compound_nouns(query_tags, query_tokens)

    # for token, pos in query_tags:
    for ind, (token, pos) in enumerate(query_tags):

        if token in ['AND', 'OR', 'ANDNOT', 'NEAR', 'NOT']:
            mode = token
            continue
        elif pos in l.ausschlusstags:
            continue
        elif pos != 'NE':

            # Stoppwörter entfernen
            if token.casefold() in l.stopwords:
                continue

            # Tippfehler korigieren
            corrwort = l.correct_typo(token)
            # wenn Korrektur mehr als 1 Wort ergibt: in Postag-Liste einfügen und einzeln verarbeiten
            if len(corrwort.split(' ')) > 1:
                npostags = l.do_pos_tagging(corrwort.split(' '))
                for i, newpostag in enumerate(npostags):
                    position = ind + i + 1
                    query_tags.insert(position, newpostag)
                continue

            # lemmatisieren und normalisieren
            token = l.find_lemma(corrwort)

        token = token.casefold()
        #### Ende NLP ######

        # ergebnisliste
        if token not in inv_ind:
            results.append({})
            continue
        else:
            docfreq, docs = inv_ind[token]
            results.append(docs)

    ergebnis = {}
    if mode == '':
        mode = 'OR'

    if mode == 'NOT':
        # Set mit allen möglichen Dokumenten-ids
        ergebnis = set(doc for d, docs in inv_ind.values() for doc in docs)
        subtr = set(doc for docs in results for doc in docs)
        ergebnis = ergebnis.difference(subtr)

    else:

        if mode == 'OR':
            # ergebnis = reduce(lambda s1, s2: s1 | s2, results)
            ergebnis = set(doc for docs in results for doc in docs)

        elif mode == 'AND':
            ergebnis = reduce(lambda s1, s2: s1 & s2, results)
            # ergebnis = results[0]
            # for i in range(1, len(results)):
            #     ergebnis = ergebnis.intersection(results[i])
            #     #test = ergebnis & results[i]

        elif mode == 'ANDNOT':
            ergebnis = reduce(lambda s1, s2: s1 - s2, results)
            # ergebnis = results[0]
            # for i in range(1, len(results)):
            #     ergebnis = ergebnis.difference(results[i])
            #     #test = ergebnis - results[i]

    # print(ergebnis)
    if len(ergebnis) > 0:
        print("Suchergebnisse: \n")
        for e in ergebnis:
            print(e)
    else:
        print("Nichts gefunden.")
        if len(results) > 1:
            print('\nTreffer für einzelne Suchbegriffe:')
            altergebnis = set(doc for docs in results for doc in docs)
            for e in altergebnis:
                print(e)


if __name__ == "__main__":
    main(sys.argv[1:])
