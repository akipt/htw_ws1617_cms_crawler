from tempfile import mkdtemp, mkstemp
from urllib.request import urlopen
import urllib
from bs4 import BeautifulSoup
import datetime
import os
from pageclass import Page

'''ToDo:
datenlabor.berlin beachten

Weiterleitungen verfolgen 301 und 302

Server error 500

'''


class Crawler:

    contentTypeHTML = 'text/html'

    excluded_links = ['#', 'http://', 'https://', 'javascript:', '.png']

    exclude_extensions = ('.js', '.pdf', '.png', '.zip')

    found_links = set()

    visited_links = set()

    pageList = []

    whitelisted_domains = []

    def __init__(self, base_url, whitelisted_domains):

        self.base_url = base_url

        self.whitelisted_domains = whitelisted_domains

        self.baseFolder = mkdtemp('crawler')

        self.create_base_folder(self.baseFolder)

    def do_crawling(self, start_link):

        self.found_links.add(start_link)

        while self.found_links:

            link_name = self.found_links.pop()

            if link_name not in self.visited_links:
                print(self.base_url + link_name)

                file_handle = urlopen(self.base_url + link_name)

                print("\nParsing: " + self.base_url + link_name + " - " + str(file_handle.getcode()))

                if file_handle.getcode() == 200:

                    if (file_handle.info()['Content-Type'].find(self.contentTypeHTML)) != -1:
                        print("[" + self.get_time_stamp() + "] " + file_handle.geturl())

                        print('File seems to be html')

                        print('Extracting links')

                        page = Page()

                        page.html = file_handle.read()

                        self.extract_links(page.html)

                        page.timestampVisited = self.get_time_stamp()

                        page.folderName = self.baseFolder

                        page.baseURL = self.base_url

                        page.fullURL = self.base_url + link_name

                        page.fileName = self.get_and_save_file(self.base_url + link_name)

                        self.visited_links.add(link_name)

                        self.pageList.append(page)
        return self.pageList

    def extract_links(self, html):

        soup_html = BeautifulSoup(html)

        for a in soup_html.find_all('a', href=True):
            # ToDo: Nicht schön diese Abfrage...
            if a['href'].endswith(self.exclude_extensions):
                print("Insignificant extension: ", a['href'])
            elif any(whiteDomains in a['href'] for whiteDomains in self.whitelisted_domains):
                print("Found the URL:", a['href'])
            elif any(excludeURL in a['href'] for excludeURL in self.excluded_links):
                print("Excluded URL:", a['href'])
            else:
                print("Found the URL:", a['href'])
                self.found_links.add(a['href'])
        return

    def get_and_save_file(self, link_name):

        tmp_file = mkstemp(".html", "", self.baseFolder)

        urllib.request.urlretrieve(link_name, tmp_file[1])

        return tmp_file[1]

    def generate_filename(self, url):

        return url.split('/')[-1]

    def get_time_stamp(self):

        return '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())

    def create_base_folder(self, directory):

        if not os.path.exists(directory):
            os.makedirs(directory)