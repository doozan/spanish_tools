#!/usr/bin/python3
# -*- python-mode -*-

import argparse
import os
import re
import sys

from spanish_words import SpanishWords

words = None


pages = {}
all_forms = {}


def add_form_target(form, word):
    if form not in all_forms:
        all_forms[form] = {word}
    else:
        all_forms[form].add(word)


def get_verb_forms(word):
    return set( k for forms in words.verb.conjugate(word).values() for k in forms if k is not None )

def get_word_forms(word, pos):
    pos = words.common_pos(pos)
    if pos == "verb":
        return get_verb_forms(word)

    if word in words.wordlist.wordforms:
        all_forms = words.wordlist.wordforms[word]
        all_forms.add( (pos,word) )
        return [ form for fpos,form in words.wordlist.wordforms[word] if fpos==pos ]

    return [word]

def get_word_data(word):
    data = words.wordlist.allwords.get(word)
    if not data:
        raise ValueError(f"No data for {word}")

    items = []
    for pos, posdata in data.items():
        items.append(f"{word} ({pos})")
        for label,defs in posdata.items():
            for i,definition in enumerate(defs,1):
                line = []
                line.append(f"{i}.")
                if label:
                    line.append(label)
                line.append(definition)
                items.append(" ".join(line))
    return "\n".join(items)

def build_page(targets):
#    if len(targets) == 1:
#        get_word_data(targets[0])
#
#    # make a disambiguation page with definitions for each possible target
#    data = []
#    for target in targets:
#        data.append(target)
#        data.append(get_word_data(target))
#
#    if len(targets) > 1:
    return "\n----\n\n".join(get_word_data(target) for target in targets)

all_pages = {}
def add_key(key, targets):
    target = "::".join(targets)
    if target not in all_pages:
        all_pages[target] = {
            "keys": [key],
            "data": build_page(targets)
        }
    else:
        all_pages[target]["keys"].append(key)

def print_pages():
    header = """\
_____
00-database-info
##:name:Wiktionary.org Spanish-English
##:url:en.wiktionary.org"""
    print(header)

    for pagename,page in sorted(all_pages.items()):
        print("_____")
        #print(page["keys"][0])
        print("|".join(page["keys"]))
        print(page["data"])

def export_dictionary():

    for word, data in words.wordlist.allwords.items():
        for pos, groups in data.items():
            for form in get_word_forms(word, pos):
                add_form_target(form, word)

    all_targets = set()
    disambig = set()
    ambig_forms = 0
    for form, targets in all_forms.items():
        if len(targets) > 1:
            ambig_forms += 1
            disambig.add(tuple(targets))
            for target in targets:
                all_targets.add(target)
        else:
            all_targets.add(next(iter(targets)))
        add_key(form, tuple(targets))

    print_pages()


#    print(len(words.wordlist.allwords), "all words")
#    print(len(all_forms), "all forms")
#    print(ambig_forms, "ambiguous forms")
#    print(len(disambig), "disambiguation targets")
#    print(len(all_targets), "targets")
#
#    no_targets = words.wordlist.allwords.keys() - all_targets
#
#    print(list(no_targets)[1:100])
#    print(len(no_targets), "missing forms")




def main():
    global words

    parser = argparse.ArgumentParser(description="Get definition of word")
    parser.add_argument("--dictionary", help="Dictionary file name (DEFAULT: es-en.txt)", default="es-en.txt")
    parser.add_argument(
        "--data-dir",
        help="Directory contaning the dictionary (DEFAULT: SPANISH_DATA_DIR environment variable or 'spanish_data')",
    )
    parser.add_argument(
        "--custom-dir",
        help="Directory containing dictionary customizations (DEFAULT: SPANISH_CUSTOM_DIR environment variable or 'spanish_custom')",
    )
    args = parser.parse_args()

    if not args.data_dir:
        args.data_dir = os.environ.get("SPANISH_DATA_DIR", "spanish_data")

    if not args.custom_dir:
        args.custom_dir = os.environ.get("SPANISH_CUSTOM_DIR", "spanish_custom")

    words = SpanishWords(
        dictionary=args.dictionary, data_dir=args.data_dir, custom_dir=args.custom_dir
    )

    export_dictionary()

main()
