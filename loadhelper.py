import pickle

def load_abbrevs(abbrev_file):
    '''
    Loads a semicolon-separated text file containing abbreviations and their translations
    :param abbrev_file: path to text file
    :return: dictionary {abbreviation:translation}
    '''
    ab = {}
    try:
        with open(abbrev_file) as f:
            for line in f:
                parts = line.split(';')
                if len(parts) == 2:
                    a, w = parts[0], parts[1]
                    ab[a] = w.strip()
    except FileNotFoundError:
        print("No Abbreviations found.")

    return ab

def read_lemmata_from_conll_corpus(tiger_corpus_file, valid_cols_n=15, col_words=1, col_lemmata=2):
    '''
    Reads lemmata from conll file
    :param tiger_corpus_file: path to conll file
    :param valid_cols_n: number of cols in file (conll09:15)
    :param col_words: column containg the tokens
    :param col_lemmata: column containing the lemmata
    :return: dictionary {token:lemma}
    '''
    lemmata_mapping = {}

    with open(tiger_corpus_file) as f:
        for line in f:
            parts = line.split()
            if len(parts) == valid_cols_n:
                w, lemma = parts[col_words], parts[col_lemmata]
                if w != lemma and w not in lemmata_mapping and not lemma.startswith('--'):
                    lemmata_mapping[w] = lemma

    return lemmata_mapping

def load_lemmata(loadnew=False, customfile='helpers/custom_lemmata.txt'):
    '''
    Constructs a dictionary with tokens and their lemmata from various sources (different corpora containing lemma information)
    :param loadnew: True, if lemmata should be read from corpora; False if lemmata are read from pickle (in case
    the corpora are not available); defaults to False
    :param customfile: path to text file with custom lemmata mappings
    :return: dictionary {token:lemma}
    '''
    lm = {}
    if loadnew:
        try:
            lm = read_lemmata_from_conll_corpus('corpora/part_A.conll', 10)
            lm.update(read_lemmata_from_conll_corpus('corpora/part_B.conll', 10))
            lm.update(read_lemmata_from_conll_corpus('corpora/part_C.conll', 10))
            lm = {k: v for k, v in lm.items() if v != 'unknown'}
            lm = {k: v for k, v in lm.items() if v != '-'}

            # self.lemmata_mapping.update(self.read_lemmata_from_tiger_corpus('corpora/tiger_release_aug07.corr.16012013.conll09'))
            tigerlm = read_lemmata_from_conll_corpus('corpora/tiger_release_aug07.corr.16012013.conll09')
            tigerlm = {k: v for k, v in tigerlm.items() if v != '-'}
            lm.update((k, v) for (k, v) in tigerlm.items() if v)

            clm = {}
            try:
                with open(customfile) as f:
                    for line in f:
                        parts = line.split(';')
                        if len(parts) == 2:
                            a, w = parts[0], parts[1]
                            clm[a] = w.strip()
                lm.update(clm)
            except FileNotFoundError:
                print("Custom Lemmata could not be loaded.")

            with open('helpers/lemmata_mapping.pickle', 'wb') as f:
                pickle.dump(lm, f, protocol=2)
        except:
            print("Lemmata could not be loaded.")

    else:
        with open('helpers/lemmata_mapping.pickle', 'rb') as f:
            lm = pickle.load(f)

    return lm

def load_stopwords(stopwords_file):
    '''
    Loads a text file containing stop words (one per line)
    :param stopwords_file: path to text file
    :return: list of stop words
    '''
    sw = []
    try:
        with open(stopwords_file) as sf:
            for line in sf:
                if line is not '':
                    sw.append(line.strip().casefold())

    except:
        print("Stopword List could not be loaded.")

    return sw
