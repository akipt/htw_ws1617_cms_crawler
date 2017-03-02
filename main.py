from crawler import Crawler
from textextractor import TextExtractor
from langprocessor import LangProcessor
import pickle
from document import Document
from indexer import Indexer
from search import Search3
import souper


def main():
    page_list = my_crawler.do_crawling

    # DEBUG
    print("\nSuccessfully parsed: " + my_crawler.start_url + " (found %d files)" % len(my_crawler.pageList))
    print("Files stored in " + my_crawler.baseFolder)

    if len(my_crawler.pageList) > 0:
        for x in my_crawler.pageList:
            print(x.get_full_url())
    # END_OF_DEBUG
    #with open('pickle/pages.pickle', 'wb') as p:
    #    pickle.dump(page_list, p, protocol=2)
    #with open('pickle/pages.pickle', 'rb') as p:
    #    page_list = pickle.load(p)

    docs = {}

    for page in page_list:
       docs[page.fullURL] = Document(souper.get_souped_title(page.html), souper.get_souped_text(page.html), souper.get_encoding(page.html))
    #with open('pickle/docs.pickle', 'wb') as d:
    #   pickle.dump(docs, d, protocol=2)

    l = LangProcessor()

    #with open('pickle/docs.pickle', 'rb') as d:
    #    docs = pickle.load(d)
    csvfile = "word_lemma_mapping.csv"
    fobj_out = open(csvfile, "w")
    fobj_out.close()
    for docid in docs.keys():
        doc = docs[docid]
        print(docid)
        doc.indexliste = l.get_index(doc.text,False)
    #k = 'http://www.datenlabor-berlin.de/index.php?id=11'
    #k = 'http://www.datenlabor-berlin.de'
    #indexliste = l.get_index(docs[k].text)

    inv_index = Indexer.get_inverse_index(docs)
    inv_posindex = Indexer.get_inverse_posindex(docs)

    # Todo: Export des inv. Positionsindexes als CSV
    # import json
    # json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}])
    # '["foo", {"bar": ["baz", null, 1.0, 2]}]'

    # Todo: Hier erfolgt der Aufruf von TokenList und der Export der CSV-Datei



    with open('pickle/invertierter_index.pickle', 'wb') as f:
        pickle.dump(inv_index, f, protocol=2)
    with open('pickle/invertierter_posindex.pickle', 'wb') as p:
        pickle.dump(inv_posindex, p, protocol=2)

    ### Test TF-IDF und Scoring ###
    '''docnum = len(docs)
    print("\nTest TF-IDF: vgl. Folie 26 in 12a")
    for docid in docs.keys():
        print("\tTop words in document {}".format(docid))
        doc_index = docs[docid].indexliste
        scores = {word: Search3.get_tfidf(word, docid, docnum, inv_index) for word in set(doc_index)}
        sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for word, score in sorted_words[:3]:
            print("\t\t{}: {}".format(word, round(score, 3)))'''


if __name__ == "__main__":
    main()
