#!/usr/bin/python3
# -*- python-mode -*-

import os
import re
import sys

from spanish_words import SpanishWords

words = None
all_plurals = {}

_unstresstab = str.maketrans("áéíóú", "aeiou")
_stresstab = str.maketrans("aeiou", "áéíóú")

def unstress(word):
    return word.translate(_unstresstab)

def stress(word):
    return word.translate(_stresstab)


ignore_pattern = r"""(feminine plural|masculine plural|plural|dated form|informal spelling|nonstandard spelling|alternative spelling|obsolete spelling|alternative form|alternate form|rare spelling|archaic spelling|obsolete form|eye dialect|alternate spelling|rare form|eye dialect|superseded spelling|euphemistic spelling|alternative form|common misspelling|euphemistic form|nonstandard form|obsolete form|informal form|dated spelling|pronunciation spelling|superseded form|alternative typography|misspelling form) of ([^,;:()]+)"""
ignore_notes = {"archaic", "dated", "eye dialect", "heraldry", "heraldiccharge", "historical", "obsolete", "rare", "numismatics"}

def dprint(*args, **kwargs):
    if _args.debug:
        if _args.dry_run:
            print(*args, **kwargs)
        else:
            print(*args, file=sys.stderr, **kwargs)

def get_useful_data(word, meta, data):
    if meta != "meta-noun":
        return data
    else:
        useful_data = {}
        if "m" in data and "f" in data:
            dprint(f"NOTICE: Noun with double genders: {word}")

        elif "m" in data or "f" in data:
            if "m" in data:
                useful_data["m"] = data["m"]
                for xnoun in data["m"]:
                    if not words.has_word(xnoun, "noun"):
                        dprint(f"MISSING: {xnoun} is referenced by {word}, but has no entry")
                    elif word != xnoun and words.wordlist.get_feminine_noun(xnoun) != word:
                        dprint(f"NOTICE: One way masculine noun link: {word} -> {xnoun} but not {xnoun} -> {word}")
            if "f" in data:
                useful_data["f"] = data["f"]
                for xnoun in data["f"]:
                    if not words.has_word(xnoun, "noun"):
                        dprint(f"MISSING: {xnoun} is referenced by {word}, but has no entry")
                    elif word != xnoun and words.wordlist.get_masculine_noun(xnoun) != word:
                        dprint(f"NOTICE: One way feminine noun link: {word} -> {xnoun} but not {xnoun} -> {word}")

        gender = "m" if "f" in data else "f"
        if "pl" in data:
            v = data['pl']
            guess_plural = make_plural(word, gender)
            if guess_plural and (" ".join(sorted(guess_plural)) == " ".join(sorted(v))):
                dprint(f"AUTOFIX: Useless plural declaration in {word}: {v}")
            else:
                useful_data["pl"] = data["pl"]
#                print(" ".join(sorted(guess_plural))," == "," ".join(sorted(v)))
            for v in data['pl']:
                if v in all_plurals and v != "-" and word!=all_plurals[v]:
                    dprint(f"FIXME: Two words share same plural ({v}) {all_plurals[v]}/{word}")
                else:
                    all_plurals[v] = word

        if len(useful_data.keys()):
            return useful_data
        return None

def print_useful_meta(word, meta, data):
    data = get_useful_data(word, meta, data)
    if data:
        print_meta(word, meta, data)


def print_line(linedata):
    if _args.dry_run:
        return

    print(" ".join(linedata))

def print_meta(word, meta, data):
    if _args.dry_run:
        return

    line = [ word, "{"+meta+"}", "::" ]

    for k,values in data.items():
        for v in values:
            line.append(f"{k}:'{v}'")

    print(" ".join(line))

