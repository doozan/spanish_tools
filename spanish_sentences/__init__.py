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

def get_ids_from_phrase(phrase):
    pattern = r"\b" + phrase.strip().lower() + r"\b"

    matches = []
    index = 0
    for item in grepdb:
        if re.search(pattern, item):
            matches.append(index)
        index+=1

    return matches



fuzzy_pos_search = {
    "VERB": [ "VERB", "ADJ", "ADV", "NOUN" ],
    "ADJ":  [ "ADJ", "ADV" ],
    "ADV":  [ "ADV", "ADJ" ]
}

def get_ids_fuzzy(word, pos):

    ids = []
    search_pos = []
    if pos in fuzzy_pos_search:
        search_pos = fuzzy_pos_search[pos]
    else:
        search_pos = [ pos ]

    for p in search_pos:
        lemma = spanish_lemmas.get_lemma(word, p)
        ids += get_ids_from_tag(lemma, p)
        if lemma and lemma in worddb:
           ids += worddb[lemma]

    return sorted(set(ids))

def get_ids_from_word(word):

    index = []
    if word in worddb:
        index = worddb[word]

    return index



# if pos is set it return only results matching that word,pos
# if it's not set, return all results matching the keyword
def get_ids_from_tag(word, pos):

    lemma = ""
    if word in tagdb:
        lemma = word
    else:
        lemma = spanish_lemmas.get_lemma(word, pos)
        if not lemma or not lemma in tagdb:
            return []

    results = set()
    if not pos:
        for item in tagdb[lemma]:
            results.update(tagdb[lemma][item])
    elif pos in tagdb[lemma]:
        results = tagdb[lemma][pos]
    else:
        return []

    return list(results)


def get_sentences_from_ids(available, count):
    sentences = []
    ids = []

    # strip duplicates and sort
    available = sorted(list(set(available)))

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
    return word.strip()

#    word = re.sub("^el ", "", word)
#    word = re.sub("^la(s) ", "", word)
#    word = re.sub(";.*", "", word)
#    word = re.sub(",.*", "", word)
#    if " " in word:
#        word = re.sub("^.{1,3} ", "", word)
#        word = re.sub(" .{1,3}$", "", word)
#    return word


def get_sentences(lookup, pos, count):
    ids = []
    lookup = lookup.lower()
    pos = pos.lower()
    source = "exact"

    if pos in [ "phrase" ] or " " in lookup:
        ids = get_ids_from_phrase(lookup)
    else:
        word = clean_word(lookup)
        ids = get_ids_from_tag(word, pos)

        if not len(ids):
            source = "literal"
            ids = get_ids_from_word(word)

            if not len(ids):
                source = "fuzzy"
                ids = get_ids_fuzzy(word, pos)

    sentences = get_sentences_from_ids(ids, count)
    return { "sentences": sentences, "matched": source }



init_sentences()
