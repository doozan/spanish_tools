#!/bin/bash

# Apache-2.0 License 
# based on https://github.com/sandae/epubFreq/blob/master/epubfreq.sh

function fail {
    echo $1
    exit 1
}

filename=$1
[ -f "$filename" ] || fail "Cannot find $1"

workspace=`mktemp -d`
unzip -q "$filename" -d "$workspace"

htmlfiles="$(find $workspace -maxdepth 10 -type f -name "*.*htm*")"

for f in $htmlfiles; do
    sed -r -e "s/>/>\n/g" -e "s/</\n</g" $f \
      | sed -n '/</!p' \
      | sed -e 's/\b/\n/g' -e 's/_/\n/g' \
      | sed '/\W/d' \
      | tr -d 0-9 \
      | sed '/^$/d' \
      | sed -r 's/([A-Z])/\l\1/g' \
      >> $workspace/all_words
done

cat $workspace/all_words \
    | sort \
    | uniq -i -c \
    | sort -n -r -s \
    | sed -e 's/^\W*\([0-9]*\) \(.*\)/\2 \1/g'

rm -rf "$workspace"
