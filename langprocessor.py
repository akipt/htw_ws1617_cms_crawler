from nltk.tokenize import word_tokenize, sent_tokenize
import nltk
from ClassifierBasedGermanTagger import ClassifierBasedGermanTagger
import pickle
import hunspell
from nltk.corpus import stopwords

class LangProcessor:
    abbrevs = {}
    ausschlusstags = []
    spellchecker = None
    lemmata_mapping = {}
    spellchecker_enc = 'UTF-8'
    stopwords = []

    def __init__(self, abbrevfile='abbreviations.txt', stopwords_file = 'stoppwortliste.txt'):
        self.loadAbbrevs(abbrevfile)

        self.ausschlusstags = ['$.', 'CARD', '$,', '$(']

        self.spellchecker = hunspell.HunSpell('/usr/share/hunspell/de_DE.dic',
                                         '/usr/share/hunspell/de_DE.aff')
        self.spellchecker_enc = self.spellchecker.get_dic_encoding()

        self.loadLemmata()

        self.loadStopwords(stopwords_file)


    def getIndex(self, text, id):
        indexlist = []

        sents = self.splitSents(text)

        for sent in sents:
            sent = self.removeAbbrev(sent)
            tokens = self.splitTokens(sent)
            postags = self.doPosTagging(tokens)
            self.findCompoundVerbs(postags, tokens)
            self.removePunct(postags, tokens)
            #postags = self.doPosTagging(tokens)
            ind = -1

            for p in postags:
                ind+= 1
                #if p[1] in self.ausschlusstags:
                #    continue
                if p[1] == 'NE':
                    lemma = p[0]
                else:
                    wort = p[0]
                    if wort.casefold() in self.stopwords:
                        continue

                    corrwort = self.correct_typo(wort)
                    if len(corrwort.split(' ')) > 1:    # wenn Korrektur mehr als 1 Wort ergibt: in Postag-Liste einfügen und einzeln verarbeiten
                        ntokens = corrwort.split(' ')
                        npostags = self.doPosTagging(ntokens)
                        laenge = len(npostags)
                        for i in range(0, laenge):
                            position = ind + i + 1
                            postags.insert(position, npostags[i])
                        continue

                    lemma = self.find_lemma(corrwort)

                token = lemma.casefold()
                indexlist.append((token, id))

        return indexlist

    def getInverseIndex(self, index):
        index.sort()
        invInd = {}

        term = ''
        docfreq = 1
        pl = []

        for tup in index:
            if tup[0] == term:
                docfreq += 1
                pl.append(tup[1])
            else:
                if term != '':
                    invInd[(term, docfreq)] = set(pl)
                term = tup[0]
                docfreq = 1
                pl = [tup[1]]

        return invInd


    ##################################### Hilfsmethoden ##################################


    def removeAbbrev(self, t):
        text = []
        for abbrev in self.abbrevs:
            t = t.replace(abbrev, self.abbrevs[abbrev])
        #text.append(t)
        return t


    def loadAbbrevs(self, abbrev_file):
        try:
            with open(abbrev_file) as f:
                for line in f:
                    parts = line.split(';')
                    if len(parts) == 2:
                        a, w = parts[0], parts[1]
                        self.abbrevs[a] = w.strip()
        except FileNotFoundError:
            print("No Abbreviations found.")


    def splitSents(self, text):

        sent_tokenizer = nltk.data.load('tokenizers/punkt/german.pickle')
        sents = sent_tokenizer.tokenize(text)

        return sents


    def splitTokens(self, text):
        tokens = nltk.word_tokenize(text)
        return tokens


    def doPosTagging(self, tokens):
        with open('pickle/nltk_german_classifier_data_tiger.pickle', 'rb') as f:
            tagger = pickle.load(f)

        # tag tokens
        postags = tagger.tag(tokens)
        return postags


    def removePunct(self, postags, tokens):
        removelist = []

        for t in postags:
            if t[1] in self.ausschlusstags:
                tokens.remove(t[0])
                removelist.append(t)

        for r in removelist:
            postags.remove(r)


    def findCompoundVerbs(self, postags, words):
        grammar = r"""
                CV:
                    {<VVFIN|VAFIN><ART>?<ADJA|CARD>?<NN><APPR|PTKVZ>} # Rule 1
                    {<VVFIN><NE><APPR|PTKVZ>} # Rule 2
                    {<VVFIN|VAFIN><ADV>?<APPR>} # Rule 3
                    """
        cpv = nltk.RegexpParser(grammar)

        tree = cpv.parse(postags)
        #zus = []
        for subtree in tree.subtrees():

            if subtree.label() == 'CV':
                # print(subtree)
                appr, verb, apprpos, verbpos = '','','',''
                for s in subtree:
                    if s[1] == 'APPR' or s[1] == 'PTKVZ':
                        appr = s[0]
                        apprpos = s[1]
                    elif s[1] == 'VVFIN' or s[1] == 'VAFIN':
                        verb = s[0]
                        ind = words.index(s[0])
                        verbpos = s[1]

                neuverb = appr + verb
                print(neuverb)
                if self.spellchecker:
                    corrspell = self.spellchecker.spell(neuverb)
                    if corrspell:
                        words[ind] = neuverb
                        postags[ind] = (neuverb, verbpos)
                        words.remove(appr)
                        postags.remove((appr, apprpos))



    @staticmethod
    def read_lemmata_from_tiger_corpus(tiger_corpus_file, valid_cols_n=15, col_words=1, col_lemmata=2):
        lemmata_mapping = {}

        with open(tiger_corpus_file) as f:
            for line in f:
                parts = line.split()
                if len(parts) == valid_cols_n:
                    w, lemma = parts[col_words], parts[col_lemmata]
                    if w != lemma and w not in lemmata_mapping and not lemma.startswith('--'):
                        lemmata_mapping[w] = lemma

        return lemmata_mapping


    def loadLemmata(self, loadnew = False):
        if loadnew:
            try:
                self.lemmata_mapping = self.read_lemmata_from_tiger_corpus('corpora/part_A.conll', 10)
                self.lemmata_mapping.update(self.read_lemmata_from_tiger_corpus('corpora/part_B.conll', 10))
                self.lemmata_mapping.update(self.read_lemmata_from_tiger_corpus('corpora/part_C.conll', 10))
                self.lemmata_mapping.update(self.read_lemmata_from_tiger_corpus('corpora/tiger_release_aug07.corr.16012013.conll09'))

                with open('pickle/lemmata_mapping.pickle', 'wb') as f:
                    pickle.dump(self.lemmata_mapping, f, protocol=2)
            except:
                print("Lemmatas could not be loaded.")

        else:
            with open('pickle/lemmata_mapping.pickle', 'rb') as f:
                self.lemmata_mapping = pickle.load(f)


    def find_lemma(self, w):

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

        # fallback
        #if not neu_w:
        #    neu_w = w

        return neu_w

    # überflüssig
    def getLemma(self, w):
        # lemmatize
        w_lemma = self.find_lemma(w)

        # no lemma? look for spelling mistakes
        if not w_lemma:
            w = self.correct_typo(w)
            w_lemma = self.find_lemma(w)

        # fallback
        if not w_lemma:
            w_lemma = w

        return w_lemma


    def loadStopwords(self, stopwords_file):
        try:
            with open(stopwords_file) as f:
                for line in f:
                    if not line is '':
                        # print(line)
                        self.stopwords.append(line.strip().casefold())
            # print(stopwords)
        except:
            print("Stopword List could not be loaded.")


