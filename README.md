# htw_ws1617_cms_crawler
Python crawler für WT Content Management, Such- und Texttechnologien (SL) - 1163121

Voraussetzungen / verwendete Pakete:
------------------------------------
	- urllib2
	- hunspell und pyhunspell mit deutschen Wörterbüchern
	- pickle
	- itertools
	- re
	- nltk mit tokenizers/punkt/german.pickle
	- tldextract
	- bs4
	- pythonds
	- functools

Der Code befindet sich auf Github: https://github.com/akipt/htw_ws1617_cms_crawler

Die Software besteht aus 4 Teilen:
	crawler.py - Crawler und Text Extractor
	indexer.py - Language Processing und Indexing
	search.py - Suche
	Search.ipynb - Such-Frontend (Jupyter Notebook)

Crawling
--------

	- crawler.py ist eigenständiges Skript, Aufruf: python3 crawler.py -s <Seed> -w <whitelisted_domains>	(beide Flags sind optional)
	- AGENT_NAME = 'CMSST4 Crawler'
	- startet standardmäßig mit seed 'http://www.datenlabor-berlin.de', andere sind möglich (Flag -s)
	- Vorgehensweise Crawler:
		- solange url in Queue ist:
			- absolute URL ermitteln
			- check ob Domain der URL in Whitelist (externe werden gefiltert)
			- check ob URL gecrawled werden darf (Suche ggf. nach robots.txt)
			- check ob URL bereits besucht
			- hole Datei (Politeness: nur alle 2 Sekunden eine Seite abfragen!)
			- werte Returncode aus 
				- 204: nächsten crawlen (Leere Seite)
				- bei 3xx: neue URL in Queue einfügen und nächsten crawlen
				- 4xx - 5xx: nächsten crawlen
				- sonst: ok
			- checke Mime Type (nur text/html erlaubt, alles andere wird gefiltert)
			- speichere temporäre Kopie der Datei
			- suche nach Links in Datei
				- alle a-Tags
				- ignoriere leere und #-Links
				- nur http und https
				- ignoriere, wenn Dateiendung in Blacklist (Bilder, PDF, ...)
				- absolute URL ermitteln
				- ignoriere externe Domains
				- ignoriere, wenn Crawlen nicht erlaubt (robots.txt)
				- ignoriere bereits besuchte Seiten
			- füge Links zu Queue hinzu
	- schreibt Log mit Datum/Uhrzeit, gecrawlter Seite und Dateinamen der lokalen Kopie

	- Text-Extraktion: 
		- ruft souper.py auf
		- extrahiere Text mit Beautiful Soup
			- nur <p class="bodytext">, <h1 class="csc-firstheader"> und <p class="csc-subheader"> (weil nur die auf Typo3-Seiten vorkommen)
		- übergebe Dokumente an Indexer (nur Dokumente mit Inhalt)		-> helpers/docs.pickle

