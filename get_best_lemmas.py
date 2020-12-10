import re

def is_good_lemma(wordlist, lemma, pos):
    for word_obj in wordlist.get_words(lemma, pos):
        for sense in word_obj.senses:
            if not (sense.qualifier and re.match(r"(archaic|dated|obsolete|rare)", sense.qualifier)) and \
                not (sense.gloss and re.match(r"(archaic|dated|obsolete|rare) form of", sense.gloss)):
                    return True

def word_is_lemma(wordlist, word, pos):
    for word in wordlist.get_words(word, pos):
        return word.is_lemma

def word_is_feminine(wordlist, word, pos):
    for word in wordlist.get_words(word, pos):
        return word.form in ["f", "fp"] or "feminine" in word.form

def word_is_feminine_form(wordlist, form, lemma, pos):
    """ Check if a given form is a feminine form of lemma """
    for word_obj in wordlist.get_words(lemma, pos):

        if word_obj.form not in ["m", "mp"] or "masculine" in word_obj.form:
            return False

        for formtype, forms in word_obj.forms.items():
            #if (formtype in ["f", "fpl"] or "feminine" in formtype) and form in forms:
            if formtype in ["f", "fpl"] and form in forms:
                return True

        # Only check the first word
        return False
    return False

def form_in_lemma(wordlist, form, lemma, pos):
    if form == lemma:
        return True

    for word in wordlist.get_words(lemma, pos):
        for formtype, forms in word.forms.items():
            if form in forms:
                return True
        # Only check the first word
        return False
    return False

def get_best_lemmas(wordlist, word, lemmas, pos):
    """
    Return the most frequently used lemma from a list of lemmas
    """


    # remove verb-se if verb is already in lemmas
    if pos == "verb":
        lemmas = [x for x in lemmas if not (x.endswith("se") and x[:-2] in lemmas)]

    # resolve lemmas that are "form of" other lemmas
    good_lemmas = set()
    for lemma in lemmas:
        for word_obj in wordlist.get_words(lemma, pos):
            good_lemmas |= set(wordlist.get_lemmas(word_obj).keys())

    lemmas = sorted(list(good_lemmas))

    # Hardcoded fixes for some verb pairs
    if pos == "verb":
        if "creer" in lemmas and "crear" in lemmas:
            lemmas.remove("crear")
        if "salir" in lemmas and "salgar" in lemmas:
            lemmas.remove("salgar")

    # discard any lemmas that aren't lemmas in their first declaration
    lemmas = [lemma for lemma in lemmas if word_is_lemma(wordlist, lemma, pos)]
    if len(lemmas) == 1:
        return lemmas


    # discard any lemmas that don't declare this form in their first definition
    lemmas = [lemma for lemma in lemmas if form_in_lemma(wordlist, word, lemma, pos)]
    if len(lemmas) == 1:
        return lemmas

    # If word is a feminine noun that could be a lemma, remove
    # any lemmas where it's just the feminine form of the masculine
    # (hamburguesa)
    if pos == "noun":
        if any(word_is_feminine(wordlist, lemma, pos) for lemma in lemmas):
            lemmas = [lemma for lemma in lemmas if not word_is_feminine_form(wordlist, word, lemma, pos)]
            if len(lemmas) == 1:
                return lemmas

    # remove dated/obsolete
    lemmas = [lemma for lemma in lemmas if is_good_lemma(wordlist, lemma, pos)]
    if len(lemmas) == 1:
        return lemmas

    # if one lemma is the word, use that
    if word in lemmas:
        return [word]

    return lemmas
