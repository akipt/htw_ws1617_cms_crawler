from crawler import Crawler
from textextractor import TextExtractor
from souppage import SoupPage
from langprocessor import LangProcessor
import pickle
from document import Document
from indexer import Indexer


def main():
    my_crawler = Crawler("http://www.datenlabor-berlin.de", ["datenlabor.berlin", "datenlabor-berlin.de"])
    # page_list = my_crawler.do_crawling
    page_list = []

    # DEBUG
    print("\nSuccessfully parsed: " + my_crawler.start_url + " (found %d files)" % len(my_crawler.pageList))
    print("Files stored in " + my_crawler.baseFolder)

    if len(my_crawler.pageList) > 0:
        for x in my_crawler.pageList:
            print(x.get_full_url())
    # END_OF_DEBUG

    soup_pages = []

    for page in page_list:
        souppage = SoupPage()
        souppage.title = TextExtractor.extract_title(page.html)
        soup_pages.append(souppage)

    l = LangProcessor()

    docs = {}
    # docs['doc0'] = Document('url1','Dokument 1','Wir führen ein Märchen-Theater auf. Sie zog ein neues Kleid an. Sie hatte ein Kleid an. Wir fangen an. Er hörte auf. Wir rufen die Männer an. Ich hole Papa ab. Ich hole ihn ab. Ich fange damit an. Ich kläre Dich auf. Ich höre Dir zu. Wir packen sieben Äpfel ein. Sie gehen schonmal vor. Die Uhr geht vor. Man hört die Kinder im Bett reden. Sie reden in dem Bett.')
    # docs['doc1'] = Document('url1','Dokument 2','Einige recht berühmte Schriftsteller wohnten im kleinen Haus an der alten Brücke, z.B. Dante. Rapunzel ließ ihr langes, goldenes Haar herunter. Die Lesung des Märchens Rapunzel dauerte sehr lange. Der Eintritt kostete 5,30€.')
    # docs['doc2'] = Document('url1','Dokument 3','Es klapperten die Klapperschlangen bis ihre Klappern schlapper klangen. Ich spiele gern Computerspiele auf meinem C64.')
    # docs['doc3'] = Document('url1','Dokument 4','Es war einmal ein Mann, der hieß Popan, der hatte sieben Söhne. Die sagten \"Vater, erzähl uns eine Geschichte!\" Da fing der Mann an. Er sprach - so sagt man - sieben Tage lang.')
    # docs['doc4'] = Document('url1','Dokument 5',"Es fand ein Spurwechsel statt. Es fand ein Spur-Wechsel statt. Es fand ein Spur Wechsel statt. Das Mittag's Menü kostet nur 3€. Das Mittagsmenü ist billig. Das Mittags-Menü ist billig. Das MittagsMenü ist billig. Die Schiff Fahrts Gesellschaft ist pleite.")
    # docs['doc5'] = Document('url1','Dokument 6','An- und Abreise. Theater-Spiel. hieb- und stichfest. An-\ngekommen. Spielspaß und -freude. Verweildauer, -länge und -kosten.')
    docs['d1'] = Document('url1', 'Dokument 1', 'Informatik Bauing. HTW HWR Beuth TH Berlin Brandenburg')
    docs['d2'] = Document('url1', 'Dokument 2', 'Informatik Bauing. HTW HWR Beuth TH Berlin Brandenburg')
    docs['d3'] = Document('url1', 'Dokument 3', 'Informatik Bauing. HTW HWR Beuth TH Berlin Brandenburg Informatik Bauing. HTW HWR Beuth TH Berlin Brandenburg')
    docs['d4'] = Document('url1', 'Dokument 4', 'Informatik HTW Beuth TH Berlin Brandenburg')
    docs['d5'] = Document('url1', 'Dokument 5', 'Informatik HTW HTW HTW HTW HWR HWR HWR HWR HWR Beuth Beuth Beuth TH TH TH TH TH TH Berlin Berlin Berlin Berlin Berlin Berlin Berlin Brandenburg Brandenburg Brandenburg Brandenburg Brandenburg Brandenburg Brandenburg Brandenburg')
    docs['d6'] = Document('url1', 'Dokument 6', 'HWR HWR HWR HWR HWR Beuth Beuth Beuth Berlin Berlin Berlin Berlin Berlin Berlin Berlin')
    # docs['doc1'] = Document('', '', 'Studium Informatik an einer FH in Berlin')
    # docs['doc2'] = Document('', '', 'Die Fachhochschule in Brandenburg')
    # docs['doc3'] = Document('', '', 'Studium an der HTW Berlin')
    # docs['doc4'] = Document('', '', 'Studium Informatik in Brandenburg')
    # docs['doc5'] = Document('', '', 'Studium an der FH Brandenburg')


    for docid in docs.keys():
        doc = docs[docid]
        doc.indexliste = l.get_index(doc.text)
        #doc.do_language_processing(l)
        doc.calc_term_frequencies()

    inv_index = Indexer.get_inverse_index(docs)
    inv_posindex = Indexer.get_inverse_posindex(docs)


    with open('pickle/invertierter_index.pickle', 'wb') as f:
        pickle.dump(inv_index, f, protocol=2)
    with open('pickle/invertierter_posindex.pickle', 'wb') as p:
        pickle.dump(inv_posindex, p, protocol=2)

    ### Test TF-IDF und Scoring ###
    docnum = len(docs)
    print("\nTest TF-IDF: vgl. Folie 26 in 12a")
    for docid in docs.keys():
        print("\tTop words in document {}".format(docid))
        doc_index = docs[docid].indexliste
        scores = {word: Indexer.get_tfidf(word, docid, docnum, inv_index) for word in set(doc_index)}
        sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for word, score in sorted_words[:3]:
            print("\t\t{}: {}".format(word, round(score, 3)))

    query = "Informatik HTW Berlin"
    #query = "Informatik HWR"           # Negativbeispiel
   # query = "Studium Informatik in Berlin"

    print("\n\nSuche nach " + query)
    queryterms = l.get_index(query)
    ergebnis = []
    for docid in docs.keys():
        score = Indexer.get_score(queryterms, docid, docnum, inv_index)
        if score > 0:
            ergebnis.append((docid, score))

    ergebnis = sorted(ergebnis, key=lambda el: (-el[1], el[0]))   # nach score (absteigend) und dann docID (aufsteigend)
    for e in ergebnis:
        doc, score = e
        print(doc + "  (score {})".format(round(score,3)))


if __name__ == "__main__":
    main()