Indexer
-------

	- indexer.py ist eigenständiges Skript, Aufruf: python3 indexer.py
	- liest Dokumente aus docs.pickle
	- für jedes Dokument: Language Processing (langprocessor.py)
		- ersetze Abkürzungen
		- Satzzerlegung (benutzt PunktSentenceTokenizer von nltk)
		- Bindestriche entfernen (zusammengesetzte Nomen werden zweimal in Index aufgenommen: einmal einzeln mit Leerzeichen getrennt und einmal zusammengeschrieben ohne Bindestrich)
		- Wortzerlegung (Regex: '[A-Za-zÄÖÜäöü][a-zäöüß[A-ZÄÖÜa-zäöüß|-|–|/|\.|\'’]*[A-ZÄÖÜa-zäöüß]')
		- POS-Tagging
		- finde zusammengesetzte Verben und füge sie zusammen
		- Satzzeichen, Sonderzeichen, Zahlen entfernen (sollten aber schon raus sein)
		- Stoppwörter entfernen
		- Lemmatisieren (Lemmata aus TIGER-Korpus, SMULTRON-Korpus und eigene)
		- Normalisieren: Kleinschreiben
		- Lemmata in Index aufnehmen

	- Invertierten Index und Invertierten Positionsindex erstellen
		- für jedes Token im Index jeden Dokumentes:
			- Position(en) im Dokument ermitteln
			- Häufigkeiten ermitteln (collection frequency, document frequency, term frequency)
				- collection frequency: absolute Häufigkeit des Vorkommens in allen Dokumenten
				- document frequency: Anzahl der Dokumente, in denen das Token vorkommt
				- term frequency: Vorkommen im Dokument -> wir benutzen die normalisierte TF, also Vorkommen / max. Vorkommen
			- in invertierten Index und invertierten Positionsindex aufnehmen
		- Struktur invertierter Index: 			{token: (cf, {docid: tf})}					-> inv_index.json und helpers/inv_index.pickle
		- Struktur invertierter Positionsindex: {token: (cf, {docid: (tf, [positions])})}	-> inv_posindex.json und helpers/inv_posindex.pickle

	- CSV-Datei mit allen Token, ihrem Lemma, der CF, allen TFs, IDF und allen TF-IDFs schreiben	-> out_neu.csv

Suche
-----

	- 3 Suchmodi: Freie Suche/Keywordsuche, Phrasensuche und Suche mit Operatoren
	- search.py ist eigenständiges Skript, Aufruf:
		- python3 search.py Keyword1 Keyword2			<-- Keywordsuche
		- python3 search.py -b "Keyword1 AND Keyword2"	<-- Boolsche Logik
		- python3 search.py -p "Eine Phrase"			<-- Phrasensuche
		- python3 search.py "Keyword1 Keyword2"			<-- Freie Suche
	- liest invertierten Index und invertierten Posindex aus inv_index.pickle und inv_posindex.pickle
	- invertierter Positionsindex wird nur in Phrasensuche verwendet (weil ansonsten der andere reicht und dieser leichter zu traversieren ist)
	- Vorgehensweise:
		- Unterscheidung der Suchmodi anhand der Aufrufparameter
		- Freie Suche:
			- doppelte Suchbegriffe ausfiltern
			- überflüssige Anführungszeichen entfernen
			- Tokenizing / Language Processing (analog Language Processing im Indexer)
			- für jedes Document Score über alle Query Token berechnen (TF-IDF)
			- Ergebnis = Liste alle Dokumente mit Score > 0 (absteigend sortiert nach Score)
		- Suche mit Logischen Operatoren:
			- AND, OR, NOT möglich
			- Logischen Ausdruck in umgekehrte Polnische Notation überführen (Shunting-Yard-Algorithmus in shyard.py)
			- Tokenizing /Language Processing der Suchbegriffe
			- Operationen auf Ergebnismengen
				- OR: UNION
				- AND: INTERSECT
				- NOT: DIFFERENCE
			- Ergebnis = Liste mit allen Dokumenten, auf die logischer Ausdruck zutrifft (sortiert nach Dokumenten-ID)
		- Phrasensuche:
			- Liste der Dokumente ermitteln, in denen alle Suchbegriffe vorkommen
			- für jeden Suchterm Liste mit Positionen pro Dokument ermitteln
			- Filtern: nur Dokumente, in denen die Suchworte an aufeinanderfolgenden Positionen auftauchen
			- Sortieren nach Position
			- Ergebnis = Liste aus Dokumenten, in denen die Phrase vorkommt (Dokumente, in denen die Phrase weit vorn vorkommt, zuerst)

Suchoberfläche
--------------

	- Jupyter Notebook Search.ipynb
	- Aufruf der drei Suchmethoden schon vorgegeben
	- Achtung: Erste Zelle muss zuerst ausgeführt werden, damit Suchmethode im Speicher liegt!
