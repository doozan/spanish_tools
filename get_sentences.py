#!/usr/bin/python3
# -*- python-mode -*-

import sys
import spanish_words
import spanish_sentences
import argparse

parser = argparse.ArgumentParser(description='Get sentences that contain variations of specified word')
parser.add_argument('word', help="Word to search for")
parser.add_argument('pos', nargs="?", default="", help="part of speech")
parser.add_argument('count', nargs="?", default=3, type=int, help="Max sentences to retrieve")
args = parser.parse_args()

words = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt")
spanish_sentences = spanish_sentences.sentences("spanish_data/sentences.json")

def format_sentences(sentences):
    return "\n".join(f'spa: {s[3]} - {s[2]} - {s[5]} - {s[0]}\neng: {s[4]} - {s[2]} - {s[5]} - {s[1]}' for s in sentences )

def get_sentences(spanish, pos, count):

    usage = words.lookup(spanish, pos)
    all_usage_pos = { words.common_pos(k):1 for k in usage }.keys() if usage else [ pos ]
    lookups = [ [ spanish, pos ] for pos in all_usage_pos ]
    results = spanish_sentences.get_sentences(lookups, 3)

    if len(results['sentences']):
        print("Matched ", results['matched'])
        print("Pos: ", all_usage_pos)
        print( format_sentences(results['sentences']) )

    return ""

get_sentences(args.word, args.pos, args.count)
