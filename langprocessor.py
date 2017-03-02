import hunspell
import re
import nltk
import pickle
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters
from nltk.tokenize import RegexpTokenizer
import loadhelper


class LangProcessor:
    abbrevs = {}
    ausschlusstags = []
    spellchecker = None
    lemmata_mapping = {}
    spellchecker_enc = 'UTF-8'
    stopwords = []

    def __init__(self, abbrevfile='helpers/abbreviations.txt', stopwords_file='helpers/stoppwortliste.txt'):
        self.abbrevs = loadhelper.load_abbrevs(abbrevfile)

        # see http://www.ims.uni-stuttgart.de/forschung/ressourcen/lexika/TagSets/stts-table.html
        self.ausschlusstags = ['$.', 'CARD', '$,', '$(', 'ITJ']

        self.spellchecker = hunspell.HunSpell('/usr/share/hunspell/de_DE.dic',
                                              '/usr/share/hunspell/de_DE.aff')
        self.spellchecker_enc = self.spellchecker.get_dic_encoding()

        self.lemmata_mapping = loadhelper.load_lemmata()

        self.stopwords = loadhelper.load_stopwords(stopwords_file)

    def get_index(self, text, write_csv=True, csvfile='out/word_lemma_mapping.csv'):
        doc_index = []
        text = self.remove_abbrev(text)
        if write_csv:
            fobj_out = open(csvfile, "a")

        sents = self.split_sents(text, self.abbrevs)

        for sent in sents:
            sent = self.remove_hyphens(sent)
            tokens = self.split_tokens(sent)

            if len(tokens) == 0:
                continue
            postags = self.do_pos_tagging(tokens)

            # Bindestrich-Substantive behandeln (Chunking)
            #self.find_compound_nouns(postags, tokens)

            # zusammengesetzte Verben suchen (Chunking)
            self.find_compound_verbs(postags, tokens)

            # ab hier wortweise...
            for ind, (wort, pos) in enumerate(postags):

                # Satzzeichen und Zahlen entfernen
                if pos in self.ausschlusstags or len(wort) == 1:
                    continue

                # Namen werden nicht geprüft
                if pos == 'NE':
                    lemma = wort

                # alle anderen Wörter verarbeiten
                else:
                    # Stoppwörter entfernen
                    if wort.casefold() in self.stopwords:
                        continue

                    # Tippfehler korrigieren
                    '''corrwort = self.correct_typo(wort)
                    # wenn Korrektur mehr als 1 Wort ergibt: in Postag-Liste einfügen und einzeln verarbeiten
                    if len(corrwort.split(' ')) > 1:
                        npostags = self.do_pos_tagging(corrwort.split(' '))
                        for i, newpostag in enumerate(npostags):
                            position = ind + i + 1
                            postags.insert(position, newpostag)
                        continue

                    # Lemmatisieren
                    lemma = self.find_lemma(corrwort)'''
                    lemma = self.find_lemma(wort)

                # Normalisieren (Kleinschreibung)
                token = lemma.casefold()
                #print(wort.ljust(20) + '\t' + token)
                if write_csv:
                    # noinspection PyUnboundLocalVariable
                    fobj_out.write(wort + '\t' + token + '\n')

                # Indexliste aufbauen
                doc_index.append(token)
        if write_csv:
            fobj_out.close()
        return doc_index

    ##################################### Hilfsmethoden ##################################


    def remove_abbrev(self, t):
        for abbrev in self.abbrevs:
            t = t.replace(' ' + abbrev.casefold() + ' ', ' ' + self.abbrevs[abbrev].casefold() + ' ')

        return t

    @staticmethod
    def remove_hyphens(t):
        # Testdatei: Startseite, Satz 7

        # Entferne doppelte Bindestriche
        text = re.sub(r"[-–­]{2}", '-', t)

        # Entferne unvollständige Kompositionsteile (inkl. 'und')
        text = re.sub(r"\w+[-–­]([.,]|\sund\s)", '', text)  # vorn (An- und Abreise)
        text = re.sub(r"(\sund\s|,\s)[-–­]\w+", '', text)  # hinten (Spielspaß und -freude)

        # Entferne Bindestriche in hart codierten Worttrennungen
        text = re.sub(r"[-–­][\n\r]+", '', text)
        # text = re.sub(r"[-–]\s[\n\r]+", '', text)
        text = re.sub(r"[-–­]\s[\n\r]*", '', text)  # id 11: Begriffs- klassifikation, ersetzt auch Gedankenstriche

        # übrig bleiben Gedankenstriche -> durch Leerzeichen ersetzen
        text = re.sub(r"\s[-–]\s", ' ', text)

        # Bindestriche im Wort entfernen
            # zusammengesetzte Nomen einzeln und zusammen speichern
        text = re.sub(r"([A-ZÄÖÜ][a-zäöüß]*)[-–\xad]([A-ZÄÖÜ][a-zäöüß]*)", '\g<1> \g<2> \g<1>\g<2>',text)
            # alle anderen Bindestriche in Worten
        text = re.sub(r"(\w*)[-–\xad](\w*)", '\g<1>\g<2>', text)

        return text

    @staticmethod
    def split_sents(text, abbrevs):

        # sent_tokenizer = nltk.data.load('tokenizers/punkt/german.pickle')
        # sents = sent_tokenizer.tokenize(text)

        punkt_param = PunktParameters()
        abbreviation = list(abbrevs.keys())
        punkt_param.abbrev_types = set(abbreviation)
        tokenizer = PunktSentenceTokenizer(punkt_param)
        sents = tokenizer.tokenize(text)

        return sents

    @staticmethod
    def split_tokens(text):
        # tokens = nltk.word_tokenize(t)

        expr = r'''[A-Za-zÄÖÜäöü][a-zäöüß[A-ZÄÖÜa-zäöüß|-|–|/|\.|\'’]*[A-ZÄÖÜa-zäöüß]'''
        tokenizer = RegexpTokenizer(expr)
        tokens = tokenizer.tokenize(text)

        return tokens

    @staticmethod
    def do_pos_tagging(tokens):
        with open('helpers/nltk_german_classifier_data_tiger.pickle', 'rb') as f:
            tagger = pickle.load(f)

        # tag tokens
        postags = tagger.tag(tokens)
        return postags

    def find_compound_verbs(self, postags, words):
        grammar = r"""
                CV:
                    {<V.*><.*><PTKVZ>}  # korrekt getaggt
                    {<V.*><ART|PIAT>?<PTKA>?<ADJA>?<NN><APPR>} # Workaround 1a
                    {<V.*><ART|PIAT>?<CARD|PIDAT|PROAV>?<NN><APPR>} # Workaround 1b
                    {<V.*><NE|PPER><APPR>} # Workaround 2
                    {<V.*><ADV>?<APPR>} # Workaround 3
                    """
        cpv = nltk.RegexpParser(grammar)

        tree = cpv.parse(postags)
        for subtree in tree.subtrees():
            ind = 0

            if subtree.label() == 'CV':
                appr, verb, apprpos, verbpos = '', '', '', ''
                for word, pos in subtree:
                    if pos == 'PTKVZ':
                        appr = word
                        apprpos = pos
                    elif pos == 'APPR':
                        appr = word
                        apprpos = pos
                    elif pos[0] == 'V':
                        verb = word
                        ind = words.index(word)
                        verbpos = pos

                neuverb = appr + verb
                if self.spellchecker:
                    corrspell = self.spellchecker.spell(neuverb)
                    if corrspell:
                        words[ind] = neuverb
                        postags[ind] = (neuverb, verbpos)
                        words.remove(appr)
                        postags.remove((appr, apprpos))


    def find_lemma(self, w):
        w_lemma = None

        # 1st try: read lemma from mapping
        if self.lemmata_mapping:
            w_lemma = self.lemmata_mapping.get(w, None)

        # 2nd try: Stemming
        if not w_lemma:
            if self.spellchecker:
                lemmata_hunspell = self.spellchecker.stem(w)
                if lemmata_hunspell:
                    w_lemma = lemmata_hunspell[-1].decode(self.spellchecker_enc)

        # fallback: use original word
        if not w_lemma:
            w_lemma = w

        return w_lemma

    def correct_typo(self, w):
        neu_w = w

        if self.spellchecker:
            corrspell = self.spellchecker.spell(w)

            if not corrspell:
                suggestions = self.spellchecker.suggest(w)
                if len(suggestions) > 0:
                    neu_w = suggestions[0].decode(self.spellchecker_enc)

        return neu_w

    def find_compound_nouns(self, postags, tokens):
        zus = ''
        removelist = []
        grammar = r"""
                        NP:
                            {<NN|NE><NN|NE>+} # Normal
                            {<NN|NE><PPER><NN|NE>*} # Deppen-Apostroph
                            """
        cpv = nltk.RegexpParser(grammar)

        tree = cpv.parse(postags)
        for subtree in tree.subtrees():

            if subtree.label() == 'NP':
                for word, pos in subtree:
                    if pos == 'NN' or pos == 'NE':  # NE nur, weil oft nicht richtig getaggt wird
                        if zus == '':
                            zus = word
                            ind = tokens.index(word)
                        else:
                            zus += word.lower()
                            removelist.append((word, pos))
                    elif word == '\'s':
                        zus += 's'
                        removelist.append((word, pos))

                if self.spellchecker:
                    corrspell = self.spellchecker.spell(zus)
                    if corrspell:
                        tokens[ind] = zus
                        postags[ind] = (zus, 'NN')

                        for w, p in removelist:
                            tokens.remove(w)
                            postags.remove((w, p))

        return postags
