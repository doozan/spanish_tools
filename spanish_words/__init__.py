from .wordlist import SpanishWordlist
from .verbs import SpanishVerbs
from .nouns import SpanishNouns
from .adjectives import SpanishAdjectives
from .synonyms import SpanishSynonyms
import re
import sys
import os

class SpanishWords:
    def __init__(self, dictionary, synonyms):

        self.wordlist = SpanishWordlist(dictionary)
        self.synonyms = SpanishSynonyms(synonyms)
        self.verb = SpanishVerbs(self)
        self.nouns = SpanishNouns(self)
        self.adjectives = SpanishAdjectives(self)


    def get_lemmas(self, word, pos, debug=False):
        word = word.lower().strip()
        pos = pos.lower()

        if pos == "adj":
            return [ self.adjectives.get_lemma(word) ]

        if pos == "noun":
            return [ self.nouns.get_lemma(word) ]

        elif pos == "verb":

            res = []
            res = self.verb.reverse_conjugate(word)
#            if debug: print(res)
#            if select_best:
            res = self.verb.select_best(res, debug)

            res = [ v['verb'] for v in res ]
            if debug: print(res)
            return res

        elif pos == "x": # past participles
            if word.endswith("s"):
                word = word[:-1]
            if word.endswith("a"):
                word = word[:-1]+"o"

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

    def selftest(self):
        return "OK"
