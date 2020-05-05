import sys


_debug=False
def set_debug(debug):
    global _debug
    _debug=debug

def dprint(*args, **kwargs):
    if _debug:
        print(*args, file=sys.stderr, **kwargs)


def get_best_pos(word, spanish, sentences, debug=False):
    set_debug(debug)

    pos_rank = get_ranked_pos(word, spanish, sentences, debug, False)
    if not pos_rank or not len(pos_rank):
        return "none"

    # No results, but multiple results, try again using lemma instead of word
    if len(pos_rank) > 1 and pos_rank[0]['count'] == 0:
        pos_rank = get_ranked_pos(word, spanish, sentences, debug, True)

    # still no results, take the first pos
    if pos_rank[0]['count'] == 0:
        return get_all_pos(word, spanish)[0]

    return pos_rank[0]['pos']


def get_all_pos(word, spanish):

    # get all possible POS usage for this word
    # cycle through all possible lemmas because words like "casas" won't
    # show up in the dictionary, but the lemma "casa" does
    all_pos = []
    for pos in ["", "adj", "noun", "verb"]:
        lemma = spanish.get_lemma(word, pos).split("|")[0]
        all_pos +=  spanish.wordlist.get_all_pos(lemma)

    all_pos = list(dict.fromkeys(all_pos))
    return all_pos


def get_ranked_pos(word, spanish, sentences, debug=False, use_lemma=False):

    all_pos = get_all_pos(word, spanish)

    if not all_pos:
        return None

    usage = []
    for pos in all_pos:
        if use_lemma:
            usage.append({ 'word': spanish.get_lemma(word, pos), 'pos': pos })
        else:
            usage.append({ 'word': "@"+word, 'pos': pos })
    pos_rank = rank_usage(usage, spanish, sentences, debug)
    dprint(pos_rank)
    return pos_rank


def rank_usage(usage, spanish, sentences, debug=False):
    set_debug(debug)

    res = []
    for item in usage:
        word = item['word']
        pos = item['pos']
        count = sentences.get_usage_count(item['word'], item['pos'])
        res.append({'word': word, 'pos': pos, 'count': count})
    return sorted(res, key=lambda k: k['count'], reverse=True)
