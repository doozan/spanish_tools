#!/usr/bin/python3
# -*- python-mode -*-

import sys
import spanish_words
import argparse

parser = argparse.ArgumentParser(description='Get lemma from word and pos')
parser.add_argument('word', help="Word to get lemma for")
parser.add_argument('pos',  help="part of speech")
args = parser.parse_args()

spanish = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt")

print(spanish.get_lemma(args.word, args.pos.lower(), debug=True))
