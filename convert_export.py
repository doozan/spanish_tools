#!/usr/bin/python3
# -*- python-mode -*-

import argparse
import csv
import os
import re

import spanish_sentences

parser = argparse.ArgumentParser(description='Convert exported notes to sentence lookup file')
parser.add_argument('infile', help="CSV export to convert")
args = parser.parse_args()

if not os.path.isfile(args.infile):
    print(f"Deck directory does not exist: {args.infile}")
    exit(1)

IDX_WORD=1
IDX_POS=2
IDX_SENTENCES=5

cleanpos = {
    "m": "noun",
    "f": "noun",
    "mf": "noun",
    "f-el": "noun",
    "m-f": "noun",
    "m/f": "noun",

    'v': 'verb',
}

def get_clean_pos(messy_pos):
    return cleanpos.get(messy_pos, messy_pos)

sentence_to_id = {}
def init_sentences():
    sentences = spanish_sentences.sentences("spanish_data/sentences.json")
    for s in sentences.sentencedb:
        sentence_to_id[s[0]] = s[3]
        sentence_to_id[s[1]] = s[4]

def get_sentence_ids(html):
    ids = []
    for res in re.findall(r'span class=""spa"">([^<]+)<.*?span class=""eng"">([^<]+)<', html):
        spa_id = sentence_to_id.get(res[0])
        eng_id = sentence_to_id.get(res[1])
        if spa_id and eng_id:
            ids.append(f"{spa_id}:{eng_id}")

    return ids


with open(args.infile) as infile:
    csvreader = csv.reader(infile)

    init_sentences()

    print("spanish,pos,sid1,sid2,sid3")
    for row in csvreader:
        word = row[IDX_WORD]
        pos = get_clean_pos(row[IDX_POS])
        ids = get_sentence_ids(row[IDX_SENTENCES])
        if len(ids):
            print(",".join( [word,pos] + list(map(str, ids)) ))
