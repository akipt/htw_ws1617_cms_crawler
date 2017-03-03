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
        '''
        Initialize Object: load all the needed resources
        :param abbrevfile: default path to abbreviations file
        :param stopwords_file: default path to stopwords file
        '''
        self.abbrevs = loadhelper.load_abbrevs(abbrevfile)

        # see http://www.ims.uni-stuttgart.de/forschung/ressourcen/lexika/TagSets/stts-table.html
        self.ausschlusstags = ['$.', 'CARD', '$,', '$(', 'ITJ']

        self.spellchecker = hunspell.HunSpell('/usr/share/hunspell/de_DE.dic',
                                              '/usr/share/hunspell/de_DE.aff')
        self.spellchecker_enc = self.spellchecker.get_dic_encoding()

        self.lemmata_mapping = loadhelper.load_lemmata()

        self.stopwords = loadhelper.load_stopwords(stopwords_file)

    def get_index(self, text):
        '''
        The main NLP method: process a document and construct the token index
        :param text: a text
        :param wordlemmadict: dictionary, in which the mapping word -> lemma will be written
        :return: list of all the tokens of the text (sorted alphabetically) - may contain duplicates
        '''
        doc_index = []
        wordlemmadict = {}
        text = self.remove_abbrev(text, self.abbrevs)

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
                #if pos == 'NE':
                #    lemma = wort

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

                if wort in wordlemmadict:
                    if token != wordlemmadict[wort]:
                        fehler = 'Uneindeutige Lemma-Zuordnung für ' + wort + '('+wordlemmadict[wort]+', '+token+')'
                        raise ValueError(fehler)
                wordlemmadict[wort] = token

                # Indexliste aufbauen
                doc_index.append(token)

        return doc_index, wordlemmadict

    ##################################### Hilfsmethoden ##################################

    @staticmethod
    def remove_abbrev(t, abbrevs):
        '''
        Replace abbreviations in a text with their translations
        :param t: the text (possibly with abbreviations)
        :param abbrevs: dictionary of abbreviations {abbreviation:translation}
        :return: text without abbreviations
        '''
        for abbrev in abbrevs:
            t = t.replace(' ' + abbrev.casefold() + ' ', ' ' + abbrevs[abbrev].casefold() + ' ')

        return t

    @staticmethod
    def remove_hyphens(t):
        '''
        Remove all kinds of hyphens in a text
        :param t: the text
        :return: text without hyphens
        '''
        # Testdatei: Startseite, Satz 7

        # Entferne doppelte Bindestriche
        text = re.sub(r"[-–­]{2}", '-', t)

        # Entferne unvollständige Kompositionsteile (inkl. 'und')
        text = re.sub(r"\w+[-–­]([.,]|\sund\s)", '', text)  # vorn (An- und Abreise)
        text = re.sub(r"(\sund\s|,\s)[-–­]\w+", '', text)  # hinten (Spielspaß und -freude)

        # Entferne Bindestriche in hart codierten Worttrennungen
        text = re.sub(r"[-–­][\n\r]+", '', text)        # TODO: Wort mit aufnehmen (Gruppe)
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
        '''
        Split a text into sentences
        :param text: full text
        :param abbrevs: dictionary of abbreviations {abbreviation:translation}
        :return: list of sentences
        '''
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
        '''
        Split a text or sentence into Tokens and remove everything, that is no word
        The Regex says the following: words should start with a letter and end with a letter. Hyphens, Dots and Slashes in between are allowed
        :param text: full text or sentence (String)
        :return: list of tokens

        '''
        # tokens = nltk.word_tokenize(t)

        expr = r'''[A-Za-zÄÖÜäöü][a-zäöüß[A-ZÄÖÜa-zäöüß|-|–|/|\.|\'’]*[A-ZÄÖÜa-zäöüß]'''
        tokenizer = RegexpTokenizer(expr)
        tokens = tokenizer.tokenize(text)

        return tokens

    @staticmethod
    def do_pos_tagging(tokens):
        '''
        Do Part-of-Speech Tagging. The TIGER corpus is used (tagset STTS)
        :param tokens: list of tokens
        :return: list of tuples [(token, postag)]
        '''
        with open('helpers/nltk_german_classifier_data_tiger.pickle', 'rb') as f:
            tagger = pickle.load(f)

        # tag tokens
        postags = tagger.tag(tokens)
        return postags

    def find_compound_verbs(self, postags, words):
        '''
        find verbs that consist of 2 parts
        :param postags: list of postags
        :param words: list of words
        :return: words- and postag lists are changed
        '''
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
        '''
        Lemmatization of a token: tries to find a lemma by using different dictionaries
        First: try to find token in dictionary built from TIGER and SMULTRON corpora
        Second: try stemming method of hunspell (which uses, in fact, also a dictionary)
        :param w: token (String)
        :return: lemma (String)
        '''
        w_lemma = None

        # 1st try: read lemma from mapping
        if self.lemmata_mapping:
            w_lemma = self.lemmata_mapping.get(w, None)

        # 2nd try: Stemming... well, not really
        '''if not w_lemma:
            if self.spellchecker:
                lemmata_hunspell = self.spellchecker.stem(w)
                if lemmata_hunspell and not isinstance(lemmata_hunspell, str):  # Änderung wegen Problem bei Julius!
                    w_lemma = lemmata_hunspell[-1].decode(self.spellchecker_enc)
        '''

        # fallback: use original word
        if not w_lemma:
            w_lemma = w

        return w_lemma

    def correct_typo(self, w):
        '''
        Try to correct typos by using hunspell's spellchecker
        :param w: token (string)
        :return: corrected token (String) or original if no correction was found or if token is correct
        '''
        neu_w = w

        if self.spellchecker:
            corrspell = self.spellchecker.spell(w)

            if not corrspell:
                suggestions = self.spellchecker.suggest(w)
                if len(suggestions) > 0:
                    neu_w = suggestions[0].decode(self.spellchecker_enc)

        return neu_w

    def find_compound_nouns(self, postags, tokens):
        '''
        Try to reassemble nouns, that are compounds (and were possibly separated during hyphen removal)
        :param postags: list of POS tags
        :param tokens: list of tokens
        :return: list of POS tags (token list is in fact also changed)
        '''
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
