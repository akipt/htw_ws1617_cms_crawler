from textextractor import TextExtractor
from bs4 import BeautifulSoup


def get_souped_text(html):

    final_text = ''
    soup = BeautifulSoup(html, 'html.parser')

    # Inhalt des HTML-Titletags (head title)
    # final_text += TextExtractor.extract_title(html) + ". "

    # header1 (body header h1 class="csc-firstHeader")
    # kann mehrfach auftreten (z.B. unter Publikationen - Vorabdrucke)
    for tag in soup.find_all('h1', 'csc-firstHeader'):
        if tag.text:
            final_text += tag.text + ". "

    # header2 (body header p mitclass="csc-subheader")
    # laut css könnte es mehrere geben, bisher aber immer nur einen Absatz gefunden
    for tag in soup.find_all('p', 'csc-subheader'):
        if tag.text:
            final_text += tag.text + ". "

    # article (body article p class="bodytext")
    # aside (body article p class="bodytext")
    for tag in soup.find_all('p', 'bodytext'):
        if tag.text:
            final_text += tag.text + ". "

    return final_text


def get_souped_title(html):
    final_title = ''

    # Inhalt des HTML-Titletags (head title)
    final_title += TextExtractor.extract_title(html)

    return final_title
