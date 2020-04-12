#!/bin/sh
bzcat enwiktionary-20200401-pages-articles.xml.bz2|gawk -v LANG=Spanish -v ISO=es -v REMOVE_WIKILINKS="y" -f trans-en-es.awk|sort -s -d -k 1,1 -t"{">es-en.txt


#sed 's/{f}/{nf}/g;'
#
#s/bc/ab/g; s/~~/bc/g'

