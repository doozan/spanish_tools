#!/usr/bin/python3
# -*- python-mode -*-

import argparse
import ijson
import json
import os
import re
import string

import sys

from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms
from .freq import FrequencyList as Freq

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
parser.add_argument("--dictionary", help="Dictionary file", required=True)
parser.add_argument("--allforms", help="Load word forms from file")
parser.add_argument("--low-mem", help="Use less memory", action='store_true', default=False)
parser.add_argument('--verbose', action='store_true')
args = parser.parse_args()

if not os.path.isfile(args.sentences):
    raise FileNotFoundError(f"Cannot open: {args.sentences}")

if args.tags and not os.path.isfile(args.tags[0]):
    raise FileNotFoundError(f"Cannot open: {args.tags}")

cache_words = not args.low_mem
with open(args.dictionary) as infile:
    wordlist = Wordlist(infile, cache_words=cache_words)

if args.allforms:
    all_forms = AllForms.from_file(args.allforms)
else:
    all_forms = AllForms.from_wordlist(wordlist)

def tag_to_pos(tag, word):

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
        pos = "prop" if ctag == "NP" else "n"
    elif ctag.startswith("P"):
        pos = "pron"
    elif ctag.startswith("R"):
        if lemma not in ["no"]:
            pos = "adv"
    elif ctag.startswith("S"):
        # if lemma not in ["a", "con", "de", "en", "por", "para"]:
        pos = "prep"
    elif ctag.startswith("V"):
        pos = "part" if ctag.endswith("P") else "v"
    elif ctag.startswith("Z") and not word.isdigit():
        pos = "num"
        lemma = word
    if not pos:
        return []

    if pos != "prop":
        word = word.lower()

    # Use our lemmas so they're the same when we lookup against other things we've lemmatized
    # Unless it's a phrase, then use their lemma
    if pos in ("n", "adj", "adv"):
        lemma = get_lemmas(wordlist, word, pos)

    # fix for freeling not generating lemmas for verbs with a pronoun suffix
    elif pos == "v":
        if not lemma.endswith("r"):
            lemma = get_lemmas(wordlist, word, pos)

    elif "_" in lemma:
        lemma = word

    # Special handling for participles, add adjective and verb lemmas
    if pos == "part":
        adj_lemma = get_lemmas(wordlist, word, "adj")
        verb_lemma = get_lemmas(wordlist, word, "v")
        adj_res = f"{word}|{adj_lemma}" if adj_lemma != word else word
        verb_res = f"{word}|{verb_lemma}" if verb_lemma != word else word

        # NOTE: part-verb doesn't match "v", but this is intentional
        return [("part-adj", adj_res), ("part-verb", verb_res)]

    if word != lemma:
        return[(pos, f"{word}|{lemma}")]

    return[(pos, word)]


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


def get_lemmas(wordlist, word, pos):

    lemmas = [x.split("|")[1] for x in all_forms.get_lemmas(word, [pos])]
    lemmas = Freq.get_best_lemmas(wordlist, word, lemmas, pos)

    if not lemmas:
        return word

    return "|".join(sorted(lemmas))

def iter_sentences():

    seen = set()
    with open(args.sentences) as infile:
        for line in infile:

            line = line.strip()
            english, spanish, credits, english_score, spanish_score = line.split("\t")

            wordcount = spanish.count(" ") + 1

            # ignore sentences with less than 6 or more than 15 spanish words
            if wordcount < 5 or wordcount > 15:
                continue

            # ignore duplicates
            # if english in seen or spanish in seen:
            uniqueid = hash(spanish)
            if uniqueid in seen:
                continue
            else:
                seen.add(uniqueid)

            # de-prioritize meta sentences
            if "atoeba" in english:
                english_score = spanish_score = 0

            sid = re.search("& #([0-9]+)", credits).group(1)
            yield [sid, english, spanish, credits, english_score, spanish_score]


def print_untagged_sentences():

    first = True
    for sid, english, spanish, credits, english_score, spanish_score in iter_sentences():
        if not first:
            print("")
        print(spanish)
        first = False

def print_credits():

    users = {}

    for sid, english, spanish, credits, english_score, spanish_score in iter_sentences():
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


word_chars = string.ascii_lowercase + "áéíóúüñ"
word_chars += word_chars.upper()
def is_boundary(c):
    return c not in word_chars

def get_original_form(tag, sentence, offset):
    """
    Verbs with pronoun suffixes are tokenized into to individual words by freeling
    This function yields the original, untokenized word
    Offset is used to adjust the begin/end tags because they're given as positions
    within the original source file, not within the sentence
    """

    if not "pos" in tag:
        return tag["form"]

    # Don't mess with multi-word stuff
    if "_" in tag["form"]:
        return tag["form"]

    if not tag["ctag"].startswith("V"):
        return tag["form"]

    start = int(tag["begin"])-offset
    end = int(tag["end"])-offset-1

    while start > 0 and not is_boundary(sentence[start-1]):
        start -= 1

    while end < len(sentence)-1 and not is_boundary(sentence[end+1]):
        end += 1

    word = sentence[start:end+1]
    return word


def print_tagged_data(verbose=False):

    tagdata = {}

    count = 0
    with open(args.tags[0], "r", encoding="utf-8") as infile:

        seen = set()

        items = ijson.kvitems(infile, "item")

        for sid, english, spanish, credits, english_score, spanish_score in iter_sentences():

            for k,v in items:
                if k == "sentences":
                    break

            count += 1
            if not count % 1000 and verbose:
                print(count, end="\r", file=sys.stderr)

            all_tags = []
            first = True
            for s in v:
                for t in s["tokens"]:
                    if first:
                        offset = int(t["begin"])
                        first = False
                    form = get_original_form(t, spanish, offset)
                    pos_tags = []
                    for word in sorted(set([form, t["form"]])):
                        pos_tags += tag_to_pos(t, word)
                    if not pos_tags:
                        continue
                    pos_tags = sorted(list(set(pos_tags)))
                    all_tags += pos_tags
                    for pos_tag in pos_tags:
                        pword, junk, plemma = pos_tag[1].partition("|")
                        if not plemma:
                            plemma = pword
                        if "_" in plemma:
                            for word, lemma in zip(pword.split("_"), plemma.split("_")):
                                if word != lemma:
                                    all_tags.append(["split", f"{word}|{lemma}"])
                                else:
                                    all_tags.append(["split", f"{word}"])

            grouped_tags = group_tags(all_tags)

            # ignore sentences with the same adj/adv/noun/verb lemma combination
            unique_tags = set()
            for pos, tags in grouped_tags.items():
                if pos not in ["adj", "adv", "n", "v", "part-adj", "part-verb"]:
                    continue
                for t in tags:
                    word, junk, lemma = t.partition("|")
                    if not lemma:
                        lemma = word
                    unique_tags.add(lemma)

            uniqueid = hash(":".join(sorted(unique_tags)))

            if uniqueid in seen:
                continue
            seen.add(uniqueid)

            interj = get_interjections(spanish)
            if interj:
                grouped_tags["interj"] = list(map(str.lower, interj))

            tag_str = " ".join(
                [f":{tag}," + ",".join(items) for tag, items in grouped_tags.items()]
            )

            print(f"{english}\t{spanish}\t{credits}\t{english_score}\t{spanish_score}\t{tag_str}")

if args.credits:
    print_credits()
elif args.tags:
    print_tagged_data(args.verbose)
else:
    print_untagged_sentences()
