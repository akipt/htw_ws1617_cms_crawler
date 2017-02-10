from bs4 import BeautifulSoup


class TextExtractor(object):
    @classmethod
    def extract_title(cls, html):
        soup = BeautifulSoup(html, 'lxml')
        return soup.title.text

        # soup = BeautifulSoup(page.html)
        # print (soup.article(text=True))
