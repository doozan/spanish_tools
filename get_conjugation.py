#!/usr/bin/python3
# -*- python-mode -*-

import argparse
import os

from spanish_words import SpanishWords

parser = argparse.ArgumentParser(description='Conjugate Spanish verb')
parser.add_argument('verb', help="Verb to conjugate")
parser.add_argument('--dictionary', help="Dictionary file name (DEFAULT: es-en.txt)")
parser.add_argument('--data-dir', help="Directory contaning the dictionary (DEFAULT: SPANISH_DATA_DIR environment variable or 'spanish_data')")
parser.add_argument('--custom-dir', help="Directory containing dictionary customizations (DEFAULT: SPANISH_CUSTOM_DIR environment variable or 'spanish_custom')")
args = parser.parse_args()

if not args.dictionary:
    args.dictionary="es-en.txt"

if not args.data_dir:
    args.data_dir = os.environ.get("SPANISH_DATA_DIR", "spanish_data")

if not args.custom_dir:
    args.custom_dir = os.environ.get("SPANISH_CUSTOM_DIR", "spanish_spanish")

words = SpanishWords(dictionary=args.dictionary, data_dir=args.data_dir, custom_dir=args.custom_dir)

print(words.verb.conjugate(args.verb))#, debug=True))
