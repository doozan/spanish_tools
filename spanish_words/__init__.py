from .wordlist import SpanishWordlist
from .verbs import SpanishVerbs
from .nouns import SpanishNouns
from .adjectives import SpanishAdjectives
import re
import sys
import os

class SpanishWords:
    def __init__(self, dictionary, data_dir, custom_dir):
        self.wordlist = SpanishWordlist(self, dictionary, data_dir, custom_dir)
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

    def get_all_pos(self, word):
        return self.wordlist.get_all_pos(word)

    def lookup(self, word, pos, get_all_pos=True, max_length=0):
        results = self.wordlist.lookup(word, pos)

        if not get_all_pos:
            return results

        for pos in self.get_all_pos(word):
            if pos in [ "adj", "noun" ]:
                lemma = self.get_lemma(word,pos)
                results.update(self.wordlist.lookup(lemma,pos))
            # TODO: catch mistagged past participles, fixed in wiki, can remove this after 8/20 wiki update
            elif pos == "verb" and not word.endswith("r") and not word.endswith("rse"):
                continue
            else:
                results.update(self.wordlist.lookup(word,pos))


        if max_length:
            results = self.shorten_defs(results, max_length)

        return results


    # Get a shorter definition having less than max_len characters
    #
    # Definitions separated by commas are assumed to be synonyms, while semicolons
    # separate distinct usage.  Synonyms may be dropped to save space
    #
    # Return up to two distinct usages from the given definitions
    #
    # For nouns with male/female parts, try to include a definition for each gender
    #
    # For verbs with reflexive/non-reflexive, try to include a definition for each use
    #
    # If there are tagged/untagged uses, try to include the untagged and the first tagged usage
    #
    # Otherwise, try to include the first two distinct uses
    #
    def shorten_defs(self, defs, max_len=60, only_first_def=False):

        first_pos = next(iter(defs))

        shortdefs = {}

        if first_pos in ["m-f", "mf", "m/f"]:
            pos = first_pos
            shortdefs[pos] = {}
            for tag,value in defs[pos].items():
                for gender in ['m', 'f']:
                    if tag.startswith(gender) and not any( x.startswith(gender) for x in shortdefs[pos] ):
                        shortdefs[pos][tag] = value

            if not len(shortdefs[pos]):
                tag = next(iter(defs[pos]))
                shortdefs[pos][tag] = defs[pos][tag]

        elif first_pos.startswith("v"):
            for pos,tags in defs.items():
                if not pos.startswith("v"):
                    continue

                if len(shortdefs) and only_first_def:
                    continue

                # Always take the first verb def, then check each pronomial or reflexive def
                if len(shortdefs) and "p" not in pos and "r" not in pos:
                    continue

                # Limit to two defs (first + pronom or reflexive)
                if len(shortdefs)>=2:
                    continue

                # Use the first definition
                for tag,val in tags.items():
                    shortdefs[pos] = { tag: val }
                    break

                ## Take the untagged value, no matter the order
                #for tag,value in tags.items():
                #    if shortdefs[pos] == {} or tag == "":
                #        shortdefs[pos] = { tag: value }

        else:
            pos = first_pos
            tags = defs[pos]
            shortdefs[pos] = {}

            # Use the first definition
            for tag,val in tags.items():
                shortdefs[pos] = { tag: val }
                break

        # If there's only one usage, try to take two definitions from it
        pos = next(iter(shortdefs))
        if not only_first_def and len(shortdefs) == 1 and len(shortdefs[pos]) == 1:
            tag = next(iter(shortdefs[pos]))
            first_def, junk, other_defs = shortdefs[pos][tag].partition(";")
            if other_defs and len(other_defs):
                shortdefs[pos][tag] = first_def
                shortdefs[pos][";"] = other_defs

        # If there's one usage, and it doesn't contain mulitple defs
        # take the second tag of the first pos
        # or the first tag of the second pos
        if not only_first_def and len(shortdefs) == 1 and len(shortdefs[pos]) == 1:
            if len(defs[pos]) > 1:
                next_tag = list(defs[pos].keys())[1]
                shortdefs[pos][next_tag] = defs[pos][next_tag]
            elif len(defs) > 1:
                next_pos = list(defs.keys())[1]
                tag = next(iter(defs[next_pos]))
                shortdefs[next_pos] = { tag: defs[next_pos][tag] }

        for separator in [ ';', '(', '[' ]:
            for pos,tags in shortdefs.items():
                for tag,value in tags.items():
                    shortdefs[pos][tag] = value.partition(separator)[0].strip()

            if sum( len(pos)+len(tag)+len(value) for pos,tags in shortdefs.items() for tag,value in tags.items() ) <= max_len:
                break

        # If it's still too long, strip the last , until less than max length or no more , to strip
        can_strip=True
        while can_strip and sum( len(pos)+len(tag)+len(value) for pos,tags in shortdefs.items() for tag,value in tags.items() ) > max_len:
            can_strip=False
            for pos,tags in shortdefs.items():
                for tag,value in tags.items():
                    strip_pos = value.rfind(",")
                    if strip_pos > 0:
                        can_strip=True
                        shortdefs[pos][tag] = value[:strip_pos].strip()
                        if sum( len(pos)+len(tag)+len(value) for pos,tags in shortdefs.items() for tag,value in tags.items() ) <= max_len:
                            break


        # Rejoin any defs that we split out, unless it's a dup or too long
        pos = next(iter(shortdefs))
        if not only_first_def and ";" in shortdefs[pos]:
            tag = next(iter(shortdefs[pos]))

            # If the second def is the same as the first def, retry without splitting the def
            if shortdefs[pos][tag] == shortdefs[pos][';']:
                shortdefs = self.shorten_defs(defs, max_len=max_len, only_first_def=True)
            else:
                otherdef = shortdefs[pos].pop(';')
                shortdefs[pos][tag] += "; " + otherdef

        # If it's too long, try with just one definition
        if not only_first_def and sum( len(pos)+len(tag)+len(value) for pos,tags in shortdefs.items() for tag,value in tags.items() ) > max_len:
            shortdefs = self.shorten_defs(defs, max_len=max_len, only_first_def=True)

        if sum( len(pos)+len(tag)+len(value) for pos,tags in shortdefs.items() for tag,value in tags.items() ) > max_len:
            print(f"Alert: Trouble shortening def: {shortdefs}", file=sys.stderr)

        return shortdefs

    def get_valid_lemmas(self, word, pos, items):
        valid = [ item for item in items if self.has_word(item, pos) ]

        if len(valid):
            valid = dict.fromkeys(valid).keys()
            if len(valid) > 1 and word in valid:
                valid.remove(word)
        return list(valid)

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
            lemmas = self.get_valid_lemmas(word, pos, maybe_lemmas)
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
                lemmas = self.get_valid_lemmas(word, pos, maybe_lemmas)

                # check for masculine versions of any lemmas
                # actrices -> actriz -> actor
                macho_lemmas = []
                for word in lemmas:
                    masc = self.wordlist.get_masculine_noun(word)
                    if not masc:
                        masc = word
                    macho_lemmas.append(masc)

                if len(macho_lemmas):
                    return macho_lemmas

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
