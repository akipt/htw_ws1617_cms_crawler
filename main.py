from crawler import Crawler
from textextractor import TextExtractor
from souppage import SoupPage
from langprocessor import LangProcessor


def main():
    my_crawler = Crawler("http://www.datenlabor-berlin.de", ["datenlabor.berlin", "datenlabor-berlin.de"])
    #page_list = my_crawler.do_crawling
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
    ind = []

    docs2 = {}
    docs2['doc0'] = ('url-platzhalter', 'Wir führen ein Märchen-Theater auf. Sie zog ein neues Kleid an. Sie hatte ein Kleid an. Wir fangen an. Er hörte auf. Wir rufen die Männer an. Ich hole Papa ab. Ich hole ihn ab. Ich fange damit an. Ich kläre Dich auf. Ich höre Dir zu. Wir packen sieben Äpfel ein. Sie gehen schonmal vor. Die Uhr geht vor. Man hört die Kinder im Bett reden. Sie reden in dem Bett.')
    docs2['doc1'] = ('url-platzhalter', 'Einige recht berühmte Schriftsteller wohnten im kleinen Haus an der alten Brücke, z.B. Dante. Rapunzel ließ ihr langes, goldenes Haar herunter. Die Lesung des Märchens Rapunzel dauerte sehr lange. Der Eintritt kostete 5,30€.')
    docs2['doc2'] = ('url-platzhalter', 'Es klapperten die Klapperschlangen bis ihre Klappern schlapper klangen. Ich spiele gern Computerspiele auf meinem C64.')
    docs2['doc3'] = ('url-platzhalter', 'Es war einmal ein Mann, der hieß Popan, der hatte sieben Söhne. Die sagten \"Vater, erzähl uns eine Geschichte!\" Da fing der Mann an. Er sprach - so sagt man - sieben Tage lang.')
    docs2['doc4'] = ('url-platzhalter', "Es fand ein Spurwechsel statt. Es fand ein Spur-Wechsel statt. Es fand ein Spur Wechsel statt. Das Mittag's Menü kostet nur 3€. Das Mittagsmenü ist billig. Das Mittags-Menü ist billig. Das MittagsMenü ist billig. Die Schiff Fahrts Gesellschaft ist pleite.")
    docs2['doc5'] = ('url-platzhalter', 'An- und Abreise. Theater-Spiel. hieb- und stichfest. An-\ngekommen. Spielspaß und -freude. Verweildauer, -länge und -kosten.')

    for doc_id in docs2.keys():
        url, doc = docs2[doc_id]
        ind += l.get_index(doc, doc_id)
    inv_ind = l.invert_index(ind)
    print(inv_ind)

if __name__ == "__main__":
    main()
