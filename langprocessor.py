import hunspell
import re
import nltk
import pickle
import math


class LangProcessor:
    #abbrevs = {}
    ausschlusstags = []
    spellchecker = None
    lemmata_mapping = {}
    spellchecker_enc = 'UTF-8'
    stopwords = []

    def __init__(self, abbrevfile='abbreviations.txt', stopwords_file='stoppwortliste.txt'):
        #self.load_abbrevs(abbrevfile)

        self.ausschlusstags = ['$.', 'CARD', '$,', '$(', 'ITJ'] # see http://www.ims.uni-stuttgart.de/forschung/ressourcen/lexika/TagSets/stts-table.html

        self.spellchecker = hunspell.HunSpell('/usr/share/hunspell/de_DE.dic',
                                              '/usr/share/hunspell/de_DE.aff')
        self.spellchecker_enc = self.spellchecker.get_dic_encoding()

        self.load_lemmata()

        self.load_stopwords(stopwords_file)

    def get_index(self, text, docid):
        doc_index = []

        sents = self.split_sents(text)

        for sent in sents:
            sent = self.remove_hyphens(sent)
            tokens = self.split_tokens(sent)
            postags = self.do_pos_tagging(tokens)

            # Bindestrich-Substantive behandeln (Chunking)
            self.find_compound_nouns(postags, tokens)

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
                    corrwort = self.correct_typo(wort)
                    # wenn Korrektur mehr als 1 Wort ergibt: in Postag-Liste einfügen und einzeln verarbeiten
                    if len(corrwort.split(' ')) > 1:
                        npostags = self.do_pos_tagging(corrwort.split(' '))
                        for i, newpostag in enumerate(npostags):
                            position = ind + i + 1
                            postags.insert(position, newpostag)
                        continue

                    # Lemmatisieren
                    lemma = self.find_lemma(corrwort)

                # Normalisieren (Kleinschreibung)
                token = lemma.casefold()

                # Indexliste aufbauen
                doc_index.append((token, docid))

        return doc_index

    @staticmethod
    def invert_index(col_index):
        inv_ind = {}

        # index.sort()
        #
        # for token, docid in index:
        #     if token == term:
        #         docfreq += 1
        #         pl.append(docid)
        #     else:
        #         if term != '':
        #             #inv_ind[(term, docfreq)] = set(pl)
        #             inv_ind[term] = (docfreq, set(pl))
        #         term = token
        #         docfreq = 1
        #         pl = [docid]

        for token, docid in col_index:
            if token in inv_ind:
                colfreq, pl = inv_ind[token]
                colfreq += 1
                pl.add(docid)
                inv_ind[token] = (colfreq, pl)
            else:
                inv_ind[token] = (1, {docid})

        return inv_ind


    def get_inverse_index(self, docs):
        indexlist = []

        for doc_id in docs.keys():
            url, doc = docs[doc_id]
            indexlist += self.get_index(doc, doc_id)

        #indexlist2 = [self.get_index(doc, doc_id) for doc_id, (url, doc) in zip(docs.keys(), docs.values())]

        inverse_index = self.invert_index(indexlist)
        return inverse_index

    ##################################### Hilfsmethoden ##################################


    #/def remove_abbrev(self, t):
    #    for abbrev in self.abbrevs:
    #        t = t.replace(abbrev, self.abbrevs[abbrev])
    #    return t

    # def load_abbrevs(self, abbrev_file):
    #     try:
    #         with open(abbrev_file) as f:
    #             for line in f:
    #                 parts = line.split(';')
    #                 if len(parts) == 2:
    #                     a, w = parts[0], parts[1]
    #                     self.abbrevs[a] = w.strip()
    #     except FileNotFoundError:
    #         print("No Abbreviations found.")


    @staticmethod
    def remove_hyphens(t):

        # Entferne unvollständige Kompositionsteile (inkl. 'und')
        text = re.sub(r"\w+-([.,]|\sund\s)", '', t)  # vorn (An- und Abreise)
        text = re.sub(r"(\sund\s|,\s)-\w+", '', text)  # hinten (Spielspaß und -freude)

        # Entferne Bindestriche in hart codierten Worttrennungen
        text = re.sub(r"-[\n\r]+", '', text)

        # übrig bleiben Bindestriche im Wort und Gedankenstriche -> durch Leerzeichen ersetzen
        text = text.replace('-', ' ')

        return text


    @staticmethod
    def split_sents(text):

        sent_tokenizer = nltk.data.load('tokenizers/punkt/german.pickle')
        sents = sent_tokenizer.tokenize(text)

        return sents


    @staticmethod
    def split_tokens(text):
        tokens = nltk.word_tokenize(text)
        return tokens


    @staticmethod
    def do_pos_tagging(tokens):
        with open('pickle/nltk_german_classifier_data_tiger.pickle', 'rb') as f:
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


    def load_lemmata(self, loadnew=False):
        if loadnew:
            try:
                self.lemmata_mapping = self.read_lemmata_from_tiger_corpus('corpora/part_A.conll', 10)
                self.lemmata_mapping.update(self.read_lemmata_from_tiger_corpus('corpora/part_B.conll', 10))
                self.lemmata_mapping.update(self.read_lemmata_from_tiger_corpus('corpora/part_C.conll', 10))
                self.lemmata_mapping.update(
                    self.read_lemmata_from_tiger_corpus('corpora/tiger_release_aug07.corr.16012013.conll09'))

                with open('pickle/lemmata_mapping.pickle', 'wb') as f:
                    pickle.dump(self.lemmata_mapping, f, protocol=2)
            except:
                print("Lemmatas could not be loaded.")

        else:
            with open('pickle/lemmata_mapping.pickle', 'rb') as f:
                self.lemmata_mapping = pickle.load(f)


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

        # fallback
        # if not neu_w:
        #    neu_w = w

        return neu_w

    def load_stopwords(self, stopwords_file):
        try:
            with open(stopwords_file) as f:
                for line in f:
                    if line is not '':
                        # print(line)
                        self.stopwords.append(line.strip().casefold())
                        # print(stopwords)
        except:
            print("Stopword List could not be loaded.")

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