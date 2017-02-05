from crawler import Crawler
from textextractor import TextExtractor
from souppage import SoupPage


def main():

    #my_crawler = Crawler("http://www.datenlabor-berlin.de", ["datenlabor.berlin", "datenlabor-berlin.de"])
    my_crawler = Crawler("http://admin.kuleuven.be")
    #my_crawler = Crawler("http://141.45.59.146")
    #my_crawler = Crawler("www.admin.larla.net")
    page_list = my_crawler.do_crawling

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

if __name__ == "__main__":
    main()