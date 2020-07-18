#!/usr/bin/python3
# -*- python-mode -*-

import sys
import spanish_sentences
import argparse

parser = argparse.ArgumentParser(description='Get sentences that contain variations of specified word')
parser.add_argument('word', help="Word to search for")
parser.add_argument('pos', nargs="?", default="", help="part of speech")
parser.add_argument('count', nargs="?", default=3, type=int, help="Max sentences to retrieve")
args = parser.parse_args()

spanish_sentences = spanish_sentences.sentences("spanish_data/sentences.json")

def format_sentences(sentences):
    return "\n".join(f'spa: {s[3]} - {s[2]} - {s[0]}\neng: {s[4]} - {s[2]} - {s[1]}' for s in sentences )

def get_sentences(lookup, pos, count):
    results = spanish_sentences.get_sentences(lookup, pos, count)

    if len(results['sentences']):
        print("Matched ", results['matched'])
        print( format_sentences(results['sentences']) )

    return ""

get_sentences(args.word, args.pos, args.count)
