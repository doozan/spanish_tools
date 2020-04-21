import spanish_words
import spanish_sentences
import spanish_lemmas
import sys

def dprint(debug, *args, **kwargs):
    if debug:
        print(*args, file=sys.stderr, **kwargs)


def get_pos_overlap(word, debug=False):
    lemmadb_pos = spanish_lemmas.get_all_pos(word)
    lemmadb_pos = set(lemmadb_pos) if lemmadb_pos and len(lemmadb_pos) else set()
    sentences_pos = set(map(str.upper, spanish_sentences.get_all_pos(word)))
    dictionary_pos = set(spanish_words.get_all_pos(word))

    dprint(debug, word, "lemmadb: ", lemmadb_pos)
    dprint(debug, word, "sentences: ", sentences_pos)
    dprint(debug, word, "words: ", dictionary_pos)

    # the sentences pulls from the same dataset (treetagger) as the lemmas, so agreement between the lemmadb and sentencesdb isn't worth much
    # however, the sentences database has better context than the lemmadb and will sometimes have more results
    # so it's good to check the dictionary against the lemmadb and the sentencesdb when looking for matches

    all_pos = sorted(lemmadb_pos & sentences_pos & dictionary_pos)

    if not len(all_pos):
        all_pos = (dictionary_pos & lemmadb_pos) | (dictionary_pos & sentences_pos)

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


def get_best_pos(word, debug=False):
    # order here does not matter because every item will be assessed and scored
    # and the highest score will be selected
    #search_lemmas = ["", "ADJ", "NOUN", "VERB"]

    search_lemmas = get_lemma_pos(word)
    dprint(debug, "Searching: ", search_lemmas)

    check_pos = []
    for pos in spanish_lemmas.get_all_pos(word):
        if pos not in check_pos:
            check_pos.append(pos)

    for lemma_pos in search_lemmas:
        lemma = spanish_words.get_lemma(word, lemma_pos)

        all_pos = get_pos_overlap(lemma, debug)

        if not all_pos or not len(all_pos):
            dprint(debug, "no overlapping usage for %s as a %s"%(lemma, lemma_pos))
            continue

        #dprint(debug, "getting weights for (%s %s %s): %s"%(word,lemma_pos, lemma, all_pos))
        dprint(debug, "getting weights for (%s %s %s): %s"%(word,lemma_pos, lemma, check_pos))

        # If there are multiple options, prefer the one with most sentence usage
        # skews us towards the tagging mistakes in the sentences (eg "placer" is
        # usually mis-tagged as a verb instead of a noun and will return "verb")
        pos  = ""
#        if len(all_pos) == 1:
#            pos = list(all_pos)[0]
#        elif len(all_pos) > 1:
#            dprint(debug, "tie breaker")
#            pos = spanish_sentences.get_best_pos(lemma, all_pos)
        pos = spanish_sentences.get_best_pos(lemma, check_pos)
        dprint(debug, "result = ",pos)

        if pos:
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
#            dprint(debug, "NONE:", word)
    return "NONE"
