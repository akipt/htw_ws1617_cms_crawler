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
    # Inhalt des HTML-Titletags (head title)
    soup = BeautifulSoup(html, 'lxml')
    final_title = soup.title.text

    return final_title


'''def get_encoding(html):
    soup = BeautifulSoup(html, 'html.parser')

    encod = soup.meta.get('charset')
    if encod == None:
        encod = soup.meta.get('content-type')
        if encod == None:
            content = soup.meta.get('content')
            match = re.search('charset=(.*)', content)
            if match:
                encod = match.group(1)
            else:
                raise ValueError('unable to find encoding')
    return encod'''
