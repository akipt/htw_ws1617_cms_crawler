# coding: utf8
import pickle
from tokenlist import TokenList
from langprocessor import LangProcessor
from itertools import groupby
import json
from math import log
import locale


class Indexer:
    @staticmethod
    def get_inverse_index(doc_col):
        '''
        Calculates the inverse index of a collection from all token lists (indexliste of each document).
        For each Token the absolute cf (collection frequency) is given and
        for each token/document the normalized tf (term frequency) is given
        :param doc_col: dictionary of documents {docid:Documentobject}
        :return: dictionary containing the inverse index {token: (cf, {docid: tf})}
        '''
        inv_index = {}

        for doc_id in doc_col.keys():
            print('\tIndiziere ' + doc_id)
            doc = doc_col[doc_id]
            if len(doc.indexliste) == 0:
                doc.indexliste, doc.wordlemmadict = l.get_index(doc.text)
            if len(doc.index) == 0:
                doc.index = {k: doc.indexliste.count(k) for k, g in groupby(sorted(doc.indexliste))}
            # termnum = sum(doc.index.values())
            termnum = len(doc.indexliste)
            maxtf = max(doc.index.values())
            for token in doc.index:
                abs_tf = doc.index[token]  # absolute termfrequenz in collection
                rel_tf = abs_tf / termnum  # relative termfrequenz
                norm_tf = abs_tf / maxtf  # normalisierte termfrequenz
                if token in inv_index:
                    colfreq, pl = inv_index[token]
                else:
                    colfreq = 0
                    pl = {}
                colfreq += abs_tf
                pl[doc_id] = norm_tf
                inv_index[token] = (colfreq, pl)

        return inv_index

    @staticmethod
    def get_inverse_posindex(doc_col):
        '''
        Calculates the inverse index with positions of a collection from all token lists (indexliste of each document).
        For each Token the absolute cf (collection frequency) and
        for each token/document the relative tf (term frequency) is given
        :param doc_col: dictionary of documents {docid:Documentobject}
        :return: dictionary containing the inverse index {token: (cf, {docid: (tf, [positions])})}
        '''
        inv_posindex = {}

        for doc_id in doc_col.keys():
            doc = doc_col[doc_id]
            if len(doc.indexliste) == 0:
                doc.indexliste, doc.wordlemmadict = l.get_index(doc.text)
            # if len(doc.index) == 0:
            #    doc.index = {key: doc.indexliste.count(key) for key, g in groupby(sorted(doc.indexliste))}
            if len(doc.posindex) == 0:
                posliste = [(k, i) for i, k in enumerate(doc.indexliste)]
                posliste = sorted(posliste)
                doc.posindex = {k: [i for t, i in g] for k, g in groupby(posliste, lambda x: x[0])}

            # termnum = sum(len(val) for val in doc.posindex.values())
            termnum = len(doc.indexliste)
            maxtf = max([len(v) for v in doc.posindex.values()])
            for token in doc.posindex:
                abs_tf = len(doc.posindex[token])  # absolute termfrequenz in collection
                rel_tf = abs_tf / termnum  # relative termfrequenz
                norm_tf = abs_tf / maxtf  # normalisierte termfrequenz

                if token in inv_posindex:
                    colfreq, postinglist = inv_posindex[token]
                else:
                    colfreq = 0
                    pl = {}
                colfreq += abs_tf
                positions = doc.posindex[token]
                pl[doc_id] = (norm_tf, positions)
                inv_posindex[token] = (colfreq, pl)

        return inv_posindex

    @staticmethod
    def get_lemma_mapping(doc_col):
        '''
        Retrieves the word-lemma mappings of each document, merges them and writes them into a csv file (sorted alphabetically)
        :param doc_col: dictionary of documents {docid:Documentobject}
        :return: dictionary with word-lemma mapping for all documents
        '''
        mappingdict = {}
        for doc_id in doc_col.keys():
            doc = doc_col[doc_id]
            if len(doc.wordlemmadict) == 0 or len(doc.indexliste) == 0:
                doc.indexliste, doc.wordlemmadict = l.get_index(doc.text)

            gesdict_set = set(mappingdict)
            docdict_set = set(doc.wordlemmadict)
            for k in gesdict_set.intersection(docdict_set):
                if mappingdict[k] != doc.wordlemmadict[k]:
                    v1 = mappingdict[k]
                    v2 = doc.wordlemmadict[k]
                    raise ValueError('Error: Different lemmata assigned to ' + k + ' (' + v1 + ', ' + v2 + ')')
            mappingdict.update((k, v) for (k, v) in doc.wordlemmadict.items() if v)

        return mappingdict

    @staticmethod
    def get_inverse_lemma_mapping(doc_col):
        lemma_mapping = Indexer.get_lemma_mapping(doc_col)
        ilm = {}
        for token,lemma in lemma_mapping.items():
            if lemma in ilm:
                ilm[lemma].append(token)
            else:
                ilm[lemma] = [token]
        return ilm


    @staticmethod
    def write_csv(doc_col, inv_index, csv_file="out/out_neu.csv"):
        '''
        Writes a csv file with columns
        [token, lemma, collection frequency, tf (doc1), ..., tf (docn), idf, tf-idf (doc1), ..., tf-idf (docn)]
        All numeric values belong to the lemma
        :param doc_col: dictionary of documents {docid:Documentobject}
        :param inv_index: dictionary containing the inverted index
        :param csv_file: path to csv file
        :return: String with all the data written to file
        '''
        # set to German locale:
        locale.setlocale(locale.LC_NUMERIC, "de_DE.UTF-8")
        docnum = len(doc_col.keys())
        inverse_lemma_mapping = Indexer.get_inverse_lemma_mapping(doc_col)
        zeilen = []
        ii = [(token, cf,pl) for token, (cf,pl) in inv_index.items()]
        ii = sorted(ii, key=lambda el: (-el[1], el[0]))

        fobj_out = open(csv_file, "w")
        tf_heading = ''
        tfidf_heading = ''
        for doc_id in sorted(doc_col.keys()):
            tf_heading += ';TF ' + doc_id
            tfidf_heading += ';TF-IDF ' + doc_id
        fobj_out.write('TOKEN;LEMMA;Collection Frequency' + tf_heading + ';IDF' + tfidf_heading + '\n')

        for token, cf, pl in ii:    # sortiert nach cf
            originalwords = inverse_lemma_mapping[token]
            for w in originalwords:
                zeile = w
                zeile += ';' + token
                zeile += ';' + locale.str(cf)
                df = len(pl)
                idf = log(docnum / df)
                tf_zeile = tfidf_zeile = ''
                for doc_id in sorted(doc_col.keys()):
                    if doc_id in pl:
                        ntf = pl[doc_id]
                    else:
                        ntf = 0
                    tf_zeile += ';' + locale.str(ntf)
                    tf_idf = ntf * idf
                    tfidf_zeile += ';' + locale.str(tf_idf)
                zeile += tf_zeile + ';' + locale.str(idf) + tfidf_zeile
                zeilen.append(zeile)
                fobj_out.write(zeile + '\n')

        fobj_out.close()
        return zeilen


