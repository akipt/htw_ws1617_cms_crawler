# coding: utf8

import csv
import datetime
import os
import sys
import time
import urllib.robotparser
from tempfile import mkdtemp, mkstemp
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse, urlsplit, urlunsplit
from urllib.request import Request, urlopen, build_opener, urlretrieve
import tldextract
from bs4 import BeautifulSoup, SoupStrainer
from noredirection import NoRedirection
from pageclass import Page
import sys, getopt
import souper
from document import Document
import pickle

'''ToDo:
write log (adding timestamps)
fix problem with whitelist and generated absolute links -> change back to relative links? or check domain? or ignore
keep data and only crawl new if changed (keep date of last crawl and only fetch headers?)
'''


class Crawler:
    AGENT_NAME = 'CMSST4 Crawler'
    polite_time = 2  # time in seconds
    contentTypeHTML = 'text/html'
    excluded_links = ['#', 'http://', 'https://', 'javascript:']
    exclude_extensions = ('.js', '.pdf', '.png', '.zip', '.jpg', '.css', '.js', '.doc', '.ppt', '.mp3', '.gif', '.swf')
    found_links = set()
    visited_links = set()
    pageList = []
    whitelisted_domains = []

    def __init__(self, start_url, whitelisted_domains=None):
        if whitelisted_domains is None:
            whitelisted_domains = []
        self.next_time = time.time()
        self.start_url = start_url
        scheme, host, path, query, fragment = urlsplit(start_url)

        # fix problems due to missing http://
        if scheme is '':
            scheme = 'http'
            start_url = '://'.join([scheme, start_url])
            scheme, host, path, query, fragment = urlsplit(start_url)

        # rebuild url (and discard fragment)
        start_url = urlunsplit((scheme, host, path, query, ''))
        print('Start Crawler with seed ' + start_url)
        self.base_url = urlunsplit((scheme, host, '', '', ''))      # root abs (http://test.org or http://sub.test.org)
                                                                    # host: test.org or sub.test.org
        # add domain(s) to whitelist
        tmp = tldextract.TLDExtract(cache_file=False)
        self.registered_domain = tmp(start_url).registered_domain
        self.fill_whitelist(whitelisted_domains, host)

        # create folders

        # old-Version was to create a name randomized temporary folder
        # self.baseFolder = mkdtemp(self.get_time_stamp_wob(), 'crawler')
        # now the output directory equals the script directory plus "out"
        self.baseFolder = os.path.realpath(os.path.dirname(sys.argv[0])) + os.sep + "out"
        print (self.baseFolder)
        self.create_base_folder(self.baseFolder)

        # load robots.txt file
        self.robotsfiles = {}
        self.fetch_robotsfile(host, self.base_url)

        # ready to start crawling -> add start_url to queue
        self.found_links.add(start_url)

    @property
    def do_crawling(self):
        f = open(os.path.join(self.baseFolder, "log.txt"),'wt')
        writer = csv.writer(f)

        while self.found_links:
            url = self.found_links.pop()  # e.g. http://test.org/index.php

            # get absolute url
            parsed_url = urlparse(url)
            if not parsed_url.hostname:
                url = self.base_url + url
                parsed_url = urlparse(url)

            # check domain (or better: host -> host may be on subdomain!)
            if parsed_url.hostname not in self.whitelisted_domains:
                print('External domain ignored: %s' % url)
                return

            # ask robots.txt whether we are allowed to fetch url
            if parsed_url.hostname not in self.robotsfiles:
                self.fetch_robotsfile(parsed_url.hostname, urlunsplit([parsed_url.scheme, parsed_url.hostname,'','','']))
            if not self.robotsfiles[parsed_url.hostname].can_fetch(self.AGENT_NAME, parsed_url.path):
                print('Not allowed to fetch %s' % parsed_url.path)
                return

            # ensure we did not already visit it
            if url in self.visited_links:
                print('Ignoring already visited %s' % url)
                return

            # be polite and wait before crawling
            while time.time() < self.next_time:
                time.sleep(0.5)
            print("[" + self.get_time_stamp() + "] Visiting: %s" % url)
            headers = {'User-Agent': self.AGENT_NAME}
            data = None

            req = Request(url, data, headers)
            try:
                opener = build_opener(NoRedirection)
                self.next_time = time.time() + self.polite_time
                file_handle = opener.open(req)
                # file_handle = urlopen(req)
            except HTTPError as e:  # TODO: Testen, ob der Crawler hier jemals reinläuft oder ob das weg kann
                print('The server couldn\'t fulfill the request. Error code: ', e.code)
                # continue
            except URLError as e:
                print('We failed to reach a server. Reason: ', e.reason)
                # continue

            code = file_handle.getcode()
            header = file_handle.info()

            # handle return codes
            if code in range(300, 308):
                redirection_target = file_handle.headers['Location']
                print("  " + str(code) + " - Redirected! Append target %s to queue" % redirection_target)
                self.found_links.add(redirection_target)
                self.visited_links.add(url)
                continue
            elif code in range(400, 599):
                print("  " + str(code) + " - Error! Ignoring %s" % url)
                continue
            elif code is 204:
                print("  " + str(code) + " - Ignoring empty document %s" % url)
                continue
            else:
                print("  " + str(code) + " - OK. Reading File...")

            # handle mimetype
            mimetype = file_handle.info().get_content_type()  # TODO: evtl. nur main type (Text verwenden) -> .get_content_maintype()
            if mimetype != self.contentTypeHTML:
                print("  Ignoring Document due to wrong MimeType %s" % mimetype)
                continue

            try:
                pagecontent = file_handle.read()
            except Exception:
                print("    Error reading file. Ignored.")
                continue

            # if everything is okay: build Page object and start extracting links
            page = Page()
            page.html = pagecontent
            timestamp1 = header['Date']
            timestamp2 = self.get_time_stamp()
            page.timestampVisited = self.get_time_stamp()
            page.folderName = self.baseFolder
            page.baseURL = self.base_url
            page.fullURL = url
            page.fileName = self.get_and_save_file(url)
            self.visited_links.add(url)

            writer.writerow((page.fullURL, page.fileName, self.get_time_stamp()))
            self.pageList.append(page)

            print('    Extracting Links...')
            self.extract_links(page.html, parsed_url)

        f.close()
        return self.pageList

    def extract_links(self, html, parsed_url):
        links = BeautifulSoup(html, 'lxml', parse_only=SoupStrainer('a', href=True))

        for link in links.find_all('a'):

            linktitle = link.string
            new_url = link['href']
            scheme, host, path, query, fragment = urlsplit(new_url)

            # parsed_newurl = urlparse(new_url)
            # basic filtering
            if len(new_url) is 0:
                print('      Ignoring empty link')
                continue
            elif new_url[0] == '#':
                print('      Ignoring hash link %s' % new_url)
                continue
            elif scheme not in [None, '', 'http', 'https']:
                print('      Ignoring non http(s) links %s' % new_url)
                continue
            elif path.endswith(self.exclude_extensions):
                print('      Ignoring due to file extension: %s' % new_url)
                continue

                # filtering II: domains from whitelist
                # transform to absolute link without fragments (# anchors)
            if host is '':
                host = parsed_url.hostname
            if scheme is '':
                scheme = parsed_url.scheme
            fragment = ''
            new_url = urlunsplit((scheme, host, path, query, fragment))
            domain = tldextract.extract(new_url).registered_domain

            if host not in self.whitelisted_domains and domain not in self.whitelisted_domains:
                print('      Ignoring links to external domain %s' % host)
                continue

                # filtering III:
                # get robots.txt
            if host not in self.robotsfiles:
                print('      Found new domain %s, get robots.txt file' % host)
                self.fetch_robotsfile(host, urlunsplit([scheme, host, '', '', '']))
            if not self.robotsfiles[host].can_fetch(self.AGENT_NAME, path):
                print('      Ignoring (link not allowed to crawl) %s' % new_url)
                continue

            # filtering IV: known links
            if new_url in self.visited_links:  #
                print('      Ignoring already visited %s' % new_url)
                continue
            elif new_url in self.found_links:
                print('      Ignoring, because already queued: %s' % new_url)
                continue

            else:
                # found new link --> save new (absolute) link in queue
                print("      Found new URL:", new_url)
                self.found_links.add(new_url)

        return

    def get_and_save_file(self, link_name):
        tmp_file = mkstemp(".html", "", self.baseFolder)
        urlretrieve(link_name, tmp_file[1])
        return tmp_file[1]

    @staticmethod
    def generate_filename(url):
        return url.split('/')[-1]

    @staticmethod
    def get_time_stamp():
        return '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())

    @staticmethod
    def get_time_stamp_wob():
        return '{:%Y%m%d-%H%M%S}'.format(datetime.datetime.now())

    @staticmethod
    def create_base_folder(directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def fill_whitelist(self, whitelisted_domains, host):

        # add hosts passed as arguments and host of start_url
        self.whitelisted_domains = whitelisted_domains
        if host not in self.whitelisted_domains:
            self.whitelisted_domains.append(host)

        # and duplicate each (domains with and w/o www should be present)
        templist = []
        for d in whitelisted_domains:
            subdomain, domain, suffix = tldextract.extract(d)
            if suffix == '':
                # IP-adresses don't need www -> TODO: are there other domain without tld????
                continue
            if subdomain == '':
                subdomain = 'www'
            else:
                sdlist = tldextract.extract(d).subdomain.split('.')
                if sdlist[0] == 'www':
                    sdlist.remove('www')
                else:  # domains with subdomains get www prefix -> TODO: is this correct? e.g. www.admin.test.org
                    sdlist.append('www')
                    sdlist.reverse()
                subdomain = '.'.join(sdlist)

            if subdomain == '':
                host2 = '.'.join([domain, suffix])
            else:
                host2 = '.'.join([subdomain, domain, suffix])
            if host2 not in self.whitelisted_domains:
                templist.append(host2)
        self.whitelisted_domains.extend(templist)

        return

    def fetch_robotsfile(self, host, base):
        print("        Fetch robots.txt for domain " + host)
        self.robotsfiles[host] = urllib.robotparser.RobotFileParser()
        self.robotsfiles[host].set_url(base + '/robots.txt')

        # be polite and wait before crawling
        while time.time() < self.next_time:
            time.sleep(0.5)
        self.next_time = time.time() + self.polite_time

        # get robots.txt
        try:
            get_url = urlopen(base + '/robots.txt')
            print('        Code ' + str(get_url.code) + ' - OK')
            self.robotsfiles[host].read()
        except HTTPError as e:
            print('        Robots.txt not available. Error code: ', e.code)
        except URLError as e:
            print('        Robots.txt not available. Reason: ', e.reason)
        except Exception:
            print("        Robots.txt not readable for %s" % base)

        # if there is no robots.txt or file is empty: allow all
        if len(self.robotsfiles[host].entries) is 0:
            self.robotsfiles[host].allow_all = True

        return

if __name__ == "__main__":
    argv = sys.argv[1:]
    optlist, args = getopt.getopt(argv, 's:w:')

    whitelist = []
    if len(optlist) == 0:
        if len(args) == 0:
            seed = 'http://www.datenlabor-berlin.de'
            whitelist = ['datenlabor-berlin.de', 'datenlabor.berlin']
        else:
            seed = args[0]
    for opt,arg in optlist:
        if opt == '-s':
            seed = arg
        elif opt == '-w':
            whitelist.append(arg)

    my_crawler = Crawler(seed, whitelist)
    page_list = my_crawler.do_crawling

    # DEBUG
    print("\nSuccessfully parsed: " + my_crawler.start_url + " (found %d files)" % len(my_crawler.pageList))
    print("Files stored in " + my_crawler.baseFolder)

    if len(my_crawler.pageList) > 0:
        for x in my_crawler.pageList:
            print(x.get_full_url())
    # END_OF_DEBUG

    docs = {}
    for page in page_list:
       docs[page.fullURL] = Document(souper.get_souped_title(page.html), souper.get_souped_text(page.html))
    with open('helpers/docs.pickle', 'wb') as d:
       pickle.dump(docs, d, protocol=2)

