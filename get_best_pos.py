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

    usage = []
    for pos in all_pos:
        usage.append({ 'word': "@"+word, 'pos': pos })
    pos_rank = get_ranked_usage(usage, spanish, spanish_sentences, debug)
    dprint(pos_rank)

    # No results, but multiple results, try again using lemma instead of word
    if (pos_rank[0]['count'] == 0 and len(pos_rank)>1):
        dprint("No usage, checking lemmas")
        usage = []
        for pos in all_pos:
            usage.append({ 'word': spanish.get_lemma(word, pos), 'pos': pos })
        pos_rank = get_ranked_usage(usage, spanish, spanish_sentences, debug)
        dprint(pos_rank)

    # still no results, take the first pos
    if (pos_rank[0]['count'] == 0):
        return all_pos[0]

    return pos_rank[0]['pos']


def get_ranked_usage(usage, spanish, sentences, debug=False):
    set_debug(debug)

    res = []
    for item in usage:
        word = item['word']
        pos = item['pos']
        count = sentences.get_usage_count(item['word'], item['pos'])
        res.append({'word': word, 'pos': pos, 'count': count})
    return sorted(res, key=lambda k: k['count'], reverse=True)
