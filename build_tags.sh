#!/bin/sh

analyze -f es.cfg --flush --output json \
--noloc --nodate --noquant \
--outlv tagged < $1 | pv > $1.tagged

echo "[" > $1.json
cat $1.tagged | sed 's/}]}]}/}]}]},/' | head -c -2 >> $1.json
echo "" >> $1.json
echo "]" >> $1.json

