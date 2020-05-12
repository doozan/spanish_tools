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
        self.verb = SpanishVerbs(self.__wordlist.irregular_verbs)

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
            lemma = self.wordlist.get_lemma(word, "adj")
            if lemma:
                return [lemma]

            return [ self.adj.get_lemma(word) ]

        if pos == "noun":
            lemma = self.wordlist.get_lemma(word, "noun")
            if lemma:
                return [lemma]

            if len(word) > 2 and word.endswith("s"):
                if self.has_word(word, "num"):
                    return [word]

                # try dropping the s first and seeing if the result is a known word (catches irregulars like bordes/borde)
                lemma = self.wordlist.get_lemma(word[:-1], "noun")
                if lemma:
                    return [lemma]

                singles = self.noun.make_singular(word)
                good_singles = []
                for single in singles:
                    lemma = self.wordlist.get_lemma(single, "noun")
                    if lemma:
                        good_singles.append(lemma)
                    elif self.has_word(single):
                        good_singles.append(single)

                if len(good_singles):
                    good_singles = list(dict.fromkeys(good_singles).keys())
                    if len(good_singles) > 1 and word in good_singles:
                        good_singles.remove(word)
                    return good_singles

            return [word]

        elif pos == "verb":

            res = []

            possible_verbs = self.verb.reverse_conjugate(word)
            if debug: print(possible_verbs)

            # validate possible verbs against real verbs in the wordlist
            if possible_verbs:
                for v in possible_verbs:
                    if self.has_word(v['verb'], "verb"):
                        res.append(v)
                    # Check for reflexive only verbs
                    elif self.has_word(v['verb']+"se", "verb"):
                        v['verb'] += "se"
                        res.append(v)

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
