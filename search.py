#!/usr/bin/python3

import sys, getopt

from langprocessor import LangProcessor
import pickle


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

    #for token, pos in query_tags:
    for ind in range(0, len(query_tags)):
        token, pos = query_tags[ind]

        if token in ['AND', 'OR', 'ANDNOT', 'NEAR', 'NOT']:
            mode = token;
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
                ntokens = corrwort.split(' ')
                npostags = l.do_pos_tagging(ntokens)
                for i in range(0, len(npostags)):
                    position = ind + i + 1
                    query_tags.insert(position, npostags[i])
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


    if mode == '':
        mode = 'OR'


    if mode == 'NOT':
        # Set mit allen möglichen Dokumenten-ids
        ergebnis = set(doc for d, docs in inv_ind.values() for doc in docs)
        subtr = set(doc for docs in results for doc in docs)
        ergebnis = ergebnis.difference(subtr)

    else:
        ergebnis = results[0]

        if mode == 'OR':
            # for i in range(1, len(results)):
            #     ergebnis = ergebnis.union(results[i])
            #     #test = ergebnis | results[i]
            ergebnis = set(doc for docs in results for doc in docs)
        elif mode == 'AND':
            for i in range(1, len(results)):
                ergebnis = ergebnis.intersection(results[i])
                #test = ergebnis & results[i]
        elif mode == 'ANDNOT':
            for i in range(1, len(results)):
                ergebnis = ergebnis.difference(results[i])
                #test = ergebnis - results[i]


    #print(ergebnis)
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