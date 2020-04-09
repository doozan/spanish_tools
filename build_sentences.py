import basewords
import sys
from os import path


_origfile=sys.argv[1]
_tagfile=sys.argv[2]
if not path.isfile(_origfile):
    print("Cannot open orig file %s"%_origfile, file=sys.stderr)
    exit(1)

if not path.isfile(_tagfile):
    print("Cannot open tag file %s"%_tagfile, file=sys.stderr)
    exit(1)

def get_tagged_word(item):
    word, tag = item.split('/',2)

    word = word.strip()
    tagclass = tag[0]

    # Noun
    if tagclass == "N":
        return "NOUN:" + basewords.get_single_noun(word)

    # Adjective
    elif tagclass == "A":
        return "ADJ:" + basewords.get_base_adjective(word)

    # Verb
    elif tagclass == "V":
        verbs = basewords.reverse_conjugate(word)
        if isinstance(verbs, list) and len(verbs) > 0:
            return "VERB:" + verbs[0]

    # Adverb
    elif tagclass == "R":
        return "ADV:" + word


with open(_origfile) as origfile, open(_tagfile) as tagfile:
    seen = {}
    for line in origfile:
        line = line.strip()
        english, spanish, extra = line.split('\t')

        tagline = next(tagfile).strip()
        tokens = tagline.split(' ')

        if len(tokens) < 5 or len(tokens) > 15:
            continue

        tags = []
        for token in tokens:
            res = get_tagged_word(token)
            if res:
                tags.append(res)

        if len(tags) < 2:
            continue

        uniqueid = ";".join(sorted(tags))
        if uniqueid in seen:
            continue
        seen[uniqueid] = 1

        tagged = " ".join(tags).lower()

        print("\t".join((english, spanish, tagged, extra)))
