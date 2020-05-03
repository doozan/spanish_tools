import sys


_debug=False
def set_debug(debug):
    global _debug
    _debug=debug

def dprint(*args, **kwargs):
    if _debug:
        print(*args, file=sys.stderr, **kwargs)

def get_best_pos(word, spanish, spanish_sentences, debug=False):
    set_debug(debug)

    # get all possible POS usage for this word
    # cycle through all possible lemmas because words like "casas" won't
    # show up in the dictionary, but the lemma "casa" does
    all_pos = []
    for pos in ["", "adj", "noun", "verb"]:
        lemma = spanish.get_lemma(word, pos).split("|")[0]
        all_pos +=  spanish.wordlist.get_all_pos(lemma)

    all_pos = list(dict.fromkeys(all_pos))

    if not len(all_pos):
        return "none"

    # If there's only one, use it
    if len(all_pos) == 1:
        dprint("Only one use found")
        return all_pos[0]

    # Get usage count of word as each possible POS
    dprint("Searching best use of %s in %s"%(word, all_pos))
    best_pos = spanish_sentences.get_best_pos("@"+word, all_pos, _debug)
    if best_pos and best_pos['count'] > 0:
        return best_pos['pos']

    dprint("No usage available")

    # There is no overlapping usage between dictionary and lemmadb
    return all_pos[0]

