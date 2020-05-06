#!/usr/bin/python3
# -*- python-mode -*-

import argparse
import os
import re
import json
import treetaggerwrapper
import spanish_words

parser = argparse.ArgumentParser(description='Tag spanish sentences')
parser.add_argument('infile', help="File to read")
args = parser.parse_args()

if not os.path.isfile(args.infile):
    raise FileNotFoundError(f"Cannot open: {args.infile}")

tagger = treetaggerwrapper.TreeTagger(TAGLANG='es')#,TAGDIR="~/Downloads/treetagger/")
words = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt", synonyms="spanish_data/synonyms.txt")

tag2pos = {
'ACRNM': "", # acronym (ISO, CEI)
'ADJ': "adj", # Adjectives (mayores, mayor)
'ADV': "adv", # Adverbs (muy, demasiado, cómo)
'ALFP': "", # Plural letter of the alphabet (As/Aes, bes)
'ALFS': "", # Singular letter of the alphabet (A, b)
'ART': "", # Articles (un, las, la, unas)
'BACKSLASH': "", # backslash (\)
'CARD': "num", # Cardinals
'CC': "conj", # Coordinating conjunction (y, o)
'CCAD': "conj", # Adversative coordinating conjunction (pero)
'CCNEG': "conj", # Negative coordinating conjunction (ni)
'CM': "", # comma (,)
'CODE': "", # Alphanumeric code
'COLON': "", # colon (:)
'CQUE': "conj", # que (as conjunction)
'CSUBF': "conj", # Subordinating conjunction that introduces finite clauses (apenas)
'CSUBI': "conj", # Subordinating conjunction that introduces infinite clauses (al)
'CSUBX': "conj", # Subordinating conjunction underspecified for subord-type (aunque)
'DASH': "", # dash (-)
'DM': "pron", # Demonstrative pronouns (ésas, ése, esta)
'DOTS': "", # POS tag for "..."
'FO': "", # Formula
'FS': "", # Full stop punctuation marks
'INT': "", # Interrogative pronouns (quiénes, cuántas, cuánto)
'ITJN': "interj", # Interjection (oh, ja)
'LP': "", # left parenthesis ("(", "[")
'NC': "noun", # Common nouns (mesas, mesa, libro, ordenador)
'NEG': "", # Negation
'NMEA': "noun", # measure noun (metros, litros)
'NMON': "noun", # month name
'NP': "propnoun", # Proper nouns
'ORD': "adj", # Ordinals (primer, primeras, primera)
'PAL': "", # Portmanteau word formed by a and el
'PDEL': "", # Portmanteau word formed by de and el
'PE': "", # Foreign word
'PERCT': "", # percent sign (%)
'PNC': "", # Unclassified word
'PPC': "pron", # Clitic personal pronoun (le, les)
'PPO': "pron", # Possessive pronouns (mi, su, sus)
'PPX': "pron", # Clitics and personal pronouns (nos, me, nosotras, te, sí)
'PREP': "prep", # Negative preposition (sin)
'PREP': "prep", # Preposition
'PREP/DEL': "prep", #  Complex preposition "después del"
'QT': "", # quotation symbol (" ' `)
'QU': "adj", # Quantifiers (sendas, cada)
'REL': "pron", # Relative pronouns (cuyas, cuyo)
'RP': "", # right parenthesis (")", "]")
'SE': "", # Se (as particle)
'SEMICOLON': "", # semicolon (;)
'SLASH': "", # slash (/)
'SYM': "", # Symbols
'UMMX': "", # measure unit (MHz, km, mA)
'VCLIger': "verb", #  clitic gerund verb
'VCLIinf': "verb", #  clitic infinitive verb
'VCLIfin': "verb", #  clitic finite verb
'VEadj': "part", # Verb estar. Past participle
'VEfin': "verb", # Verb estar. Finite
'VEger': "verb", # Verb estar. Gerund
'VEinf': "verb", # Verb estar. Infinitive
'VHadj': "part", # Verb haber. Past participle
'VHfin': "verb", # Verb haber. Finite
'VHger': "verb", # Verb haber. Gerund
'VHinf': "verb", # Verb haber. Infinitive
'VLadj': "part", # Lexical verb. Past participle
'VLfin': "verb", # Lexical verb. Finite
'VLger': "verb", # Lexical verb. Gerund
'VLinf': "verb", # Lexical verb. Infinitive
'VMadj': "part", # Modal verb. Past participle
'VMfin': "verb", # Modal verb. Finite
'VMger': "verb", # Modal verb. Gerund
'VMinf': "verb", # Modal verb. Infinitive
'VSadj': "part", # Verb ser. Past participle
'VSfin': "verb", # Verb ser. Finite
'VSger': "verb", # Verb ser. Gerund
'VSinf': "verb", # Verb ser. Infinitive
}


mismatch = {}

def tag_to_pos(tag):

    if "\t" not in tag:
        return None
        return "__BADTAG__" #+tag+"-__"

    word,usage,oldlemma = tag.split("\t")

    pos = tag2pos[usage]
    if pos:
        pos = pos.lower()
        lemma = words.get_lemma(word, pos)
        if oldlemma != lemma:
            mismatch[oldlemma] = lemma
        if pos != "propnoun":
            word = word.lower()
            lemma = lemma.lower()

        return [ pos, lemma, "@"+word ] #+"|#"+usage

    return None


def get_tags(spanish):
    tags = tagger.tag_text(spanish)
#    print(tags)
    pos_tags = map(tag_to_pos, tags)

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



with open(args.infile) as infile:
    seen = {}
    print("[")
    first = True
    for line in infile:
        line = line.strip()
        english, spanish, credits = line.split("\t")
        tags = get_tags(spanish)
        if "__BADTAG__" in tags:
            continue

        wordcount = spanish.count(" ")+1

        # ignore simple sentences
        if len(tags) < 2:
            continue

        # ignore sentences with less than 6 or more than 15 spanish words
        if wordcount < 5 or wordcount > 15:
            continue

        # ignore duplicates
        if english in seen or spanish in seen:
            continue
        else:
            seen[english] = 1
            seen[spanish] = 1

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

        #spanish_tagged = " ".join(tags)
        #print("%s\t%s\t%s\t%s"%(english, spanish, spanish_tagged, credits))

    print("\n]")

#    print(mismatch)
