from urllib.request import urlopen
import urllib
from bs4 import BeautifulSoup
import datetime

from pageclass import Page

from tempfile import mkdtemp, mkstemp

import os
'''ToDo:
datenlabor.berlin beachten

Weiterleitungen verfolgen 301 und 302

Server error 500

'''


class Crawler:

    contentTypeHTML = 'text/html'

    excludedLinks = ['#', 'http://', 'https://', 'javascript:', '.png']

    excludeExtensions = ('.js', '.pdf', '.png', '.zip')

    foundLinks = set()

    visitedLinks = set()

    pageList = []


    def __init__(self, baseURL, whitelistedDomains):

        self.baseURL = baseURL

        self.whitelistedDomains = whitelistedDomains

        self.baseFolder = mkdtemp('crawler')

        self.createBaseFolder(self.baseFolder)


    def doCrawling(self, startLink):

        self.foundLinks.add(startLink)

        while self.foundLinks:

            linkName = self.foundLinks.pop()

            if linkName not in self.visitedLinks:
                print(self.baseURL + linkName)

                fileHandle = urlopen(self.baseURL + linkName)

                print("\nParsing: " + self.baseURL + linkName + " - " + str(fileHandle.getcode()))

                if fileHandle.getcode() == 200:

                    if (fileHandle.info()['Content-Type'].find(self.contentTypeHTML)) != -1:
                        print("[" + self.getTimeStamp() + "] " + fileHandle.geturl())

                        print('File seems to be html')

                        print('Extracting links')

                        page = Page()

                        page.body = fileHandle.read()

                        soup = BeautifulSoup(page.body)

                        page.title = soup.title.text

                        self.extractLinks(soup)

                        page.timestampVisited = self.getTimeStamp()

                        page.folderName = self.baseFolder

                        page.baseURL = self.baseURL

                        page.fullURL = self.baseURL + linkName


                        #page.body = self.extractText(fileHandle)

                        page.fileName = self.getAndSaveFile(self.baseURL + linkName)

                        self.visitedLinks.add(linkName)

                        self.pageList.append(page)

    def extractText(self, html):
        return

        # soup = BeautifulSoup(html)

        # return(html.body(text=True))

    def extractLinks(self, soupHTML):

        for a in soupHTML.find_all('a', href=True):
            # ToDo: Nicht schön diese Abfrage...
            if ( a['href'].endswith(self.excludeExtensions)):
                print("Insignificant extension: ", a['href'])
            elif any(whiteDomains in a['href'] for whiteDomains in self.whitelistedDomains):
                print("Found the URL:", a['href'])
            elif any(excludeURL in a['href'] for excludeURL in self.excludedLinks):
                print("Excluded URL:", a['href'])
            else:
                print("Found the URL:", a['href'])
                self.foundLinks.add(a['href'])
        return

    def getAndSaveFile(self, linkName):

        #fileName.replace('?','')
        #deaktiviert, da der Dateipfad zu lang werden kann (>255 Zeichen)

        tmpFile = mkstemp(".html","", self.baseFolder)

        urllib.request.urlretrieve( linkName, tmpFile[1] )

        return tmpFile[1]


    def generateFilename(self, url):

        return url.split('/')[-1]

    def getTimeStamp(self):

        return '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())

    def createBaseFolder(self, directory):

        if not os.path.exists(directory):
            os.makedirs(directory)

def main():

    myCrawler = Crawler("http://www.datenlabor-berlin.de/", ["datenlabor.berlin"])
    myCrawler.doCrawling("index.php")

    print("\nSuccessfully parsed: " + myCrawler.baseURL)
    print("Files stored in " + myCrawler.baseFolder)

    for x in myCrawler.pageList:
        print(x.getTitle() + " (" + x.getFullURL() + ")")
        print(x.getBody())


        #ToDo: Save file
if __name__ == "__main__":
    main()