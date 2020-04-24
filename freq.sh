#!/bin/bash

stats () {

origfile=/tmp/${1}_orig.csv
[ -f $origfile ] || echo "$origfile not found" 

posfile=/tmp/${1}_pos.csv
[ -f $posfile ] || echo "$posfile not found"

clearfile=/tmp/${1}_clear.csv
echo "spanish,pos" > $clearfile
grep CLEAR $origfile | cut -d ',' -f '2,3' >> $clearfile

top5k=/tmp/${1}_top5k.csv
head -5001 $clearfile > $top5k

WORDS=$(cat $origfile | wc -l)
CLEAR=$(cat $clearfile | wc -l)
NOSENT=$(grep ",NOSENT," $origfile | wc -l )
USABLE=$((CLEAR + NOSENT))
NOPOS=$(grep ',none' $posfile | wc -l)

echo "$WORDS total words"
echo "$USABLE usable words ($CLEAR clear, $NOSENT nosent)"
echo "$NOPOS missing POS"
echo "$(head -5001 $clearfile | grep ',noun' | wc -l) Nouns in top 5000"
echo "$(head -5001 $clearfile | grep ',verb' | wc -l) Verbs in top 5000"
echo "$(head -5001 $clearfile | grep ',adj' | wc -l) Adjectives in top 5000"
echo "$(head -5001 $clearfile | grep ',adv' | wc -l) Adverbs in top 5000"

}

compare () {

comparefile=/tmp/compare_${1}_${2}.txt
python3 compare.py /tmp/${1}_clear.csv /tmp/${2}_clear.csv > $comparefile
MISSING=$(grep "^-" $comparefile | wc -l)
CHANGED=$(grep "^~" $comparefile | wc -l)
ADDED=$(grep "^+" $comparefile | wc -l)
CHANGES=$((MISSING + CHANGED + NEW))

echo "$CHANGES changes from $1 ($CHANGED changed, $MISSING removed, $ADDED new)"
}


do_freq () {
python3 freq.py 2018_es_50k.txt 2018.csv || exit
#echo "spanish,pos">/tmp/words.csv && grep CLEAR 2018.csv | cut -d',' -f'2,3'  >> /tmp/words.csv
#python3 compare.py 5k.csv /tmp/words.csv | cut -d ',' -f1,2,3 > /tmp/list.csv
#grep "^1," /tmp/list.csv  | cut -d ',' -f2 | sort | uniq > /tmp/c1.txt
#grep "^2," /tmp/list.csv  | cut -d ',' -f2 | sort | uniq > /tmp/c2.txt
}

newtag=new
oldtag=lastrun
[ -z "$1" ] || newtag=$1
[ -z "$2" ] || oldtag=$2

echo "$oldtag stats"
stats $oldtag
do_freq
cp 2018.csv /tmp/${newtag}_orig.csv
cp 2018_es_50k.txt.lemmas.csv /tmp/${newtag}_pos.csv
echo "########################"
echo "New stats"
stats $newtag

compare $oldtag $newtag
[ "$oldtag" == "lastrun" ] || compare lastrun $newtag

echo "see /tmp/compare_lastrun_${newtag}.txt for details"

cp /tmp/${newtag}_orig.csv /tmp/lastrun_orig.csv
cp /tmp/${newtag}_pos.csv /tmp/lastrun_pos.csv
