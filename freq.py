import glob
import csv
import re
import os
import sys
import argparse
import spanish_words
import spanish_sentences
import get_best_pos

parser = argparse.ArgumentParser(description='Lemmatize frequency list')
parser.add_argument('file', help="Frequency list")
parser.add_argument('outfile', help="CSV file to create")
args = parser.parse_args()

words = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt", synonyms="spanish_data/synonyms.txt", iverbs="spanish_data/irregular_verbs.txt")
sentences = spanish_sentences.sentences(words, "spanish_data/spa-tagged.txt")

freq = {}
def add_count(word, pos, count, origword):
    tag = pos+":"+word
    if tag not in freq:
        freq[tag] = { 'count': 0, 'usage': [] }

    freq[tag]['count'] += int(count)
    freq[tag]['usage'].append(count+":"+origword)

flags_defs = {
    'UNKNOWN': "Word does not appear in lemma database or dictionary",
    'NOUSAGE': "Multiple POS, but no sentences for any usage",
    'PRONOUN': "Ignoring pronouns",
    'FILLER': "Common filler word",
    'LETTER': "Letter",
    'NODEF': "No definition",
    'NOSENT': "No sentences",
    "FUZZY": "Only has fuzzy sentance matches",
    "DUPLICATE": "Duplicate usage of word with different POS",
    "DUPLICATE-ADJ-ADV": "Adverb duplicates existing adjective",
    "DUPLICATE-ADJ-NOUN": "Noun duplicates existing adjective",
    "DUPLICATE-REFLEXIVE": "Reflexive verb duplicase existing non-reflexive verb"
}



def flag(name):
    return name
#+ ": " + flags_defs[name]
#    return name + ": " + flags_defs[name]


def get_word_flags(word,pos):
    flags = []
    pos = pos.lower()
    if pos == "unknown":
        flags.append(flag("UNKNOWN"))

    if pos == "none":
        flags.append(flag("NOUSAGE"))

    if pos == "pron":
        flags.append(flag("PRONOUN"))

    if pos == "letter":
        flags.append(flag("LETTER"))


    definition = words.lookup(word, pos)
    if not definition:
        flags.append(flag("NODEF"))

    res = sentences.get_sentences(word,pos,1)
    if not len(res['sentences']):
        flags.append(flag("NOSENT"))

    else:
        if res['matched'] != "exact":
            flags.append(flag("FUZZY"))

    # remove reflexive verbs if the non-reflexive verb is already on the list
    if word.endswith("rse") and pos == "verb" and "verb:"+word[:-2] in wordlist:
        flags.append(flag("DUPLICATE-REFLEXIVE"))

    return flags



wordlist = {}
def build_wordlist():

    wordusage = {}
    count = 1
    for k,item in sorted(freq.items(), key=lambda item: item[1]['count'], reverse=True):
        pos,word = k.split(":")

        flags = get_word_flags(word, pos)
        # flag the most common "filler" words (pronouns, articles, etc)
        if count<200 and pos not in [ "adj", "adv", "noun", "verb" ]:
            flags.append(flag("FILLER"))

        # Check for repeat usage
        if word not in wordusage:
            wordusage[word] = {}
#        else:
#            flags.append("DUPLICATE")

        wordusage[word][pos] = item['count']

        wordlist[k] = {
            'count': count,
            'word': word,
            'pos': pos,
            'flags': flags,
            'usage': item['usage']
        }

        count += 1

    repeatusage = {}
    for word in wordusage:
        if len(wordusage[word].keys()) > 1:
            repeatusage[word] = wordusage[word]

    for word,all_pos in repeatusage.items():
        best_count = -1
        best_pos = ""
        for pos,count in all_pos.items():
            if count > best_count:
                best_count = count
                best_pos = pos

        popular_pos = []
        for pos,count in all_pos.items():
            if count<(best_count/2):
                wordlist[pos+":"+word]['flags'].append("LESSUSED-"+ "-".join(all_pos))
            else:
                popular_pos.append(pos)

        if "adj" in popular_pos and "adv" in popular_pos:
            wordlist["adv:"+word]['flags'].append(flag("DUPLICATE-ADJ-ADV"))
        if "adj" in popular_pos and "noun" in popular_pos:
            wordlist["noun:"+word]['flags'].append(flag("DUPLICATE-ADJ-NOUN"))



with open(args.file) as infile, open(args.file+".lemmas.csv",'w') as outfile:
#with open(args.file) as infile, open(args.outfile,'w') as outfile:
    csvwriter = csv.writer(outfile)
    csvwriter.writerow(["count", "word", "lemma", "pos"])
    for line in infile:
        word, count = line.strip().split(' ')

        pos = get_best_pos.get_best_pos(word, words, sentences)
        lemma = words.get_lemma(word, pos)
        add_count(lemma, pos, count, word)

        csvwriter.writerow([count,word,lemma,pos])

#exit()

build_wordlist()

with open(args.outfile,'w') as outfile:
    csvwriter = csv.writer(outfile)
    csvwriter.writerow(["rank", "spanish", "pos","flags","usage"])

    for k,item in sorted(wordlist.items(), key=lambda item: item[1]['count']):
        if len(item['flags']) == 1 and "FUZZY" in item['flags']:
            item['flags'].append("CLEAR")

        if not len(item['flags']):
            item['flags'].append("CLEAR")
        csvwriter.writerow([item['count'],item['word'],item['pos'],"; ".join(item['flags']),"|".join(item['usage'])])

#print(str(v).rjust(12) + "  " + k) 

