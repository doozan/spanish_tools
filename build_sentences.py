#!/usr/bin/python3
# -*- python-mode -*-

import argparse
import sys
import os
import re
import json
import spanish_words
import bz2



parser = argparse.ArgumentParser(description='Manage tagged sentences')
parser.add_argument('--tags', nargs=1, help="Merged tagged data with original data")
parser.add_argument('sentences', default="spa.txt", help="Master sentences file with spanish/english sentences (default spa.txt)")
args = parser.parse_args()

if not os.path.isfile(args.sentences):
    raise FileNotFoundError(f"Cannot open: {args.sentences}")

if args.tags and not os.path.isfile(args.tags[0]):
    raise FileNotFoundError(f"Cannot open: {args.tags}")

words = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt")

mismatch = {}

def tag_to_pos(tag):

    word = tag['form']
    lemma = tag['lemma']
    ctag = tag['ctag']

    pos = None
    if ctag.startswith("A"): # and lemma not in ["el", "la", "uno"]:
        pos = "adj"
    elif ctag.startswith("C"): # and lemma not in ["si", "que"]:
        if lemma not in ["y"]:
            pos = "conj"
    elif ctag.startswith("D"):
        pos = "art"
    elif ctag.startswith("I"):
        pos = "interj"
    elif ctag.startswith("N"): # and lemma not in ["tom", "mary", "john"]:
        pos = "propnoun" if ctag == "NP" else "noun"
    elif ctag.startswith("P"):
        pos = "pron"
    elif ctag.startswith("R"):
        if lemma not in ["no"]:
            pos = "adv"
    elif ctag.startswith("S"):
       # if lemma not in ["a", "con", "de", "en", "por", "para"]:
            pos = "prep"
    elif ctag.startswith("V"):
        pos = "part" if ctag.endswith("P") else "verb"
    elif ctag.startswith("Z") and not word.isdigit():
        pos = "num"
        lemma = word
    if not pos:
        return None

    if pos != "propnoun":
#        if pos != "num" and "_" in lemma:
#            print(f"c-c-combo: {pos} {lemma}: {word}", file=sys.stderr)
#            return None
        word = word.lower()

    # Use our lemmas so they're the same when we lookup against other things we've lemmatized
    # Unless it's a phrase, then use their lemma
    if pos in ("noun", "adj", "part"):
        lemma = words.get_lemma(word, pos)

    # fix for freeling not generating lemmas for verbs with a pronoun suffix
    elif pos == "verb":
        if not lemma.endswith("r"):
            lemma = words.get_lemma(word, pos)

    elif "_" in lemma:
        lemma = word

#        newlemma = words.get_lemma(word, pos)
#        if lemma != newlemma:
#            mismatch[f"{pos}:{lemma}"] = newlemma
#            lemma = newlemma

    return [ pos, lemma, "@"+word ]


def group_tags(pos_tags):

    res = {}
    for item in pos_tags:
        if not item:
            continue
        pos, lemma, word = item
        if pos not in res:
            res[pos] = [lemma, word]
        else:
            res[pos] += [lemma, word]

    for pos,words in res.items():
        res[pos] = list(dict.fromkeys(words))

    return res

#    return good_tags

def get_interjections(string):

    pattern = r"""(?x)(?=          # use lookahead as the separators may overlap (word1. word2, blah blah) should match word1 and word2 using "." as a separator
        (?:^|[:;,.¡!¿]\ ?)         # Punctuation (followed by an optional space) or the start of the line
        ([a-zA-ZáéíñóúüÁÉÍÑÓÚÜ]+)  # the interjection
        (?:[;,.!?]|$)              # punctuation or the end of the line
    )"""
    return re.findall(pattern, string, re.IGNORECASE)



def load_sentences():
    sentences = {}

    seen = {}
    with open(args.sentences) as infile:
        for line in infile:
            line = line.strip()
            sdata = line.split("\t")
            english,spanish,credits = sdata

            wordcount = spanish.count(" ")+1

            # ignore sentences with less than 6 or more than 15 spanish words
            if wordcount < 5 or wordcount > 15:
                continue

            # ignore duplicates
            if english in seen or spanish in seen:
                continue
            else:
                seen[english] = 1
                seen[spanish] = 1

            sid=re.search("& #([0-9]+)", credits).group(1)
            sentences[sid] = sdata

    return sentences


def print_untagged_sentences():
    sentences = load_sentences()

    first=True
    for sid, sdata in sentences.items():
        if not first:
            print("")
        print(sdata[1])
        first=False


def print_tagged_data():

    sentences = load_sentences()
    idx2sent = list(sentences.keys())

    tagdata = {}

#    with open(args.tags[0], 'r', encoding="utf-8") as infile:
#        tagdata = json.load(infile)

    with bz2.BZ2File(args.tags[0], 'r') as infile:
        tagdata = json.load(infile)

#    with zipfile.ZipFile(args.tags[0], 'r') as z:
#        filename = z.namelist()[0]
#        with z.open(filename) as f:
#            tagdata = json.load(f)


    first=True
    print("[")
    seen = {}
    index = 0
    for p in tagdata: #['paragraphs']:
        sdata = sentences[idx2sent[index]]
        english, spanish, credits = sdata
        index = index+1

        pos_tags = []
        for s in p['sentences']:
            for t in s['tokens']:
                pos_tag = tag_to_pos(t)
                if not pos_tag:
                    continue
                pos_tags.append(pos_tag)
                plemma = pos_tag[1]
                if "_" in plemma:
                    pword = pos_tag[2][1:]
                    for word,lemma in zip( pword.split("_"), plemma.split("_") ):
                        pos_tags.append(['split', lemma, '@'+word])


        tags = group_tags(pos_tags)

        # ignore sentences with the same adj/adv/noun/verb/pastparticiple combination
        unique_tags = []
        for n in [ "adj", "adv", "noun", "verb", "part" ]:
            if n not in tags:
                continue
            unique_tags += [t for t in tags[n] if not t.startswith("@")]
        uniqueid = ":".join(sorted(set(unique_tags)))
        if uniqueid in seen:
            continue
        seen[uniqueid] = 1


        interj = get_interjections(spanish)
        if interj:
            tags['interj'] = list(map(str.lower, interj))

        english = json.dumps(english, ensure_ascii=False)
        spanish = json.dumps(spanish, ensure_ascii=False)
        tags = json.dumps(tags, ensure_ascii=False)
        credits = json.dumps(credits, ensure_ascii=False)

        if not first:
            print(",\n")
        else:
            first = False

        print(\
f"""[{credits},
{english},
{spanish},
{tags}]""", end="")

    print("\n]")


if not (args.tags):
    print_untagged_sentences()
else:
    print_tagged_data()
