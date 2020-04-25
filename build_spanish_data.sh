#!/bin/sh

jq --version >/dev/null || echo "jq not found, install it first" && exit
curl --version >/dev/null || echo "curl not found, install it first" && exit
bzcat --version >/dev/null || echo "bzcat not found, install it first" && exit

# download the awk script
curl 'https://en.wiktionary.org/w/api.php?action=query&prop=revisions&rvslots=*&rvprop=content&format=json&&titles=User:Matthias_Buchmeier/trans-en-es.awk' \
  | jq -r '.query.pages | .[] | .revisions[].slots.main."*"' \
  | sed -e "1,/===Code (non-English entries/d" -e '0,/<source lang=awk>/d' -e '/<\/source>/,$d' \
  > trans-en-es.awk

# process the wiktionary dump
curl 'https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles.xml.bz2' \
  | bzcat | gawk -v LANG=Spanish -v ISO=es -v REMOVE_WIKILINKS="y" -f trans-en-es.awk > es-en.txt
sort -s -d -k 1,1 -t"{" -o es-en.txt es-en.txt

# process the pythonol dictionary into a list of synonyms
curl https://github.com/phrozensmoke/LEGACY-Open_Source-Pre2006/raw/master/pythonol/dictionary/data_dict1.txt \
  | iconv -f ISO-8859-1 -t UTF-8 \
  | python3 build_synonyms.py \
  > synonyms.txt

# download the list of irregular verbs
curl https://github.com/phrozensmoke/LEGACY-Open_Source-Pre2006/raw/master/pythonol/datafiles/irregular_verbs.txt \
  | iconv -f ISO-8859-1 -t UTF-8 \
  > irregular_verbs.txt
