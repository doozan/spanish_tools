#!/usr/bin/python3
# -*- python-mode -*-

import os
import argparse

import spanish_sentences
from spanish_words import SpanishWords

parser = argparse.ArgumentParser(description='Get sentences that contain variations of specified word')
parser.add_argument('word', help="Word to search for")
parser.add_argument('pos', nargs="?", default="", help="part of speech")
parser.add_argument('count', nargs="?", default=3, type=int, help="Max sentences to retrieve")
parser.add_argument('--strict', action='store_true', help="Only show sentences matching the specified pos")
parser.add_argument('--dictionary', help="Dictionary file name (DEFAULT: es-en.txt)")
parser.add_argument('--sentences', help="Sentences file name (DEFAULT: sentences.json)")
parser.add_argument('--data-dir', help="Directory contaning the dictionary (DEFAULT: SPANISH_DATA_DIR environment variable or 'spanish_data')")
parser.add_argument('--custom-dir', help="Directory containing dictionary customizations (DEFAULT: SPANISH_CUSTOM_DIR environment variable or 'spanish_custom')")
args = parser.parse_args()

if not args.dictionary:
    args.dictionary="es-en.txt"

if not args.sentences:
    args.sentences="sentences.json"

if not args.data_dir:
    args.data_dir = os.environ.get("SPANISH_DATA_DIR", "spanish_data")

if not args.custom_dir:
    args.custom_dir = os.environ.get("SPANISH_CUSTOM_DIR", "spanish_custom")

sentences = spanish_sentences.sentences(sentences=args.sentences, data_dir=args.data_dir, custom_dir=args.custom_dir)

def format_sentences(sentences):
    return "\n".join(f'spa: {s[3]} - {s[2]} - {s[5]} - {s[0]}\neng: {s[4]} - {s[2]} - {s[5]} - {s[1]}' for s in sentences )

def get_sentences(spanish, pos, count, all_usage):

    lookups = [ [ spanish, pos ]]
    if all_usage:
        words = SpanishWords(dictionary=args.dictionary, data_dir=args.data_dir, custom_dir=args.custom_dir)
        usage = words.lookup(spanish, pos)
        all_usage_pos = { words.common_pos(k):1 for k in usage }.keys() if usage else [ pos ]
        lookups = [ [ spanish, pos ] for pos in all_usage_pos ]

    results = sentences.get_sentences(lookups, count)

    if len(results['sentences']):
        print("Matched ", results['matched'])
        if all_usage:
            print("Pos: ", all_usage_pos)
        print( format_sentences(results['sentences']) )

    return ""

get_sentences(args.word, args.pos, args.count, not args.strict)
