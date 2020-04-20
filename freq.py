import glob
import csv
import re
import os
import sys
import argparse
import spanish_words
import spanish_sentences
import spanish_lemmas

parser = argparse.ArgumentParser(description='Lemmatize frequency list')
parser.add_argument('file', help="Frequency list")
parser.add_argument('outfile', help="CSV file to create")
args = parser.parse_args()


lemmapos2pos = {
'PREP': 'PREP',
'ADJ': 'ADJ',
'ADV': 'ADV',
'NC': 'NOUN',
'NP': 'NP',
'VCLIfin': 'VERB',
'VCLIger': 'VERB',
'VCLIinf': 'VERB',
'VEadj': 'VERB',
'VEfin': 'VERB',
'VEger': 'VERB',
'VEinf': 'VERB',
'VHadj': 'VERB',
'VHfin': 'VERB',
'VHger': 'VERB',
'VLadj': 'VERB',
'VLfin': 'VERB',
'VLger': 'VERB',
'VLinf': 'VERB',
'VMadj': 'VERB',
'VMfin': 'VERB',
'VMger': 'VERB',
'VMinf': 'VERB',
'VSadj': 'VERB',
'VSfin': 'VERB',
'VSger': 'VERB',
'VSinf': 'VERB',
}


def get_best_pos(word):
    lemmadb_pos = spanish_lemmas.get_all_pos(word)
    lemmadb_pos = set(lemmadb_pos) if lemmadb_pos and len(lemmadb_pos) else set()
    sentences_pos = set(map(str.upper, spanish_sentences.get_all_pos(word)))
    dictionary_pos = set(spanish_words.get_all_pos(word))

    all_pos = lemmadb_pos & sentences_pos & dictionary_pos
    if not len(all_pos):
        all_pos = sentences_pos & dictionary_pos

    if not len(all_pos):
        all_pos = lemmadb_pos & dictionary_pos

    if not len(all_pos):
        all_pos = lemmadb_pos & sentences_pos

    if not len(all_pos):
        if len(dictionary_pos):
            all_pos = dictionary_pos
        elif len(sentences_pos):
            all_pos = sentences_pos
        elif len(lemmadb_pos):
            all_pos = lemmadb_pos

    pos  = ""
    if len(all_pos):
        pos = spanish_sentences.get_best_pos(word, all_pos)


    if pos == "":
        all_pos = lemmadb_pos | sentences_pos | dictionary_pos
#        pos = "NONE"
        best_pos = ""
        best_count = -1
        for pos in all_pos:
            lemma = spanish_words.get_lemma(word, pos)
            count = len(spanish_sentences.get_ids_from_tag(lemma, pos.lower()))
            if count > best_count:
                best_count = count
                best_pos = pos

#            all_results += str(count)+":"+pos


        if best_pos == "":
            #print("No great pos", word)
            pos = "NONE"
        else:
            pos = best_pos

    return pos


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
    'FILLER': "Common filler word",
    'NODEF': "No definition",
    'NOSENT': "No sentences",
    "FUZZY": "Only has fuzzy sentance matches",
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
    if pos == "UNKNOWN":
        flags.append(flag("UNKNOWN"))

    if pos == "NONE":
        flags.append(flag("NOUSAGE"))


    definition = spanish_words.lookup(word, pos)
    if not definition:
        flags.append(flag("NODEF"))

    res = spanish_sentences.get_sentences(word,pos,1)
    if not len(res['sentences']):
        flags.append(flag("NOSENT"))

    else:
        if res['matched'] != "exact":
            flags.append(flag("FUZZY"))

    # remove reflexive verbs if the non-reflexive verb is already on the list
    if word.endswith("rse") and pos == "VERB" and "VERB:"+word[:-2] in wordlist:
        flags.append(flag("DUPLICATE-REFLEXIVE"))

    return flags



wordlist = {}
def build_wordlist():

    wordusage = {}
    for k,v in sorted(freq.items(), key=lambda item: item[1]['count'], reverse=True):
        pos,word = k.split(":")

        if word not in wordusage:
            wordusage[word] = []
        wordusage[word].append(pos)

    count = 1
    for k,item in sorted(freq.items(), key=lambda item: item[1]['count'], reverse=True):
        pos,word = k.split(":")

        flags = get_word_flags(word, pos)
        # flag the most common "filler" words (pronouns, articles, etc)
        if count<200 and pos not in [ "ADJ", "ADV", "NOUN", "VERB" ]:
            flags.append(flag("FILLER"))

        wordlist[pos+":"+word] = {
            'count': count,
            'word': word,
            'pos': pos,
            'flags': flags,
            'usage': item['usage']
        }

#        print(count,pos,word)
        count += 1

    repeatusage = {}
    for word in wordusage:
        if len(wordusage[word]) > 1:
            repeatusage[word] = wordusage[word]

    for word,all_pos in repeatusage.items():
        if "ADJ" in all_pos and "ADV" in all_pos:
            wordlist["ADV:"+word]['flags'].append(flag("DUPLICATE-ADJ-ADV"))
        if "ADJ" in all_pos and "NOUN" in all_pos:
            wordlist["NOUN:"+word]['flags'].append(flag("DUPLICATE-ADJ-NOUN"))
#        for pos in all_pos:
#            if pos not in ["ADJ", "ADV", "NOUN"]:
#                wordlist[pos+":"+word]['flags'].append("REPEAT-"+ "-".join(all_pos))



with open(args.file) as infile, open(args.file+".lemmas.csv",'w') as outfile:
#with open(args.file) as infile, open(args.outfile,'w') as outfile:
    csvwriter = csv.writer(outfile)
    csvwriter.writerow(["count", "word", "lemma", "pos"])
    for line in infile:
        word, count = line.strip().split(' ')

        pos = get_best_pos(word).upper()
        lemma = spanish_words.get_lemma(word, pos)
        add_count(lemma, pos, count, word)

        csvwriter.writerow([count,word,lemma,pos])

#exit()

build_wordlist()

with open(args.outfile,'w') as outfile:
    csvwriter = csv.writer(outfile)
    csvwriter.writerow(["Count", "Word", "Part of Speech","Flags","Usage"])

    for k,item in sorted(wordlist.items(), key=lambda item: item[1]['count']):
        if len(item['flags']) == 1 and "FUZZY" in item['flags']:
            item['flags'].append("CLEAR")

        if not len(item['flags']):
            item['flags'].append("CLEAR")
        csvwriter.writerow([item['count'],item['word'],item['pos'],"; ".join(item['flags']),"|".join(item['usage'])])

#print(str(v).rjust(12) + "  " + k) 

