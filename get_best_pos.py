import spanish_words
import spanish_sentences
import spanish_lemmas
import sys


_debug=False
def set_debug(debug):
    global _debug
    _debug=debug

def dprint(*args, **kwargs):
    if _debug:
        print(*args, file=sys.stderr, **kwargs)


def get_pos_overlap(word):
    lemmadb_pos = spanish_lemmas.get_all_pos(word)
    lemmadb_pos = set(lemmadb_pos) if lemmadb_pos and len(lemmadb_pos) else set()
    sentences_pos = set(map(str.upper, spanish_sentences.get_all_pos(word)))
    dictionary_pos = set(spanish_words.get_all_pos(word))

    dprint(word, "lemmadb: ", lemmadb_pos)
    dprint(word, "sentences: ", sentences_pos)
    dprint(word, "words: ", dictionary_pos)

    # the sentences pulls from the same dataset (treetagger) as the lemmas, so agreement between the lemmadb and sentencesdb isn't worth much
    # however, the sentences database has better context than the lemmadb and will sometimes have more results
    # so it's good to check the dictionary against the lemmadb and the sentencesdb when looking for matches

    all_pos = sorted(lemmadb_pos & sentences_pos & dictionary_pos)

    if not len(all_pos):
        all_pos = sorted((dictionary_pos & lemmadb_pos) | (dictionary_pos & sentences_pos))

    return all_pos



# Get a list of possible POS types to use to lemmify the given word
# The list will include only the elements "", "VERB", "NOUN", "ADJ"
# and will preserve any ordering available in the spanish_lemmas db
def get_lemma_pos(word):

    search_lemmas = [""]
    lemmas = spanish_lemmas.get_all_pos(word)
    if lemmas and len(lemmas):
        search_lemmas += sorted(set(lemmas))

    for more_lemma in ["VERB", "NOUN", "ADJ"]:
        if more_lemma not in search_lemmas:
            search_lemmas.append(more_lemma)

    for lemma in search_lemmas:
        if lemma not in ["", "VERB", "NOUN", "ADJ"]:
            search_lemmas.remove(lemma)

    return search_lemmas


def get_dictionary_overlap(word, list_pos):
    good = []
    for pos in list_pos:
        lemma = spanish_words.get_lemma(word, pos)
        entry = spanish_words.lookup(lemma, pos)
        if entry and len(entry):
            good.append(pos)

    return good


def get_best_pos3(word):

    # get all possible POS usage for this word
    # cycle through all possible lemmas because words like "casas" won't
    # show up in the dictionary, but the lemma "casa" does
    all_lemmadb = []
    all_dict = []
    for pos in ["", "ADJ", "NOUN", "VERB"]:
        lemma = spanish_words.get_lemma(word, pos)
        all_lemmadb += spanish_lemmas.get_all_pos(lemma)
        all_dict +=  spanish_words.get_all_pos(lemma)


    # Limit search to words that are in the dictionary
    # Keep the set ordered by the position in the dictionary, to give preference
    # to the first entries in the dictionary
    common_pos = []
    for f in all_dict:
        if f in all_lemmadb and f not in common_pos:
            common_pos.append(f)

    if len(common_pos):

        # If there's only one, use it
        if len(common_pos) == 1:
            return list(common_pos)[0]

        # Get usage count of word as each possible POS
        dprint("Searching best use of %s in %s"%(word, common_pos))
        best_pos = spanish_sentences.get_best_pos("@"+word, common_pos, _debug)
        if best_pos and best_pos['count'] > 0:
            return best_pos['pos']

        dprint("No usage available, using first overlapping dictionary entry")
        for item in all_dict:
            if item in common_pos:
                return item

    # There is no overlapping usage between dictionary and lemmadb
    if len(all_dict):
        dprint("No overlapping use, deferring to first dictionary entry: ", all_dict)
        return all_dict[0]

    return "NONE"


