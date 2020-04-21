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

def get_best_pos(word, debug=False):
    set_debug(debug)

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
        dprint("lemmadb usage: ", all_lemmadb)
        dprint("No overlapping use, deferring to first dictionary entry: ", all_dict)
        return all_dict[0]

    return "NONE"


