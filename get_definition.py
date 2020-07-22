#!/usr/bin/python3
# -*- python-mode -*-

import argparse
from spanish_words import SpanishWords

parser = argparse.ArgumentParser(description='Get definition of word')
parser.add_argument('--syn', action='store_true', help="Show synonyms instead of definitions")
parser.add_argument('word', help="Word to search for")
parser.add_argument('pos', nargs="?", default="", help="part of speech")
args = parser.parse_args()

def pretty_print(word, item, syns):
    if not item:
        return
    for pos in item:
        print("==========================")
        print("%s (%s)"%(word, pos))

        for note,usage in item[pos].items():
#            defs = spanish_words.get_best_defs(item[pos][note],40)
#            defs = spanish_words.split_defs(defs)
#            usage = spanish_words.defs_to_string(defs, pos)

            if note == "":
                print(usage)
            else:
                print("%s: %s" % (note, usage))
    print("==========================")
    if len(syns):
        print("See also: %s" % ", ".join(syns))


spanish = SpanishWords(dictionary="spanish_data/es-en.txt")
syns = spanish.get_synonyms(args.word, args.pos)

if (args.syn):
    print("See also: %s" % ", ".join(syns))
else:
    res = spanish.lookup(args.word, args.pos)

#    print(res)
    pretty_print(args.word, res, syns)