def get_best_pos2(word):
    # order here does not matter because every item will be assessed and scored
    # and the highest score will be selected
    #search_lemmas = ["", "ADJ", "NOUN", "VERB"]



    lemmadb_pos = spanish_lemmas.get_all_pos(word)
    dprint("search_lemmas", lemmadb_pos)
    check_pos = sorted(get_dictionary_overlap(word, lemmadb_pos))
    dprint("check_pos", check_pos)



    # this is subject to positional bias since it takes the first matching result from the list of check_po
    # would it be better to get the weights for all items and then compare, or would that bias towards verbs?
    for lemma_pos in check_pos:
        lemma = "@"+word if lemma_pos == "" else spanish_words.get_lemma(word, lemma_pos)
        dprint("Searching best use of %s lemmatized as %s to %s in %s"%(word, lemma_pos, lemma,check_pos))


        best_pos = ""
        best_count = -1
        weight = spanish_sentences.get_best_pos(lemma, check_pos, _debug)
        if weight['count'] > best_count:
            best_count = weight['count']
            best_pos = weight['pos']

        if best_count > 0:
            return best_pos


    # At this point we've exhausted all possible matches for the word using the sentence database
    # so we're left gussing the "best" just using overlaps from the dictionary and the lemmadb

    for lemma_pos in check_pos:

        lemma = spanish_words.get_lemma(word, lemma_pos)
        all_pos = get_pos_overlap(lemma)

        if not all_pos or not len(all_pos):
            dprint("no overlapping usage for %s as a %s"%(lemma, lemma_pos))
            continue

        # just pick the first one, since we have no better way of guessing which is more useful
        return list(all_pos)[0]


    # There is no overlap between any sources for any available lemmmas
    # Search again using just the dictionary
    for lemma_pos in ["", "NOUN", "VERB", "ADJ"]:
        lemma = spanish_words.get_lemma(word, lemma_pos)
        dictionary_pos = spanish_words.get_all_pos(word)

        if len(dictionary_pos):
            return dictionary_pos[0]


    return "NONE"

def get_best_pos1(word):
    search_lemmas = get_lemma_pos(word)

    for lemma_pos in overlap:
        lemma = spanish_words.get_lemma(word, lemma_pos)

        all_pos = get_pos_overlap(lemma)

        if not all_pos or not len(all_pos):
            dprint("no overlapping usage for %s as a %s"%(lemma, lemma_pos))
            continue

        #dprint("getting weights for (%s %s %s): %s"%(word,lemma_pos, lemma, all_pos))

        # If there are multiple options, prefer the one with most sentence usage
        # skews us towards the tagging mistakes in the sentences (eg "placer" is
        # usually mis-tagged as a verb instead of a noun and will return "verb")
        pos  = ""
#        if len(all_pos) == 1:
#            pos = list(all_pos)[0]
#        elif len(all_pos) > 1:
#            dprint("tie breaker")
#            pos = spanish_sentences.get_best_pos(lemma, all_pos)
        check_pos = set(spanish_lemmas.get_all_pos(lemma)) | set(spanish_words.get_all_pos(lemma))
        dprint("getting weights for (%s %s %s): %s"%(word,lemma_pos, lemma, check_pos))
        pos = spanish_sentences.get_best_pos(lemma, check_pos)
        dprint("result = ",pos)

        if pos != "":
            return pos

    # There is no overlap between any sources for any available lemmmas
    # Search again using just the dictionary
    for lemma_pos in ["", "NOUN", "VERB", "ADJ"]:
        lemma = spanish_words.get_lemma(word, lemma_pos)
        dictionary_pos = spanish_words.get_all_pos(word)

        if len(dictionary_pos):
            return dictionary_pos[0]

#    if pos == "":
#            pos = "NONE"
#            dprint("NONE:", word)
    return "NONE"

def get_best_pos(word, debug=False):
    set_debug(debug)
    #return get_best_pos1(word)
    #return get_best_pos2(word)
    return get_best_pos3(word)

