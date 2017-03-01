from textextractor import TextExtractor
from bs4 import BeautifulSoup

def get_souped_text(html):
    final_text = ''
    soup = BeautifulSoup(html, 'html.parser')

    #Inhalt des HTML-Titletags (head title)
    final_text += TextExtractor.extract_title(html) + ". "

    #header1 (body header h1 class="csc-firstHeader") - kann mehrfach auftreten (z.B. unter Publikationen - Vorabdrucke)
    for strong_tag in soup.find_all('h1','csc-firstHeader'):
        final_text +=  strong_tag.text + ". "

    #header2 (body header p mitclass="csc-subheader") - laut css könnte es mehrere geben, bisher aber immer nur einen Absatz gefunden
    for strong_tag in soup.find_all('p', 'csc-subheader'):
        final_text += strong_tag.text + ". "

    #article (body article p class="bodytext")
    #aside (body article p class="bodytext")
    for strong_tag in soup.find_all('p', 'bodytext'):
        final_text += strong_tag.text + ". "

    return (final_text)