#!/usr/bin/python3
# -*- python-mode -*-

import argparse
from spanish_words import SpanishWords

parser = argparse.ArgumentParser(description='Get definition of word')
parser.add_argument('--strict', action='store_true', help="Limit result to the pos specified")
parser.add_argument('word', help="Word to search for")
parser.add_argument('pos', nargs="?", default="", help="part of speech")
args = parser.parse_args()

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


spanish = SpanishWords(dictionary="spanish_data/es-en.txt")
syns = spanish.get_synonyms(args.word, args.pos)

res = spanish.lookup(args.word, args.pos, get_all_pos=(not args.strict))

pretty_print(args.word, res, syns)
