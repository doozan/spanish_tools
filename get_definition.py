import sys
import spanish_words
import argparse

parser = argparse.ArgumentParser(description='Get definition of word')
parser.add_argument('--syn', action='store_true', help="Show synonyms instead of definitions")
parser.add_argument('word', help="Word to search for")
parser.add_argument('pos', nargs="?", default="", help="part of speech")
args = parser.parse_args()

def pretty_print(word, item):
    for pos in item:
        print("==========================")
        print("%s (%s)"%(word, pos))

        for tag in item[pos]:
            defs = spanish_words.get_best_defs(item[pos][tag],40)
            usage = spanish_words.defs_to_string(defs, pos)

            if tag == "x":
                print(usage)
            else:
                print("%s: %s" % (tag, usage))
    print("==========================")


if (args.syn):
    print("See also: %s" % "$ ".join(spanish_words.get_synonyms(args.word)))
else:
    result = spanish_words.lookup(args.word, args.pos)
    pretty_print(args.word, result)