
from crawler import Crawler

def main():

    myCrawler = Crawler("http://www.datenlabor-berlin.de/", ["datenlabor.berlin"])
    pageList = myCrawler.doCrawling("index.php")

    print("\nSuccessfully parsed: " + myCrawler.baseURL)
    print("Files stored in " + myCrawler.baseFolder)

    for x in myCrawler.pageList:
        print(x.getTitle() + " (" + x.getFullURL() + ")")


if __name__ == "__main__":
    main()