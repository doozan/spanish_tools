from .wordlist import SpanishWordlist
from .verbs import SpanishVerbs
from .nouns import SpanishNouns
from .adjectives import SpanishAdjectives
import re
import sys
import os

class SpanishWords:
    def __init__(self, dictionary):
        self.wordlist = SpanishWordlist(dictionary, self)
        self.adj = SpanishAdjectives()
        self.noun = SpanishNouns()
        self.verb = SpanishVerbs(self.wordlist.irregular_verbs)

    def common_pos(self, pos):
        return self.wordlist.common_pos(pos)

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

        if pos == "adj":
            if self.has_word(word, "noun"):
                results.update(self.wordlist.lookup(word,"noun"))
            #if self.verb.is_past_participle(word):
            #    lemma = self.get_lemma(word, "verb")
            #    results['adj'].update({'verb': f'past particple of {lemma}'})

        elif pos == "noun":
            word_adj = self.get_lemma(word, "adj")
            if self.has_word(word_adj, "adj"):
                results.update(self.wordlist.lookup(word_adj,"adj"))
            #if self.verb.is_past_participle(word):
            #    lemma = self.get_lemma(word, "verb")
            #    results['adj'].update({'verb': f'past particple of {lemma}'})

        elif pos != "interj":
            if self.has_word(word, "adj"):
                results.update(self.wordlist.lookup(word,"adj"))
            if self.has_word(word, "noun"):
                results.update(self.wordlist.lookup(word,"noun"))

        results = self.filter_country_notes(results)
        return results

    def filter_country_notes(self, alldefs):
        if not alldefs:
            return {}
        res = {}
        for pos,notes in alldefs.items():
            res[pos] = {}
            for note, defs in notes.items():
                tags = { n.strip() for n in note.lower().split(',') }

                # strip smaller country-specific usage if it's only listed for one country
                overlap = tags & {"chile", "argentina", "venezuela", "peru", "uruguay", "el salvador", "colombia", "cuba", "honduras", "ecuador", "bolivia", "costa rica", "nicaragua", "dominican republic", "guatemala", "paraguay", "puerto rico", "panama", "caribbean", "philippines", "us", "united states", "new mexico", "louisiana"}
                if len(overlap) == 1:
                    if "mexico" not in tags and "spain" not in tags:
                        continue
                res[pos][note] = defs

        return res


    def get_valid_lemmas(self, word, items, pos):
        valid = [ item for item in items if self.has_word(item, pos) ]

        if len(valid):
            valid = list(dict.fromkeys(valid).keys())
            if len(valid) > 1 and word in valid:
                valid.remove(word)
        return valid

    def get_synonyms(self, word, pos):
        word = word.lower().strip()
        pos = pos.lower()

        syns = self.wordlist.get_synonyms(word, pos)
        if not syns:
            return []
        return syns


    def get_lemmas(self, word, pos, debug=False):
        word = word.lower().strip()
        pos = pos.lower()

        if pos == "adj":
            lemma = self.wordlist.get_lemma(word, "adj")
            if lemma:
                return [lemma]

            maybe_lemmas = self.adj.get_lemma(word)
            lemmas = self.get_valid_lemmas(word, maybe_lemmas, pos)
            if len(lemmas):
                return lemmas

            return [word]

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

                maybe_lemmas = self.noun.make_singular(word)
                lemmas = self.get_valid_lemmas(word, maybe_lemmas, pos)
                if len(lemmas):
                    return lemmas

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
