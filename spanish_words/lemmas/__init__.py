from .verbs import SpanishVerbs
from .nouns import SpanishNouns
from .adjectives import *

class SpanishLemmas:
    def __init__(self, spanish_words, irregular_verbs):
        self.verbs = verbs.SpanishVerbs(spanish_words, irregular_verbs)
        self.nouns = nouns.SpanishNouns(spanish_words)

    def get_lemmas(self, word, pos, debug=False):
        word = word.lower().strip()
        pos = pos.lower()

        if pos == "adj":
            return [ adjectives.get_base_adjective(word) ]

        if pos == "noun":
            return [ self.nouns.get_base_noun(word) ]

        elif pos == "verb":

            if debug: print(self.verbs.reverse_conjugate(word))
            return [ v['verb'] for v in self.verbs.reverse_conjugate(word) ]

        return [ word ]

    def get_lemma(self, word, pos, debug=False):
        lemmas = self.get_lemmas(word,pos,debug)

        if not len(lemmas):
            return word

        if len(lemmas) == 1:
            return lemmas[0]

        # remove dups
        lemmas = list(dict.fromkeys(lemmas)) # Requires cpython 3.6 or python 3.7
        return "|".join(lemmas)

    def conjugate(self, verb, forms=None, debug=False):
        return self.verbs.conjugate(verb, forms, debug)
