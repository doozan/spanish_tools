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
        self.synonyms = SpanishSynonyms(synonyms)
        self.adj = SpanishAdjectives(self)
        self.noun = SpanishNouns(self)
        self.__wordlist = SpanishWordlist(dictionary, self)
        self.verb = SpanishVerbs(self)

    @property
    def wordlist(self):
        return self.__wordlist

    def get_defs(self, word):
        return self.wordlist.get_defs(word)

    def has_word(self, word, pos=None):
        if pos == "part":
            if self.wordlist._has_word(word, "adj"):
                return True
            elif self.wordlist._has_word(word, "noun"):
                return True
            lemma = self.get_lemma(word, "verb")
            if self.wordlist._has_word(lemma, "verb"):
                return True
            return False
        else:
            return self.wordlist._has_word(word, pos)

    def lookup(self, word, pos):
        results = self.wordlist.lookup(word, pos)

        if pos == "adj" and self.has_word(word, "noun"):
            results.update(self.wordlist.lookup(word,"noun"))

        if pos == "noun" and self.has_word(word, "adj"):
            results.update(self.wordlist.lookup(word,"adj"))

        if pos != "interj" and self.has_word(word, "interj"):
            results.update(self.wordlist.lookup(word,"interj"))

        if pos == "adj" and self.verb.is_past_participle(word):
            lemma = self.get_lemma(word, "verb")
            results['adj'].update({'verb': f'past particple of {lemma}'})

            results.update(self.wordlist.lookup(lemma,"verb"))

        return results

    def get_lemmas(self, word, pos, debug=False):
        word = word.lower().strip()
        pos = pos.lower()

        if pos == "adj":
            return [ self.adj.get_lemma(word) ]

        if pos == "noun":
            lemma = self.wordlist.get_lemma(word)
            if lemma:
                return [ lemma ]

            return [ self.noun.get_lemma(word) ]

        elif pos == "verb":

            res = []
            res = self.verb.reverse_conjugate(word)
#            if debug: print(res)
#            if select_best:
            res = self.verb.select_best(res, debug)

            res = [ v['verb'] for v in res ]
            if debug: print(res)
            return res

        elif pos == "part": # past participles
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
