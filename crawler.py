#from urrlib import parse
from urllib.request import urlopen
import urllib
from bs4 import BeautifulSoup
import datetime

import string
import random
import os
'''ToDo
datenlabor.berlin beachten

Weiterleitungen verfolgen 301 und 302

Dateinamen speichern, Fragezeichen ersetzen

Server error 500

'''
def extractLinks( html):
    
    soup = BeautifulSoup(html.read())

    for a in soup.find_all('a', href=True):
        if any(exclude in a['href'] for exclude in excludedLinks) or a['href'].endswith(excludeExtensions):
            print ("Excluded URL:", a['href'])
        else:
            print ("Found the URL:", a['href'])
            foundLinks.add(a['href'])
    return

def extractText( html):
    
    soup = BeautifulSoup(html)

    return soup.text()

def getAndSaveFile(linkName, directory, fileName):
    
    urllib.request.urlretrieve(linkName,directory + fileName)


def generateFilename( url):

    return url.split('/')[-1]

def getTimeStamp():

    return '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())

def createBaseFolder(directory):

    if not os.path.exists(directory):
        os.makedirs(directory)


contentTypeHTML = 'text/html'

excludedLinks = ['#','http://','https://', 'javascript:']

excludeExtensions = ('.js','.pdf','.zip')


baseUrl = "http://www.datenlabor-berlin.de/"

baseFolder = '/tmp/crawler/'

foundLinks = set()

visitedLinks = set()


def main():

    foundLinks.add("index.php")

    createBaseFolder(baseFolder)

    while (foundLinks):

        linkName = foundLinks.pop()

        if linkName not in visitedLinks:
            print (baseUrl + linkName)

            fileHandle = urlopen( baseUrl+linkName )

            print ("\nParsing: " + baseUrl+linkName + " - " + str(fileHandle.getcode()))

            if (fileHandle.getcode()==200):

                if ((fileHandle.info()['Content-Type'].find(contentTypeHTML)) != -1):
                    print("[" + getTimeStamp() + "] " + fileHandle.geturl())

                    print('File seems to be html')

                    print('Extracting links')

                    extractLinks(fileHandle)

                    getAndSaveFile(baseUrl+linkName,baseFolder,generateFilename(baseUrl+linkName))

                    visitedLinks.add(linkName)





    




        #ToDo: Save file
if __name__ == "__main__":
    main()
