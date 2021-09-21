#!/bin/sh

analyze -f es.cfg --flush --output json \
--noloc --nodate --noquant \
--outlv tagged < $1 | pv > $1.tagged

echo "[" > $1.json
head -n -1 $1.tagged | sed 's/}]}]}/}]}]},/' | sed '$ s/.$//' >> $1.json
echo "" >> $1.json
echo "]" >> $1.json

