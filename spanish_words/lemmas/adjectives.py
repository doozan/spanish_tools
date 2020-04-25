def get_base_adjective(word):
    if word.endswith("s"):
        word = word[:-1]

    if word.endswith("ale"):
        return word[:-1]

    if word.endswith("dora"):
        return word[:-1]

    if word.endswith("tora"):
        return word[:-1]

    if word.endswith("ista"):
        return word

    # Not a real rule, but good enough for stemming
    if word.endswith("a"):
        return word[:-1] + "o"

    return word
