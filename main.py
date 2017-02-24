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

    doc0 = "Wir führen ein Märchen-Theater auf. Sie zog ein neues Kleid an. Sie hatte ein Kleid an. Wir fangen an. Er hörte auf. Wir rufen die Männer an. Ich hole Papa ab. Ich hole ihn ab. Ich fange damit an. Ich kläre Dich auf. Ich höre Dir zu. Wir packen sieben Äpfel ein. Sie gehen schonmal vor. Die Uhr geht vor. Man hört die Kinder im Bett reden. Sie reden in dem Bett."
    doc1 = "Einige recht berühmte Schriftsteller wohnten im kleinen Haus an der alten Brücke, z.B. Dante. Rapunzel ließ ihr langes, goldenes Haar herunter. Die Lesung des Märchens Rapunzel war hieb- und stichfest und dauerte sehr lange. Der Eintritt kostete 5,30€."
    doc2 = "Es klapperten die Klapperschlangen bis ihre Klappern schlapper klangen. Ich spiele gern Computerspiele auf meinem C64."
    doc3 = "Es war einmal ein Mann, der hieß Popan, der hatte sieben Söhne. Die sagten \"Vater, erzähl uns eine Geschichte!\" Da fing der Mann an. Er sprach - so sagt man - sieben Tage lang."
    doc4 = "Es fand ein Spurwechsel statt. Es fand ein Spur-Wechsel statt. Es fand ein Spur Wechsel statt. Das Mittag's Menü kostet nur 3€. Das Mittagsmenü ist billig. Das Mittags-Menü ist billig. Das MittagsMenü ist billig. Die Schiff Fahrts Gesellschaft ist pleite."
    docs = [doc0, doc1, doc2, doc3, doc4]
    l = LangProcessor()
    docID = 0
    ind = []

    for doc in docs:
        docID += 1
        ind += l.getIndex(doc, docID)

    invInd = l.getInverseIndex(ind)
    print(invInd)

if __name__ == "__main__":
    main()
