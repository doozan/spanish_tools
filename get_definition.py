import argparse
from spanish_words import SpanishWords

parser = argparse.ArgumentParser(description='Get definition of word')
parser.add_argument('--syn', action='store_true', help="Show synonyms instead of definitions")
parser.add_argument('word', help="Word to search for")
parser.add_argument('pos', nargs="?", default="", help="part of speech")
args = parser.parse_args()

def pretty_print(word, item):
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


spanish = SpanishWords(dictionary="spanish_data/es-en.txt", synonyms="spanish_data/synonyms.txt")

if (args.syn):
    print("See also: %s" % ", ".join(spanish.synonyms.get_synonyms(args.word)))
else:
    res = spanish.wordlist.lookup(args.word, args.pos)

#    print(res)
    pretty_print(args.word, res)