# This is a bug-for-bug implementation of wiktionary Module:es-headword
def make_plural(singular, gender="m"):
    if singular == "":
        return None

    if " " in singular:
        res = re.match("^(.+)( (?:de|a)l? .+)$", singular)  # match xxx (de|del|a|al) yyyy
        if res:
            pl = make_plural(res.group(1), gender)
            if not pl:
                return None
            first = pl[0]
            second = res.group(2)
            return [first+second]
        else:
            words = singular.split(" ")
            if len(words) == 2:
                pl = make_plural(words[0], gender)
                if not pl:
                    return None
                noun = pl[0]
                adj = get_adjective_forms(words[1], gender)
                if not adj:
                    #raise ValueError("No adjective forms for", words[1], gender)
                    return None

                if gender == "m" and "mp" in adj:
                    return [noun + " " + adj["mp"]]
                elif gender == "f" and "fp" in adj:
                    return [noun + " " + adj["fp"]]
        # Bug: Anything with two spaces that doesn't include "de/l" or "a/l" will fall through
        # and be handled as a singular noun

    # ends in unstressed vowel or á, é, ó (casa: casas)
    if singular[-1] in "aeiouáéó":
        return [singular+"s"]

    # ends in í or ú (bambú: [bambús, bambúes])
    if singular[-1] in "íú":
        return [ singular+"s", singular+"es" ]

    # ends in a vowel + z (nariz: narices)
    if len(singular)>1 and singular[-2] in "aeiouáéó" and singular.endswith("z"):
        return [singular[:-1]+"ces"]

    # ends tz (hertz: hertz)
    if singular.endswith("tz"):
        return [singular]

    modsingle = re.sub("qu([ie])", r"k\1", singular)
    vowels = []
    for c in modsingle:
        if c in "aeiouáéíóú":
            vowels.append(c)

    # ends in s or x with more than 1 syllable, last syllable unstressed (saltamontes: saltamontes)
    if len(vowels) > 1 and singular[-1] in "sx":
        return [singular]

    # I can't find any places where this actually applies
    # ends in l, r, n, d, z, or j with 3 or more syllables, accented on third to last syllable
    if len(vowels) > 2 and singular[-1] in "lrndzj" and vowels[len(vowels)-2] in "áéíóú":
        return [singular]

    # ends in a stressed vowel + consonant, remove the stress and add -es (ademán: ademanes)
    if len(singular)>1 and singular[-2] in "áéíóú" and singular[-1] not in "aeiouáéíóú":
        return [ singular[:-2] + unstress(singular[-2:]) + "es" ]

    # ends in an unaccented vowel + y, l, r, n, d, j, s, x (color: coleres)
    if len(singular)>1 and singular[-2] in "aeiou" and singular[-1] in "ylrndjsx":
        # two or more vowels and ends with -n, add stress mark to plural  (desorden: desórdenes)
        if len(vowels) > 1 and singular[-1] == "n":
            res = re.match("^(.*)([aeiou])([^aeiou]*[aeiou][nl])$", modsingle)
            if res:
                start = res.group(1)  # dólmen
                vowel = res.group(2)
                end = res.group(3)
                modplural = start + stress(vowel) + end + "es"
                plural = re.sub("k", "qu", modplural)
                return [ plural ]
        return [ singular + "es" ]

    # ends in a vowel+ch (extremely few cases) (coach: coaches)
    if len(singular)>2 and singular.endswith("ch") and singular[-3] in "aeiou":
        return [ singular + "es" ]

    # this matches mostly loanwords and is usually wrong (confort: conforts)
    if len(singular)>1 and singular[-2] in "bcdfghjklmnpqrstvwxyz" and singular[-1] in "bcdfghjklmnpqrstvwxyz":
        return [ singular + "s" ]

    # this seems to match only loanwords
    # ends in a vowel + consonant other than l, r, n, d, z, j, s, or x (robot: robots)
    if len(singular)>1 and singular[-2] in "aeiou" and singular[-1] in "bcfghkmpqtvwy":
        return [ singular + "s" ]

    return None

# This is a bug-for-bug implementation of wiktionary Module:es-headword
def get_adjective_forms(singular, gender):
    if singular.endswith("dor") and gender == "m":
        return {"ms": singular, "mp": singular+"es", "fs": singular+"a", "fp":singular+"as"}

    if singular.endswith("dora") and gender == "f":
        stem = singular[:-1]
        return {"ms": stem, "mp": stem+"es", "fs": stem+"a", "fp":stem+"as"}

    # Bug: no apparent support for non-feminines that end in -a
    if singular[-1] == "o" or (singular[-1] == "a" and gender == "f"):
        stem = singular[:-1]
        return {"ms": stem+"o", "mp": stem+"os", "fs": stem+"a", "fp":stem+"as"}

    if singular[-1] == "e" or singular.endswith("ista"):
        plural = singular+"s"
        return {"ms": singular, "mp":plural, "fs":singular, "fp":plural}

    if singular[-1] == "z":
        plural = singular[:-1]+"ces"
        return {"ms": singular, "mp":plural, "fs":singular, "fp":plural}

    if singular[-1] == "l" or singular[-2:] in [ "ar", "ón", "ún" ]:
        plural = singular[:-2] + unstress(singular[-2]) + singular[-1] + "es"
        return {"ms": singular, "mp":plural, "fs":singular, "fp":plural}

    if singular.endswith("or"):
        plural = singular+"es"
        return {"ms": singular, "mp":plural, "fs":singular, "fp":plural}

    if singular[-2:] in ["án", "és", "ín"]:
        stem = singular[:-2] + unstress(singular[-2]) + singular[-1]
        return {"ms": singular, "mp":stem+"es", "fs":stem+"a", "fp":stem+"as"}



