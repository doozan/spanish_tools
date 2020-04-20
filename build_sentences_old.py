import argparse
#import basewords
import sys
from os import path
#import spanish_lemmas
import spanish_words


parser = argparse.ArgumentParser(description='Generate a list of tagged/lemmatized sentences')
parser.add_argument('infile', help="File with clean sentences")
parser.add_argument('tagfile', help="File with tagged sentences")
args = parser.parse_args()

_origfile=args.infile
_tagfile=args.tagfile
if not path.isfile(_origfile):
    print("Cannot open orig file %s"%_origfile, file=sys.stderr)
    exit(1)

if not path.isfile(_tagfile):
    print("Cannot open tag file %s"%_tagfile, file=sys.stderr)
    exit(1)


pos_class_tags = {
    "A": "ADJ",
    "C": "CONJ",
    "D": "DET",
    "N": "NOUN",
    "P": "PRON",
    "R": "ADV",
    "S": "PREP",
    "V": "VERB",
    "Z": "NUM"
}

def get_tagged_word(item):
    word, tag = item.split('/',2)

    word = word.strip().lower()
    tagclass = tag[0]
    if tagclass in pos_class_tags:
        pos = pos_class_tags[tagclass]
        lemma = spanish_words.get_lemma(word, pos)
        if not lemma:
            lemma = word
        return pos + ":" + lemma + "|@" + word


with open(_origfile) as origfile, open(_tagfile) as tagfile:
    seen = {}
    for line in origfile:
        line = line.strip()
        english, spanish, extra = line.split('\t')

        tagline = next(tagfile).strip()
        tokens = tagline.split(' ')

        # ignore sentences with less than 5 or more than 15 spanish words
        if len(tokens) < 5 or len(tokens) > 15:
            continue

        # ignore duplicates
        if english in seen or spanish in seen:
            continue
        else:
            seen[english] = 1
            seen[spanish] = 1

        tags = []
        for token in tokens:
            res = get_tagged_word(token)
            if res:
                tags.append(res)

        # ignore simple sentences
        if len(tags) < 2:
            continue

        # ignore sentences with the same adj/adv/noun/verb combination
        unique_tags = [t for t in tags if t[0] in ["A", "N", "V" ]]
        uniqueid = ":".join(sorted(unique_tags))
        if uniqueid in seen:
            continue
        seen[uniqueid] = 1

        tagged = " ".join(tags).lower()

        print("\t".join((english, spanish, tagged, extra)))
