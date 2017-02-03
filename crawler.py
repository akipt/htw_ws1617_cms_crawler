from tempfile import mkdtemp, mkstemp
import urllib.robotparser
from urllib.parse import urlparse, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from urllib.error import  URLError
import urllib
from bs4 import BeautifulSoup, SoupStrainer
import datetime
import os
from pageclass import Page

'''ToDo:
datenlabor.berlin beachten
Weiterleitungen verfolgen 301 und 302
Server error 500
'''

class Crawler:
    AGENT_NAME = 'CMSST Crawler'
    contentTypeHTML = 'text/html'
    excluded_links = ['#', 'http://', 'https://', 'javascript:']
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

        self.rp = urllib.robotparser.RobotFileParser()
        self.rp.set_url(base_url + '/robots.txt')
        self.rp.read()
        if len(self.rp.entries) is 0:
            self.rp.allow_all = True

        if urlparse(base_url).path is '':
            self.found_links.add(base_url+'/')
        else:
            self.found_links.add(base_url)

    @property
    def do_crawling(self):

        while self.found_links:
            url = self.found_links.pop()

            # get absolute url
            parsed_url = urlparse(url)
            if not parsed_url.hostname:
                url = self.base_url + url
                parsed_url = urlparse(url)

            # check domain
            if parsed_url.hostname not in self.whitelisted_domains:
                print('External domain ignored: %s' % parsed_url.hostname)
                return

            # ask robots.txt whether we are allowed to fetch url
            if not self.rp.can_fetch(self.AGENT_NAME, parsed_url.path):
                print('Not allowed to fetch %s' % parsed_url.path)
                return

            # ensure we did not already visit it
            if url in self.visited_links:                       # TODO: evtl. url durch parsed_url.path ersetzen
                print('Ignoring already visited %s' % url)
                return

            print("[" + self.get_time_stamp() + "] Visiting: %s" % url)
            headers = {'User-Agent': self.AGENT_NAME}
            data = None

            req = Request(url, data, headers)
            try:
                file_handle = urlopen(req)
            except URLError as e:
                if hasattr(e, 'reason'):
                    print('  We failed to reach a server. Reason: ', e.reason)
                    continue
                elif hasattr(e, 'code'):
                    print('  The server couldn\'t fulfill the request. Error code: ', e.code)
                    continue


            header = file_handle.info()

            mimetype = file_handle.info().get_content_type()        # TODO: evtl. nur main type (Text verwenden) -> .get_content_maintype()
            if mimetype != self.contentTypeHTML :
                print("  Ignoring Document due to wrong MimeType %s" % mimetype)
                continue

            if file_handle.geturl() is not url:
                print("  Redirected to %s" % file_handle.geturl())
                url = file_handle.geturl()

            code = file_handle.getcode()
            print('  %d - OK, File seems to be html. Reading File...' % code)
            page = Page()
            timestamp1 = header['Date']
            timestamp2 = self.get_time_stamp()
            page.timestampVisited = self.get_time_stamp()
            try:
                page.html = file_handle.read()
            except e:
                print("    Error reading file. Ignored.")
            page.folderName = self.baseFolder
            page.baseURL = self.base_url
            page.fullURL = url
            page.fileName = self.get_and_save_file(url)
            self.visited_links.add(url)
            self.pageList.append(page)

            print('    Extracting Links...')
            self.extract_links(page.html, parsed_url)

        return self.pageList

    def extract_links(self, html, parsed_url):
        links = BeautifulSoup(html, 'lxml', parse_only=SoupStrainer('a', href=True))

        for link in links.find_all('a'):
            try:
                linktitle = link.string
                new_url = link['href']
                scheme, host, path, query, fragment = urlsplit(new_url, '', False)

                if len(new_url) is 0:
                    print('      Ignoring empty link')
                elif new_url[0] == '#':
                    print('      Ignoring hash link %s' % new_url)
                elif host and scheme not in [None, 'http', 'https']:
                    print('      Ignoring non http(s) links %s' % new_url)
                elif new_url in self.excluded_links:
                    print('      Ignoring excluded links %s' % new_url)
                elif host not in self.whitelisted_domains:
                    print('      Ignoring links to external domain %s' % host)
                elif not self.rp.can_fetch(self.AGENT_NAME, path):
                    print('      Ignoring (link not allowed to crawl) %s' % new_url)
                    
                else:
                    if host is '' or scheme is '':
                        scheme = parsed_url.scheme
                        host = parsed_url.hostname
                        new_url = urlunsplit((scheme, host, path, query, fragment))


                    if new_url in self.visited_links:  #
                        print('Ignoring already visited %s' % url)
                    elif new_url in self.found_links:
                        print('      Ignoring, because already queued: %s' % new_url)

                    else:
                        print("      Found new URL:", new_url)

                        # add absolute links
                        self.found_links.add(new_url)        # TODO: add absolute links or relative ones?
            except:
                print("Error.")

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
