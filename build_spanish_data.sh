#!/bin/sh

#jq --version >/dev/null || echo "jq not found, install it first" && exit
curl --version >/dev/null || echo "curl not found, install it first" && exit
bzcat --version >/dev/null || echo "bzcat not found, install it first" && exit

[ -d spanish_data ] || mkdir spanish_data

# download the awk script
#curl 'https://en.wiktionary.org/w/api.php?action=query&prop=revisions&rvslots=*&rvprop=content&format=json&&titles=User:Matthias_Buchmeier/trans-en-es.awk' \
#  | jq -r '.query.pages | .[] | .revisions[].slots.main."*"' \
#  | sed -e "1,/===Code (non-English entries/d" -e '0,/<source lang=awk>/d' -e '/<\/source>/,$d' \
#  > trans-en-es.awk

# process the wiktionary dump
curl 'https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles.xml.bz2' \
  | bzcat \
  | gawk -v LANG=Spanish -v ISO=es -v REMOVE_WIKILINKS="y" -v ENABLE_SYN="y" -v ENABLE_META="y" -v DEBUG_META="spanish_data/meta-templates.txt" -f trans-en-es.awk \
  > orig.es-en.txt
  sort -s -d -k 1,1 -t"{" -o orig.es-en.txt orig.es-en.txt
  python3 process_meta.py orig.es-en.txt > spanish_data/es-en.txt


# Build the sentence list
wget https://downloads.tatoeba.org/exports/per_language/spa/spa_sentences_detailed.tsv.bz2
wget https://downloads.tatoeba.org/exports/per_language/eng/eng_sentences_detailed.tsv.bz2
wget https://downloads.tatoeba.org/exports/links.tar.bz2
wget https://downloads.tatoeba.org/exports/user_languages.tar.bz2
wget http://www.manythings.org/anki/spa-eng.zip

unzip spa-eng.zip

bzcat user_languages.tar.bz2 | tail -n +2 |  grep -P "^spa\t5" | cut -f 3 | grep -v '\N' > spa_5.txt
bzcat user_languages.tar.bz2 | tail -n +2 |  grep -P "^spa\t4" | cut -f 3 | grep -v '\N' > spa_4.txt
bzcat user_languages.tar.bz2 | tail -n +2 |  grep -P "^spa\t[1-5]" | cut -f 3 > spa_known.txt

bzcat user_languages.tar.bz2 | tail -n +2 |  grep -P "^eng\t5" | cut -f 3 | grep -v '\N' > eng_5.txt
bzcat user_languages.tar.bz2 | tail -n +2 |  grep -P "^eng\t4" | cut -f 3 | grep -v '\N' > eng_4.txt
bzcat user_languages.tar.bz2 | tail -n +2 |  grep -P "^eng\t[1-5]" | cut -f 3  > eng_known.txt

bzcat spa_sentences_detailed.tsv.bz2 | awk 'BEGIN {FS="\t"} NR==FNR{A[$1];next}($4 in A){print $1 "\t" $3 "\t" $4 "\t50" }' spa_5.txt - > spa_sentences.tsv
bzcat spa_sentences_detailed.tsv.bz2 | awk 'BEGIN {FS="\t"} NR==FNR{A[$1];next}($4 in A){print $1 "\t" $3 "\t" $4 "\t40" }' spa_4.txt - >> spa_sentences.tsv
bzcat spa_sentences_detailed.tsv.bz2 | awk 'BEGIN {FS="\t"} NR==FNR{A[$1];next}!($4 in A){print $1 "\t" $3 "\t" $4 "\t0" }' spa_known.txt - >> spa_sentences.tsv

bzcat eng_sentences_detailed.tsv.bz2 | awk 'BEGIN {FS="\t"} NR==FNR{A[$1];next}($4 in A){print $1 "\t" $3 "\t" $4 "\t5" }' eng_5.txt - > eng_sentences.tsv
bzcat eng_sentences_detailed.tsv.bz2 | awk 'BEGIN {FS="\t"} NR==FNR{A[$1];next}($4 in A){print $1 "\t" $3 "\t" $4 "\t4" }' eng_4.txt - >> eng_sentences.tsv
bzcat eng_sentences_detailed.tsv.bz2 | awk 'BEGIN {FS="\t"} NR==FNR{A[$1];next}!($4 in A){print $1 "\t" $3 "\t" $4 "\t0" }' eng_known.txt - >> eng_sentences.tsv


cat<<'EOF'>join.awk
BEGIN {FS="\t"}
FNR == 1 {FID++}
FID==1{eng[$1] = $2; credit[$1] = $3; skill[$1] = $4}
FID==2{spa[$1] = $2; credit[$1] = $3; skill[$1] = $4}
FID==3 && $1 in eng && $2 in spa{ print eng[$1] "\t" spa[$2] "\tCC-BY 2.0 (France) Attribution: tatoeba.org #" $1 " (" credit[$1] ") & #" $2 " (" credit[$2] ")\t" skill[$1]+skill[$2] }
EOF

bzcat links.tar.bz2 | gawk -f join.awk eng_sentences.tsv spa_sentences.tsv - | pv > joined.tsv

cat spa.txt joined.tsv | sort -k1,1 -k2,2 -t$'\t' --unique | awk 'BEGIN {FS="\t"}; {x=$1; print gsub(/ /, " ", x) "\t" $0}' | sort -n | cut -f 2- | sed 's/)$/)\t56/' > eng-spa.tsv

./build_sentences.py eng-spa.tsv > spa-only.txt
./build_tags.sh spa-only.txt
./build_sentences.py --tags spa-only.txt.json eng-spa.tsv > spanish_data/sentences.json

# Generate the irregular verb list and table
python3 build_irregular_verbs.py > spanish_words/paradigms.py