def main():

    global words
    words = SpanishWords(dictionary=_args.dictionary, data_dir=_args.data_dir, custom_dir=_args.custom_dir)

    seen = {}
    prev_fem = ""
    prev_word = ""
    prev_pos = ""
    with open(_args.infile) as infile:
        for line in infile:
            item = words.wordlist.parse_line(line)

            word = item['word']
            pos = item['pos']
            note = item['note']
            syn = item['syn']
            definition = item['def']

            meta_type = None
            meta_data = []

            # Print notice for any use of the "feminine of" template, which should be replaced with something better
            res = re.search("feminine of ([^,;:()]+)", definition)
            if res:
                dprint(f"FIXME: {word} uses worthless 'feminine of' template")

            if pos == "f":
                first_def = word != prev_fem

                masculine = words.wordlist.get_masculine_noun(word)
                res = re.search("(feminine noun|female equivalent) of ([^,;:()]+)", definition)
                if res:

                    sub_pattern = res.group(0)+r"[,;:()]*\s*"
                    definition = re.sub(sub_pattern, "", definition)
#                    print(f"Cleaned: '{old_def}' => '{definition}'")

                    def_masculine = res.group(2).strip()
                    if masculine and def_masculine != masculine:
                        dprint(f"FIXME: {word} is confused about its partner, definition says {def_masculine} but header says {masculine}")
                    else:
                        masculine = def_masculine

                    if first_def:
                        if not words.wordlist.is_feminized_noun(word):
                            dprint(f"ERROR: NOHEAD {word} uses feminine noun/equivalent of in first definition, but does not declare masculine noun in es-noun")
                            meta_type = "meta-noun"
                            meta_data = {"m": [masculine]}

                    else:
                        dprint(f"INFO: {word} uses feminine noun, but not in its first definition {prev_fem}")

                if masculine:
                    other_fem = words.wordlist.get_feminine_noun(masculine)
                    if not other_fem:
                        dprint(f"NOTICE: {word} has unrequited partner: {masculine}")
                    elif other_fem != word:
                        dprint(f"FIXME: {word} has unfaithful partner: {masculine}/{other_fem}")

                prev_fem = word

            # Replace "obsolete form of" et al with a lemma to the good word
            # but only if it's the first definition
            match = re.match(ignore_pattern, definition)
            if match:
                definition = ""
                if prev_word != word or prev_pos != pos:
                    lemma = match.group(2).strip()
                    meta_type = f"meta-lemma-{pos}"
                    meta_data = {"lemma": [lemma]}

            notes = { n.strip() for n in note.lower().split(',') }

            # strip definitions that are noted as obsolete
            if ignore_notes & notes:
                definition = ""

            prev_pos = pos
            prev_word = word

            if not pos.startswith("meta-"):
                definition = definition.strip()
                if definition != "":
                    linedata = [ word, "{"+pos+"}" ]
                    if note:
                        linedata.append (f"[{note}]")
                    if syn:
                        linedata.append(f"| {syn}")
                    linedata.append(f":: {definition}")
                    print_line(linedata)
                if meta_type:
                    print_meta(word, meta_type, meta_data)
                continue

            data = words.wordlist.parse_tags(definition)
            print_useful_meta(word, pos, data)

            if word not in seen:
                seen[word] = {}
            if pos not in seen[word]:
                seen[word][pos] = definition
            else:
                dprint(f"NOTICE: Multiple definitions for {word} {pos} {seen[word][pos]}/{definition}")


if __name__ == "__main__":

    import argparse
    global _args

    parser = argparse.ArgumentParser(description='Check and clean wiktionary dump')
    parser.add_argument('infile', help="Input file")
    parser.add_argument('--dry-run', help="Don't print output line", action="store_true")
    parser.add_argument('--debug', help="Print cleanup information about messy items", action="store_true")
    parser.add_argument('--dictionary', help="Dictionary file name (DEFAULT: es-en.txt)")
    parser.add_argument('--sentences', help="Sentences file name (DEFAULT: sentences.tsv)")
    parser.add_argument('--data-dir', help="Directory contaning the dictionary (DEFAULT: SPANISH_DATA_DIR environment variable or 'spanish_data')")
    parser.add_argument('--custom-dir', help="Directory containing dictionary customizations (DEFAULT: SPANISH_CUSTOM_DIR environment variable or 'spanish_custom')")
    args = parser.parse_args()

    if not args.dictionary:
        args.dictionary="es-en.txt"

    if not args.sentences:
        args.sentences="sentences.tsv"

    if not args.data_dir:
        args.data_dir = os.environ.get("SPANISH_DATA_DIR", "spanish_data")

    if not args.custom_dir:
        args.custom_dir = os.environ.get("SPANISH_CUSTOM_DIR", "spanish_custom")

    _args = parser.parse_args()

    main()
