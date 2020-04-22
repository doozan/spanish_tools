#import random
import sys
import math
import re
import os
import spanish_words

grepdb = []
sentencedb = []
tagdb = {}

_tagfile = os.path.join(os.path.dirname(__file__), 'spa-tagged.txt')

if not os.path.isfile(_tagfile):
    print("Cannot find tagged data, run build_sentences.py first")
    exit(1)


def strip_sentence(string):
    stripped = re.sub('[^ a-zA-ZáéíñóúüÁÉÍÑÓÚÜ]+', '', string).lower()
    return re.sub(' +', ' ', stripped)

def get_interjections(string):

    pattern = r"""(?x)(?=          # use lookahead as the separators may overlap (word1. word2, blah blah) should match word1 and word2 using "." as a separator
        (?:^|[:;,.¡!¿]\ ?)         # Punctuation (followed by an optional space) or the start of the line
        ([a-zA-ZáéíñóúüÁÉÍÑÓÚÜ]+)  # the interjection
        (?:[;,.!?]|$)              # punctuation or the end of the line
    )"""
    return re.findall(pattern, string, re.IGNORECASE)


# tags usually look like noun:word
# but can also look look noun:word1|word1|word2

def add_tag_to_db(tag,index):
    pos,word = tag.split(":")

    for word in list(dict.fromkeys(word.split("|"))):
        word = word.lower()
        if word not in tagdb:
            tagdb[word] = {}

        if pos not in tagdb[word]:
            tagdb[word][pos] = []

        tagdb[word][pos].append(index)



def tag_interjections(sentence, index):
    for word in get_interjections(sentence):
        add_tag_to_db("interj:"+word, index)

def init_sentences():
    index=0
    with open(_tagfile) as infile:
        for line in infile:
            english, spanish, tagged, extras = line.split("\t",4)
            stripped = strip_sentence(spanish).strip()
            tagged = tagged.strip()

            tag_interjections(spanish, index)
            sentencedb.append( (spanish, english) )
            grepdb.append(stripped)

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
    "verb": [ "verb", "adj", "adv", "noun" ],
    "adj":  [ "adj", "adv" ],
    "adv":  [ "adv", "adj" ]
}

def get_ids_fuzzy(word, pos):

    ids = []
    search_pos = []

    if pos == "interj":
        return []

    if pos in fuzzy_pos_search:
        search_pos = fuzzy_pos_search[pos]
    else:
        search_pos = [ pos ]

    for p in search_pos:
        lemma = spanish_words.get_lemma(word, p)
        ids += get_ids_from_tag(lemma, p)

    return sorted(set(ids))

def get_ids_from_word(word):
    return get_ids_from_tag("@"+word, "")


# if pos is set it return only results matching that word,pos
# if it's not set, return all results matching the keyword
def get_ids_from_tag(word, pos):

    lemma = ""
    if word in tagdb:
        lemma = word
    else:
        lemma = spanish_words.get_lemma(word, pos)
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


def get_sentence_ids(lookup, pos):
    ids = []
    lookup = lookup.strip().lower()
    pos = pos.lower()
    source = "exact"

    if pos in [ "phrase" ] or " " in lookup:
        ids = get_ids_from_phrase(lookup)
    else:
        word = clean_word(lookup)
        ids = get_ids_from_tag(word, pos)

        if not len(ids):
            source = "literal"
            if pos != "INTERJ":
                ids = get_ids_from_word(word)

            if not len(ids):
                source = "fuzzy"
                ids = get_ids_fuzzy(word, pos)
    return { "ids": ids, "source": source }

def get_sentences(lookup, pos, count):
    res = get_sentence_ids(lookup, pos)
    sentences = get_sentences_from_ids(res['ids'], count)
    return { "sentences": sentences, "matched": res['source'] }


def get_all_pos(word):
    word = word.lower()
    if word in tagdb:
        return list(tagdb[word].keys())
    return []


def get_best_pos(word, all_pos=None, debug=False):
    word = word.lower()


    best_pos = ""
    best_count = -1
    if word in tagdb:
        if not all_pos:
            all_pos = tagdb[word]
        for pos in all_pos:
            pos = pos.lower()
            if pos in tagdb[word]:
                count = len(tagdb[word][pos])
                if debug:
                    print(count,word,pos)
                if count > best_count:
                    best_pos = pos
                    best_count = count
            elif debug:
                print(0,word,pos)

    return { 'count': best_count, 'pos': best_pos }





init_sentences()
