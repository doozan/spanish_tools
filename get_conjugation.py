#!/usr/bin/python3
# -*- python-mode -*-

import sys
import spanish_words
import argparse

parser = argparse.ArgumentParser(description='Conjugate Spanish verb')
parser.add_argument('verb', help="Verb to conjugate")
args = parser.parse_args()

spanish = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt")

#print(words.get_lemma(args.word, args.pos.lower(), debug=True))
print(spanish.verb.conjugate(args.verb))#, debug=True))
