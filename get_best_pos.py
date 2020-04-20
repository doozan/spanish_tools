import spanish_words
import spanish_sentences
import spanish_lemmas

def get_pos_overlap(word, debug=False):
    lemmadb_pos = spanish_lemmas.get_all_pos(word)
    lemmadb_pos = set(lemmadb_pos) if lemmadb_pos and len(lemmadb_pos) else set()
    sentences_pos = set(map(str.upper, spanish_sentences.get_all_pos(word)))
    dictionary_pos = set(spanish_words.get_all_pos(word))

    if debug:
        print(word, "lemmadb: ", lemmadb_pos)
        print(word, "sentences: ", sentences_pos)
        print(word, "words: ", dictionary_pos)

    # The dictionary usually has the best/most accurate data
    # The lemmadb is okay but not great, is a good source of "most common" usage
    # and the sentences data is often wrong
    # If there's an agreement between any of the datasets, assume it's likely a good usage

    all_pos = sorted(lemmadb_pos & sentences_pos & dictionary_pos)
    if not len(all_pos):
        if len(sentences_pos & dictionary_pos):
            print(word, sorted(sentences_pos & dictionary_pos), "has sentences and dictionary usage but no lemmadb")
#        all_pos = sentences_pos & dictionary_pos

    if not len(all_pos):
        all_pos = (lemmadb_pos & dictionary_pos) | (lemmadb_pos & sentences_pos)

    return all_pos



# Get a list of possible POS types to use to lemmify the given word
# The list will include only the elements "", "VERB", "NOUN", "ADJ"
# and will preserve any ordering available in the spanish_lemmas db
def get_lemma_pos(word):

    search_lemmas = [""]
    lemmas = spanish_lemmas.get_all_pos(word)
    if lemmas and len(lemmas):
        search_lemmas += sorted(lemmas)

    for more_lemma in ["VERB", "NOUN", "ADJ"]:
        if more_lemma not in search_lemmas:
            search_lemmas.append(more_lemma)

    for lemma in search_lemmas:
        if lemma not in ["", "VERB", "NOUN", "ADJ"]:
            search_lemmas.delete(lemma)


def get_best_pos(word, debug=False):
    # order here does not matter because every item will be assessed and scored
    # and the highest score will be selected
    search_lemmas = ["", "ADJ", "NOUN", "VERB"]

    for lemma_pos in search_lemmas:
        lemma = spanish_words.get_lemma(word, lemma_pos)
        all_pos = get_pos_overlap(lemma, debug)
        if debug:
            print("all_pos (%s %s %s): %s"%(word,lemma_pos, lemma, all_pos))

        if all_pos and len(all_pos):
            print("getting weights for: ", lemma, all_pos)
        continue


        # If there are multiple options, prefer the one with most sentence usage
        # skews us towards the tagging mistakes in the sentences (eg "placer" is
        # usually mis-tagged as a verb instead of a noun and will return "verb")
        pos  = ""
        if len(all_pos) == 1:
            pos = list(all_pos)[0]
        elif len(all_pos) > 1:
            if debug:
                print("tie breaker")
            #pos = spanish_sentences.get_best_pos(lemma, all_pos)
            if debug:
                print("result = ",pos)

        if pos:
            return pos

    exit()

    # There is no overlap between any sources for any available lemmmas
    # Search again using just the dictionary
    for lemma_pos in ["", "NOUN", "VERB", "ADJ"]:
        lemma = spanish_words.get_lemma(word, pos)
        dictionary_pos = sorted(set(spanish_words.get_all_pos(word)))

        if len(dictionary_pos):
            return dictionary_pos[0]

    if pos == "":
            pos = "NONE"
#            print("NONE:", word)
    return pos
