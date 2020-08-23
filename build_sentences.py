#!/usr/bin/python3
# -*- python-mode -*-

import argparse
import ijson
import json
import os
import re

from spanish_words import SpanishWords

parser = argparse.ArgumentParser(description="Manage tagged sentences")
parser.add_argument(
    "sentences",
    default="spa.txt",
    help="Master sentences file with spanish/english sentences (default spa.txt)",
)
parser.add_argument(
    "--credits", action="store_true", help="Print sentence credits only"
)
parser.add_argument("--tags", nargs=1, help="Merged tagged data with original data")
parser.add_argument("--dictionary", help="Dictionary file name (DEFAULT: es-en.txt)")
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

if not args.data_dir:
    args.data_dir = os.environ.get("SPANISH_DATA_DIR", "spanish_data")

if not args.custom_dir:
    args.custom_dir = os.environ.get("SPANISH_CUSTOM_DIR", "spanish_custom")

if not os.path.isfile(args.sentences):
    raise FileNotFoundError(f"Cannot open: {args.sentences}")

if args.tags and not os.path.isfile(args.tags[0]):
    raise FileNotFoundError(f"Cannot open: {args.tags}")

words = SpanishWords(
    dictionary=args.dictionary, data_dir=args.data_dir, custom_dir=args.custom_dir
)

mismatch = {}


def tag_to_pos(tag):

    word = tag["form"]
    lemma = tag["lemma"]
    ctag = tag["ctag"]

    pos = None
    if ctag.startswith("A"):  # and lemma not in ["el", "la", "uno"]:
        pos = "adj"
    elif ctag.startswith("C"):  # and lemma not in ["si", "que"]:
        if lemma not in ["y"]:
            pos = "conj"
    elif ctag.startswith("D"):
        pos = "art"
    elif ctag.startswith("I"):
        pos = "interj"
    elif ctag.startswith("N"):  # and lemma not in ["tom", "mary", "john", "maría"]:
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
        word = word.lower()

    # Use our lemmas so they're the same when we lookup against other things we've lemmatized
    # Unless it's a phrase, then use their lemma
    if pos in ("noun", "adj", "part", "adv"):
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

    if word != lemma:
        return [pos, f"{word}|{lemma}"]

    return [pos, f"{word}"]


def group_tags(pos_tags):

    res = {}
    for item in pos_tags:
        if not item:
            continue
        pos, wordtag = item
        if pos not in res:
            res[pos] = [wordtag]
        else:
            res[pos] += [wordtag]

    for pos, words in res.items():
        res[pos] = list(dict.fromkeys(words))

    return res


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
            english, spanish, credits, score = sdata

            wordcount = spanish.count(" ") + 1

            # ignore sentences with less than 6 or more than 15 spanish words
            if wordcount < 5 or wordcount > 15:
                continue

            # ignore duplicates
            # if english in seen or spanish in seen:
            if spanish in seen:
                continue
            else:
                seen[english] = 1
                seen[spanish] = 1

            sid = re.search("& #([0-9]+)", credits).group(1)
            sentences[sid] = sdata

    return sentences


def print_untagged_sentences():
    sentences = load_sentences()

    first = True
    for sid, sdata in sentences.items():
        if not first:
            print("")
        print(sdata[1])
        first = False


def print_credits():
    sentences = load_sentences()

    users = {}

    for english, spanish, credits, score in sentences.values():
        res = re.match(
            r"CC-BY 2.0 \(France\) Attribution: tatoeba.org #([0-9]+) \(([^)]+)\) & #([0-9]+) \(([^)]+)\)",
            credits,
        )
        eng_id, eng_user, spa_id, spa_user = res.groups()
        for user in [eng_user, spa_user]:
            if not user in users:
                users[user] = []
        users[eng_user].append(eng_id)
        users[spa_user].append(spa_id)

    print(f"CC-BY 2.0 (France) Attribution: tatoeba.org")
    for user, sentences in sorted(
        users.items(), key=lambda item: (len(item[1]) * -1, item[0])
    ):
        count = len(sentences)
        if count > 1:
            print(f"{user} ({len(sentences)}) #{', #'.join(sorted(sentences))}\n")
        else:
            print(f"{user} #{', #'.join(sorted(sentences))}")


def print_tagged_data():

    sentences = load_sentences()
    idx2sent = list(sentences.keys())

    tagdata = {}

    with open(args.tags[0], "r", encoding="utf-8") as infile:

        seen = {}
        index = 0

        items = ijson.kvitems(infile, "item")

        for k, v in items:
            if k != "sentences":
                continue

            sdata = sentences[idx2sent[index]]
            english, spanish, credits, score = sdata
            index = index + 1

            pos_tags = []
            for s in v:
                for t in s["tokens"]:
                    pos_tag = tag_to_pos(t)
                    if not pos_tag:
                        continue
                    pos_tags.append(pos_tag)
                    pword, junk, plemma = pos_tag[1].partition("|")
                    if not plemma:
                        plemma = pword
                    if "_" in plemma:
                        for word, lemma in zip(pword.split("_"), plemma.split("_")):
                            if word != lemma:
                                pos_tags.append(["split", f"{word}|{lemma}"])
                            else:
                                pos_tags.append(["split", f"{word}"])

            tags = group_tags(pos_tags)

            # ignore sentences with the same adj/adv/noun/verb/pastparticiple lemma combination
            unique_tags = []
            for pos in ["adj", "adv", "noun", "verb", "part"]:
                if pos not in tags:
                    continue
                for t in tags[pos]:
                    word, junk, lemma = t.partition("|")
                    if not lemma:
                        lemma = word
                    unique_tags.append(lemma)

            uniqueid = "!".join(sorted(set(unique_tags)))
            if uniqueid in seen:
                continue
            seen[uniqueid] = 1

            interj = get_interjections(spanish)
            if interj:
                tags["interj"] = list(map(str.lower, interj))

            tag_str = " ".join(
                [f":{tag}," + ",".join(items) for tag, items in tags.items()]
            )

            print(f"{english}\t{spanish}\t{credits}\t{str(score).zfill(2)}\t{tag_str}")


if args.credits:
    print_credits()
elif args.tags:
    print_tagged_data()
else:
    print_untagged_sentences()
