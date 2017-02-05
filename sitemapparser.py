"""
Inspired by Craig Addyman (http://www.craigaddyman.com/parse-an-xml-sitemap-with-python/)
Inspired by Viktor Petersson (http://viktorpetersson.com) / @vpetersson
"""

from bs4 import BeautifulSoup
import requests

class SitemapParser():
    sitemapxml = ''
    links = []

    def __init__(self, url='https://www.cloudsigma.com/sitemap.xml'):
        self.url = url
        get_url = requests.get(url)

        if get_url.status_code == 200:
            self.sitemapxml = get_url.text
            self.parse_sitemap()

    def process_sitemap(self):
        soup = BeautifulSoup(self.sitemapxml, 'lxml')
        result = []

        for loc in soup.findAll('loc'):
            result.append(loc.text)

        return result

    def is_sub_sitemap(self, s):
        if s.endswith('.xml') and 'sitemap' in s:
            return True
        else:
            return False

    def parse_sitemap(self):
        sitemapcandidates = self.process_sitemap()

        while sitemapcandidates:
            candidate = sitemapcandidates.pop()

            if self.is_sub_sitemap(candidate):
                sub_sitemap = self.get_sitemap(candidate)
                for i in self.process_sitemap(sub_sitemap):
                    sitemapcandidates.append(i)
            else:
                self.links.append(candidate)
        return
