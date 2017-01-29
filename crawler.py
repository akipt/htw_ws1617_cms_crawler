
from urllib.request import urlopen
import urllib
from bs4 import BeautifulSoup
import datetime

from tempfile import mkdtemp, mkstemp

import os
'''ToDo:
datenlabor.berlin beachten

Weiterleitungen verfolgen 301 und 302

Dateinamen speichern, Fragezeichen ersetzen

Server error 500

'''
class crawler:

    contentTypeHTML = 'text/html'

    excludedLinks = ['#', 'http://', 'https://', 'javascript:']

    excludeExtensions = ('.js', '.pdf', '.png', '.zip')

    foundLinks = set()

    visitedLinks = set()

    def __init__(self, baseURL):

        self.baseURL = baseURL

        self.baseFolder = mkdtemp('crawler')

        self.createBaseFolder(self.baseFolder)


    def doCrawling(self, startLink):

        self.foundLinks.add(startLink)

        while (self.foundLinks):

            linkName = self.foundLinks.pop()

            if linkName not in self.visitedLinks:
                print(self.baseURL + linkName)

                fileHandle = urlopen(self.baseURL + linkName)

                print("\nParsing: " + self.baseURL + linkName + " - " + str(fileHandle.getcode()))

                if (fileHandle.getcode() == 200):

                    if ((fileHandle.info()['Content-Type'].find(self.contentTypeHTML)) != -1):
                        print("[" + self.getTimeStamp() + "] " + fileHandle.geturl())

                        print('File seems to be html')

                        print('Extracting links')

                        self.extractLinks(fileHandle)

                        self.getAndSaveFile(self.baseURL + linkName)

                        self.visitedLinks.add(linkName)

    def extractLinks(self, html):

        soup = BeautifulSoup(html.read())

        for a in soup.find_all('a', href=True):
            if any(exclude in a['href'] for exclude in self.excludedLinks) or a['href'].endswith(self.excludeExtensions):
                print ("Excluded URL:", a['href'])
            else:
                print ("Found the URL:", a['href'])
                self.foundLinks.add(a['href'])
        return

    def extractText(self, html):

        soup = BeautifulSoup(html)

        return soup.text()

    def getAndSaveFile(self, linkName):

        #fileName.replace('?','')
        #deaktiviert, da der Dateipfad zu lang werden kann (>255 Zeichen)

        tmpFile = mkstemp(".html","", self.baseFolder)

        urllib.request.urlretrieve( linkName, tmpFile[1] )


    def generateFilename(self, url):

        return url.split('/')[-1]

    def getTimeStamp(self, ):

        return '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())

    def createBaseFolder(self, directory):

        if not os.path.exists(directory):
            os.makedirs(directory)

def main():

    myCrawler = crawler("http://www.datenlabor-berlin.de/")
    myCrawler.doCrawling("index.php")

    print("\nSuccessfully parsed: " + myCrawler.baseURL)
    print("Files stored in " + myCrawler.baseFolder)


        #ToDo: Save file
if __name__ == "__main__":
    main()