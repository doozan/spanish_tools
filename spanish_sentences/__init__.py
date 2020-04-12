#import random
import sys
import math
import re
import os
import spanish_lemmas

grepdb = []
worddb = []
sentencedb = []
tagdb = {}
worddb = {}

_tagfile = os.path.join(os.path.dirname(__file__), 'spa-tagged.txt')

if not os.path.isfile(_tagfile):
    print("Cannot find tagged data, run build_sentences.py first")
    exit(1)


def strip_sentence(string):
    stripped = re.sub('[^ a-zA-ZáéíñóúüÁÉÍÑÓÚÜ]+', '', string).lower()
    return re.sub(' +', ' ', stripped)


# tags usually look like noun:word
# but can also look look noun:word1|word1|word2

def add_tag_to_db(tag,index):
    pos,word = tag.split(":")

    for word in set(word.split("|")):
        if word not in tagdb:
            tagdb[word] = {}

        if pos not in tagdb[word]:
            tagdb[word][pos] = [index]
        else:
            tagdb[word][pos].append(index)

def init_sentences():
    index=0
    with open(_tagfile) as infile:
        for line in infile:
            english, spanish, tagged, extras = line.split("\t",4)
            stripped = strip_sentence(spanish).strip()
            tagged = tagged.strip()

            sentencedb.append( (spanish, english) )
            grepdb.append(stripped)

            for word in stripped.split(" "):
                if word not in worddb:
                    worddb[word] = [index]
                else:
                    worddb[word].append(index)

            for tag in tagged.split(" "):
                add_tag_to_db(tag,index)
            index+=1

def get_sentences_from_phrase(phrase, count):
    pattern = r"\b" + phrase.strip().lower() + r"\b"

    matches = []
    index = 0
    for item in grepdb:
        if re.search(pattern, item):
            matches.append(index)
        index+=1

    return get_sentences_from_index(matches, count)

def get_sentences_from_word(word, count):

    index = []
    if word in worddb:
        index = worddb[word]

    else:
        results = get_sentences_from_tag(word, "", count)
        if results:
            return results

        lemma = spanish_lemmas.get_lemma(word, "")
        if lemma and lemma in worddb:
            index = worddb[lemma]

    if len(index):
        return get_sentences_from_index(index, count)
    return []

def get_sentences_from_tag(word, pos, count):

    found_word = ""
    if word in tagdb:
        found_word = word
    else:
        lemma = spanish_lemmas.get_lemma(word, pos)
        if lemma and lemma in tagdb:
            found_word = lemma
        else:
            return []

    results = set()
    if not pos:
        for item in tagdb[found_word]:
            results.update(tagdb[found_word][item])
    elif pos in tagdb[found_word]:
        results = tagdb[found_word][pos]
    else:
        return []

    return get_sentences_from_index(list(results), count)


def get_sentences_from_index(available,count):
    sentences = []
    ids = []

    available = sorted(available)

    results = len(available)
    if results <= count:
        ids = range(0,results)
    else:
        step = results/(count+1.0)

        # select sentences over an even distribution of the range
        ids = [ math.ceil((i+1)*step) for i in range(count) ]

# Randomly select sentences
#        while count>0:
#            rnd = random.randint(0,results)-1
#            if rnd in ids:
#                continue
#            ids.append(rnd)
#            count-=1
#        ids = sorted(ids)

    for idx in ids:
        sentences.append(sentencedb[available[idx]])

    return(sentences)

def clean_word(word):
    word = re.sub("^el ", "", word)
    word = re.sub("^la(s) ", "", word)
    word = re.sub(";.*", "", word)
    word = re.sub(",.*", "", word)
    if " " in word:
        word = re.sub("^.{1,3} ", "", word)
        word = re.sub(" .{1,3}$", "", word)
    return word


def get_sentences(lookup, pos, count):
    results = []
    source = "exact"

    if pos in [ "phrase" ]:
        results = get_sentences_from_phrase(lookup, count)
    else:
        word = clean_word(lookup)
        results = get_sentences_from_tag(word, pos, count)

        if not len(results):
            source = "fuzzy"
            results = get_sentences_from_word(word, count)

    return { "sentences": results, "matched": source }



init_sentences()
