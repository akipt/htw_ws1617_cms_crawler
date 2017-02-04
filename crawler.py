from tempfile import mkdtemp, mkstemp
import urllib.robotparser
from urllib.parse import urlparse, urlsplit, urlunsplit
from urllib.request import Request, urlopen, HTTPErrorProcessor, build_opener
from urllib.error import URLError
from bs4 import BeautifulSoup, SoupStrainer
import tldextract
import datetime
import os
from pageclass import Page
from noredirection import NoRedirection

'''ToDo:
polite crawler -> frequency -> see http://blog.mischel.com/2011/12/20/writing-a-web-crawler-politeness/
don't follow redirects automatically, because checks don't work -> get redirect location and add it to queue
fix problem with whitelist and generated absolute links -> change back to relative links? or check domain? or ignore
'''

class Crawler:
    AGENT_NAME = 'CMSST4 Crawler'
    contentTypeHTML = 'text/html'
    excluded_links = ['#', 'http://', 'https://', 'javascript:']
    exclude_extensions = ('.js', '.pdf', '.png', '.zip', '.jpg', '.css', '.js', '.doc', '.ppt', '.mp3', '.gif', '.swf')
    found_links = set()
    visited_links = set()
    pageList = []
    whitelisted_domains = []

    def __init__(self, start_url, whitelisted_domains=[]):
        self.start_url = start_url

        scheme, host, path, query, fragment = urlsplit(start_url)

        # discard www subdomain, because things get difficult
        subdomain, domain, suffix = tldextract.extract(start_url)
        if subdomain == 'www':
            subdomain = ''
        host = '.'.join([subdomain, domain, suffix])

        # set scheme to http if not filled
        if scheme is '':
            scheme = 'http'

        # rebuild url
        self.base_url = urlunsplit((scheme, host, '', '', ''))

        self.registered_domain = tldextract.extract(start_url).registered_domain    # TODO: do we need this?
        self.whitelisted_domains = whitelisted_domains
        #self.whitelisted_domains.append(self.registered_domain)
        self.whitelisted_domains.append(host)
        self.baseFolder = mkdtemp('crawler')
        self.create_base_folder(self.baseFolder)

        self.rp = urllib.robotparser.RobotFileParser()
        self.rp.set_url(self.base_url + '/robots.txt')
        self.rp.read()
        if len(self.rp.entries) is 0:
            self.rp.allow_all = True

        self.found_links.add(start_url)

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
            #domain = tldextract.extract(url).registered_domain
            #if domain not in self.whitelisted_domains:
            if parsed_url.hostname not in self.whitelisted_domains:
                print('External domain ignored: %s' % url)
                return

            # ask robots.txt whether we are allowed to fetch url
            if not self.rp.can_fetch(self.AGENT_NAME, parsed_url.path):
                print('Not allowed to fetch %s' % parsed_url.path)
                return

            # ensure we did not already visit it
            if url in self.visited_links:
                print('Ignoring already visited %s' % url)
                return

            print("[" + self.get_time_stamp() + "] Visiting: %s" % url)
            headers = {'User-Agent': self.AGENT_NAME}
            data = None

            req = Request(url, data, headers)
            try:
                opener = build_opener(NoRedirection)
                #file_handle = opener.open(req)
                file_handle = urlopen(req)
            except URLError as e:
                if hasattr(e, 'reason'):
                    print('  We failed to reach a server. Reason: ', e.reason)
                    continue
                elif hasattr(e, 'code'):
                    print('  The server couldn\'t fulfill the request. Error code: ', e.code)
                    continue

            code = file_handle.getcode()
            header = file_handle.info()

            if code in [302, 301]:
                redirection_target = file_handle.headers['Location']
                print("  " + str(code) + " - Redirected! Append target %s to queue" % redirection_target)
                self.found_links.add(redirection_target)
                self.visited_links.add(url)
                continue

            mimetype = file_handle.info().get_content_type()        # TODO: evtl. nur main type (Text verwenden) -> .get_content_maintype()
            if mimetype != self.contentTypeHTML :
                print("  Ignoring Document due to wrong MimeType %s" % mimetype)
                continue

            #if file_handle.geturl() is not url:
            #    print("  Redirected to %s" % file_handle.geturl())
            #    url = file_handle.geturl()

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

            linktitle = link.string
            new_url = link['href']
            scheme, host, path, query, fragment = urlsplit(new_url)
            parsed_url = urlparse(new_url)
            #h = parsed_url.hostname
            domain = tldextract.extract(new_url)
            location = parsed_url.netloc
            # basic filtering
            if len(new_url) is 0:
                print('      Ignoring empty link')
            elif new_url[0] == '#':
                print('      Ignoring hash link %s' % new_url)
            elif scheme not in [None, '', 'http', 'https']:
                print('      Ignoring non http(s) links %s' % new_url)
            elif not self.rp.can_fetch(self.AGENT_NAME, path):
                print('      Ignoring (link not allowed to crawl) %s' % new_url)
            elif new_url.endswith(self.exclude_extensions):
                print('      Ignoring due to file extension: %s' % new_url)

            else:
                # transform to absolute link and discard fragments (# anchors)
                if host is '' :
                    host = parsed_url.hostname
                if scheme is '':
                    scheme = parsed_url.scheme
                fragment = ''
                new_url = urlunsplit((scheme, host, path, query, fragment))

                # advanced filtering

                if host is not '' and host not in self.whitelisted_domains:
                    print('      Ignoring links to external domain %s' % host)
                elif new_url in self.visited_links:  #
                    print('      Ignoring already visited %s' % new_url)
                elif new_url in self.found_links:
                    print('      Ignoring, because already queued: %s' % new_url)


                else:       # save new (absolute) link in queue
                    print("      Found new URL:", new_url)
                    self.found_links.add(new_url)


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