if __name__ == "__main__":
    l = LangProcessor()
    with open('helpers/docs.pickle', 'rb') as d:
        docs = pickle.load(d)

    '''ind = 0
    tmp = {}
    for key, val in sorted(docs.items()):
        tmp[key] = val
        ind += 1
        if ind >= 3:
            break
    docs = tmp'''

    print("Starte Indizierung...")

    inv_ind = Indexer.get_inverse_index(docs)
    inv_posind = Indexer.get_inverse_posindex(docs)

    print("\n Schreibe Invertierten Index in Datei...")
    with open('helpers/invertierter_index.pickle', 'wb') as invf:
        pickle.dump(inv_ind, invf, protocol=2)
    with open('helpers/invertierter_posindex.pickle', 'wb') as invpf:
        pickle.dump(inv_posind, invpf, protocol=2)

    # Todo: Export des inv. Positionsindexes als JSON
    r = json.dumps(inv_posind, indent=4)  # json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}])
    # '["foo", {"bar": ["baz", null, 1.0, 2]}]'
    file_out = open("out/inv_posindex.json", "w")
    file_out.write(str(r))
    file_out.close()

    '''print ("Calculating absolute and normalized TF")
    for document in docs.values():
        document.calc_term_frequencies()
    print ("Done")

    # Todo: Hier erfolgt der Aufruf von TokenList und der Export der CSV-Datei
    Indexer.write_lemma_csv(docs, "out/word_lemma_mapping.csv")
    print ("Calculating IDFs and TF-IDFs and preparing CSV export")
    my_token_list = TokenList(docs)'''

    print("\nCSV Export...")
    Indexer.write_csv(docs, inv_ind)
    print("\tFertig.")
