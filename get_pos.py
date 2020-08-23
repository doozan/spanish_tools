#!/usr/bin/python3
# -*- python-mode -*-

import argparse
import os

import get_best_pos
import spanish_sentences
from spanish_words import SpanishWords

parser = argparse.ArgumentParser(description="Guess most likely pos from word")
parser.add_argument("word", help="Word to get pos for")
parser.add_argument(
    "--pos",
    nargs="+",
    type=str,
    help="space separated list of parts of speech to get best from",
)
parser.add_argument("--dictionary", help="Dictionary file name (DEFAULT: es-en.txt)")
parser.add_argument("--sentences", help="Sentences file name (DEFAULT: sentences.tsv)")
parser.add_argument(
    "--data-dir",
    help="Directory contaning the dictionary (DEFAULT: SPANISH_DATA_DIR environment variable or 'spanish_data')",
)
parser.add_argument(
    "--custom-dir",
    help="Directory containing dictionary customizations (DEFAULT: SPANISH_CUSTOM_DIR environment variable or 'spanish_custom')",
)
args = parser.parse_args()

if not args.dictionary:
    args.dictionary = "es-en.txt"

if not args.sentences:
    args.sentences = "sentences.tsv"

if not args.data_dir:
    args.data_dir = os.environ.get("SPANISH_DATA_DIR", "spanish_data")

if not args.custom_dir:
    args.custom_dir = os.environ.get("SPANISH_CUSTOM_DIR", "spanish_custom")

words = SpanishWords(
    dictionary=args.dictionary, data_dir=args.data_dir, custom_dir=args.custom_dir
)
sentences = spanish_sentences.sentences(
    sentences=args.sentences, data_dir=args.data_dir, custom_dir=args.custom_dir
)

print(get_best_pos.get_best_pos(args.word, words, sentences, debug=True))
