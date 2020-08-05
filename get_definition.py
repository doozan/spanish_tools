#!/usr/bin/python3
# -*- python-mode -*-

import argparse
import os

from spanish_words import SpanishWords

parser = argparse.ArgumentParser(description='Get definition of word')
parser.add_argument('--strict', action='store_true', help="Limit result to the pos specified")
parser.add_argument('--dictionary', help="Dictionary file name (DEFAULT: es-en.txt)")
parser.add_argument('--data-dir', help="Directory contaning the dictionary (DEFAULT: SPANISH_DATA_DIR environment variable or 'spanish_data')")
parser.add_argument('--custom-dir', help="Directory containing dictionary customizations (DEFAULT: SPANISH_CUSTOM_DIR environment variable or 'spanish_custom')")
parser.add_argument('word', help="Word to search for")
parser.add_argument('pos', nargs="?", default="", help="part of speech")
args = parser.parse_args()

if not args.dictionary:
    args.dictionary="es-en.txt"

if not args.data_dir:
    args.data_dir = os.environ.get("SPANISH_DATA_DIR", "spanish_data")

if not args.custom_dir:
    args.custom_dir = os.environ.get("SPANISH_CUSTOM_DIR", "spanish_custom")

words = SpanishWords(dictionary=args.dictionary, data_dir=args.data_dir, custom_dir=args.custom_dir)

def make_shortdef(defs):
    usage = ""
    pos = next(iter(defs))

    shortdef = next(iter(defs[pos].values()))

    if len(shortdef) < 80:
        return shortdef

    shortdef = shortdef.partition(';')[0].strip()

    if len(shortdef) < 80:
        return shortdef

    shortdef = shortdef.partition('(')[0].strip()

    if len(shortdef) < 80:
        return shortdef

    print(f"Long shortdef: {shortdef}")
    return shortdef


def pretty_print(word, item, syns):
    if not item:
        return

    shortdef = make_shortdef(item)
    print(f"ShortDef: {shortdef}")

    for pos in item:
        print("==========================")
        print("%s (%s)"%(word, pos))

        for note,usage in item[pos].items():
            if note == "":
                print(usage)
            else:
                print("%s: %s" % (note, usage))
    print("==========================")
    if len(syns):
        print("See also: %s" % ", ".join(syns))


syns = words.get_synonyms(args.word, args.pos)

res = words.lookup(args.word, args.pos, get_all_pos=(not args.strict))

pretty_print(args.word, res, syns)
