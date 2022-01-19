#!/bin/python3

'''
wget https://github.com/hermitdave/FrequencyWords/raw/master/content/2018/es/es_full.txt
wget http://corpus.rae.es/frec/CREA_total.zip
zcat CREA_total.zip | tail -n +2 | awk '{gsub("\\,",""); print $2" "$3;}' | iconv -f ISO-8859-1 -t UTF-8  > CREA_full.txt
python3 merge.py es_full.txt CREA_full.txt | awk '$2>3' > merged.txt
'''

import argparse
import sys

parser = argparse.ArgumentParser(description="Combine two frequency lists")
parser.add_argument("file1")
parser.add_argument("file2")
args = parser.parse_args()

words = {}
matches = 0

stats = []
for i, filename in enumerate([args.file1, args.file2]):
    stat = { 'items': 0, 'weight': 0, 'filename': filename }
    with open(filename) as infile:
        stat["weight"] = sum(int(line.split()[1]) for line in infile)
    stats.append(stat)

max_weight = max(stat["weight"] for stat in stats)
print(stats, file=sys.stderr)

for stat in stats:
    scale = 1
    #scale = max_weight/stat["weight"]
    #print("scaling factor", scale, max_weight, stat["weight"], file=sys.stderr)
    with open(stat["filename"]) as infile:
        for line in infile:
            word,count = line.split()
            scaled = int(int(count)*scale)
            current = words.get(word, 0)
            words[word] = current + scaled
            if current:
                matches += 1

print(matches, "matching words of", len(words), "total words", file=sys.stderr)

for word in sorted(words, key=words.get, reverse=True):
    print(f"{word} {words[word]}")
