#!/usr/bin/python3

import argparse
import os
import re
import sys

from collections import defaultdict

from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.word import Word
from enwiktionary_wordlist.all_forms import AllForms

from .probability import PosProbability
from ..sentences import SpanishSentences

class FrequencyList():

    # Some verbs can have the same forms, hard code a list of
    # preferred verbs, lesser verb
    _verb_fixes = [
       ("creer", "crear"),
       ("salir", "salgar"),
       ("salir", "salar"),
       ('soler', 'solar'),
       ("prender", "prendar"),
    ]

    def __init__(self, wordlist, allforms, sentences, ignore_data, probs, debug_word=None):
        self.wordlist = wordlist
        self.allforms = allforms
        self.sentences = sentences
        self.probs = probs
        self.load_ignore(ignore_data)
        self.DEBUG_WORD = debug_word
        self.forced_regs = {}

    def load_ignore(self, ignore_data):
        self.ignore = {line.strip() for line in ignore_data if line.strip() and not line.strip().startswith("#")}

    def is_irregular_verb(self, word):
        if word.pos != "v":
            return False

        forced_reg = self.forced_regs.get(word)
        if forced_reg is None:
            forced_reg = Word(word.word, [ ("pos", word.pos), ("meta", re.sub("es-conj", "es-conj-reg", word.meta)) ])
            self.forced_regs[word] = forced_reg

        return word.forms != forced_reg.forms

    def is_irregular_form(self, form, formtype, word):
        if word.pos != "v":
            return False

        forced_reg = self.forced_regs.get(word)
        if forced_reg is None:
            forced_reg = Word(word.word, [ ("pos", word.pos), ("meta", re.sub("es-conj", "es-conj-reg", word.meta)) ])
            self.forced_regs[word] = forced_reg

        return form not in forced_reg.forms.get(formtype, [])

    def formtypes(self, freqlist):

        entries = self.find_lemmas(freqlist)
        for form, details in entries.items():
            pos, count, lemma = details

            formtypes = set()
            for w in self.wordlist.get_words(lemma, pos):
                for formtype, forms in w.forms.items():
                    if form in forms:
                        if self.is_irregular_form(form, formtype, w):
                            formtype += "*"
                        formtypes.add(formtype)

            yield f"{form}, {lemma}, {count}, {', '.join(sorted(formtypes))}"

    def process(self, freqlist, minuse=0):
        entries = self.find_lemmas(freqlist)
        freq = self.build_freqlist(entries)

        yield("count,spanish,pos,flags,usage")
        for k, item in sorted(freq.items(), key=lambda item: (item[1]["count"]*-1, item[1]["word"])):
            if minuse and item["count"] < minuse:
                break
            yield(
                ",".join(
                    map(
                        str,
                        [
                            item["count"],
                            item["word"],
                            item["pos"],
                            "; ".join(item["flags"]),
                            "|".join(sorted(item["usage"], key=lambda x: int(x.partition(":")[0]), reverse=True)),
                        ],
                    )
                )
            )

    def find_lemmas(self, freqlist):

        """
        freqlist is an iterable of strings formatted as "[@]word[:pos][ N]"
          @ - optional, word will be treated as an exact lemma, without being resolved further
          word - the word form
          :pos - optional - word will be treated as the given part of speech
          N - count, optional, must be preceeded by a space - the number of occurances of the word
              if N is invalid or not specified, an arbitrary value will be assigned,
              giving greater value to the words appearing earliest in the iterable

        returns: { "form": (pos, count, lemma), ... }, [ multilemma1, ...], [ maybeplural1, ...]
        if the pos or lemma cannot be determined yet, they will be NULL and the word will be included
        in either the multilemma or the maybeplural list
        words that are not part of the spanish database will have NULL pos and lemma but will not be
        included in the multilemma or maybeplural lists
        """

        lines = {}
        multi_lemmas = []
        maybe_plurals = []

        # Read all the lines and do an initial lookup of lemmas
        for linenum, line in enumerate(freqlist):
            word, _, count = line.strip().partition(" ")
            word, _, pos = word.partition(":")

            if not count or not count.isdigit():
                if count:
                    word = word + " " + count
                # If the list doesn't include a counter,
                # assign a value in descending order to preserve the list order
                count = 100000-linenum
            else:
                count = int(count)

            if word in self.ignore:
                continue

            lemma = None
            if word.startswith("@"):
                lemma = word[1:]
                word = word[1:]

            preferred_lemmas = self.get_preferred_lemmas(word, lemma, pos)
            if word == self.DEBUG_WORD:
                print(word, "possible lemmas", [(l.word, l.pos) for l in preferred_lemmas], (word, lemma, pos))

            if not pos:

                if self.maybe_plural(word, preferred_lemmas):
                    maybe_plurals.append((word, preferred_lemmas))
                    pos = None
                    if word == self.DEBUG_WORD:
                        print("###", word, "maybe_plural")
                else:
                    pos = self.get_best_pos(word, preferred_lemmas)

                    if word == self.DEBUG_WORD:
                        print("###", word, "best pos", pos)

                    # TODO: if get_ranked_pos has a tie,
                    # add the word to a new multi_pos list
                    # and resolve it later

            if not lemma and pos:
                lemmas = []
                for l in preferred_lemmas:
                    if l.pos == pos and l.word not in lemmas:
                        lemmas.append(l.word)

                if word == self.DEBUG_WORD:
                    print("###", word, "getting lemmas", lemmas, pos)

                if not lemmas:
                    raise ValueError("couldn't find lemma", word, pos)

                if len(lemmas) > 1:
                    if word == self.DEBUG_WORD:
                        print("###", word, "multi_lemma")
                    multi_lemmas.append((word, preferred_lemmas))
                    lemma = None
                else:
                    lemma = lemmas[0]

            lines[word] = (pos, count, lemma)

        # Run through the lines again and use the earlier counts to
        # pick best lemmas from words with multiple lemmas
        print(f"resolving {len(multi_lemmas)} multi lemmas")
        for word, preferred_lemmas in multi_lemmas:
            item = lines[word]
            pos,count,_ = item

            lemma = self.get_most_frequent_lemma(lines, word, pos, preferred_lemmas)

            lines[word] = (pos, count, lemma)

            if word == self.DEBUG_WORD:
                print("###", word, "resolving lemmas", item, "to", lemma)

        print(f"resolving {len(maybe_plurals)} maybe plurals")
        for word, preferred_lemmas in maybe_plurals:
            entry = self.resolve_plurals(lines, word, preferred_lemmas)
            lines[word] = entry

        return lines


    def resolve_plurals(self, lines, word, preferred_lemmas):

        # process plurals after all other lemmas have been processed
        # if a plural has non-verb lemmas, take the non-verb lemma with the greatest usage
        #
        # fixes the following:
        #
        # mamá,n,,276902:mamá
        # mamás,adv,NODEF; NOSENT,2379:mamás
        #
        # soltero,n,,9181:soltero|8614:soltera
        # soltero,adj,DUPLICATE,3076:solteros|2356:solteras
        #
        _,count,_ = lines[word]

        if word == self.DEBUG_WORD:
            print("###", word, "resolving plurals")

        # Special handling for feminine plurals, stay with the feminine
        # form instead of using the masculine lemma
        if word.endswith("as"):
            lemma_pos, lemma_count, lemma_lemma = lines.get(word[:-1], [None,0,None])
            if lemma_count and word == self.DEBUG_WORD:
                print(word, "found feminine singular", lemma_pos, lemma_count, count)

            if lemma_count > count:
                return (lemma_pos, count, lemma_lemma)

        # If any possible singular lemmas has more uses than the plural, use it
        entry = self.get_best_singular(lines, word, preferred_lemmas)
        if entry:
            return entry

        # No singular form has more usage than the plural,
        # fallback to handling it like any other word
        if word == self.DEBUG_WORD:
            print(word, "popular plural, not following")

        pos = self.get_best_pos(word, preferred_lemmas)
        lemma = self.get_most_frequent_lemma(lines, word, pos, preferred_lemmas)

        if not lemma:
            for l in preferred_lemmas:
                print(l.word, l.pos, lines.get(l.word))
            raise ValueError("No lemmas", word, pos, posrank, [(l.word,l.pos) for l in preferred_lemmas])

        return (pos, count, lemma)

    def get_best_pos(self, word, preferred_lemmas):
        res = self.get_ranked_pos(word, preferred_lemmas)
        if not res:
            return None

        if len(res) > 1 and res[0][2] == res[1][2]:
            print("ambiguous best pos", word, res, "using first", res[0])
        form,pos,count = res[0]
        return pos

    def get_best_singular(self, lines, word, preferred_lemmas):

        _,count,_ = lines[word]

        # Plurals should use the same POS as the singular, unless the plural usage is more common
        # in which case it should use get_best_pos
        best = None
        best_count = -1
        checked_lemmas = []

        if word == self.DEBUG_WORD:
            print(word, "checking lemmas", [(l.pos, l.word) for l in preferred_lemmas])

        allowed_pos = self.get_all_pos(preferred_lemmas)
        for l in preferred_lemmas:

            if l.pos == "v":
                continue

            if l.word in checked_lemmas:
                continue
            checked_lemmas.append(l.word)

            item = lines.get(l.word)
            if not item:
                continue

            lemma_pos, lemma_count, lemma_lemmas = item

            if not lemma_pos or lemma_pos not in allowed_pos:
                continue

            if word == self.DEBUG_WORD:
                print(word, "checking item", l.word, item, lemma_count, best_count, lemma_count>best_count)

            if lemma_count > best_count:
                best = item
                best_count = lemma_count

        # If the singular is more popular than the plural, use it
        # sometimes the form is a lemma (gracias, iterj) so the count
        # will be equal
        if count > best_count:
            return

        if word == self.DEBUG_WORD:
            print(word, "following singular", best)

        pos, _, lemma = best
        return (pos, count, lemma)


    def maybe_plural(self, form, lemmas):
        """
        form - string
        lemmas - list of Word objects
        returns True if the form could be a plural
        A form may be plural if it ends with 's' and has any non-verb lemmas that don't match the form
        """
        if not form.endswith("s"):
            return False

        return any(l.pos != "v" and l.word != form for l in lemmas)

    def word_is_lemma(self, w):
        """
        This is a very strict definition of a lemma, the first word declared on a page:
           + " form" not in meta
           + the first sense is not a form of
           + it's not a feminine equivalent of
           + it's not labelled archaic
        """

        if not w or not w.senses:
            return False

        # TODO: deeper/better search if " form" in self.word (maybe "pos form")?
        if w.meta and " form" in w.meta and " form" not in w.word:
            return False

        # Feminine nouns that declare a masculine form aren't lemmas unless they're explicitly allowed
        if w.pos == "n" and w.genders == "f" and "m" in w.forms and w.word not in self.allforms.FEM_LEMMAS:
            return False

        # singular nouns are always lemmas, even "feminine of"
#        if (self.pos == "n" and self.genders in ["m", "f"]):
#            return True

#        if word.pos == "n" and word.genders == "f" and "m" in word.forms and word.word not in FEM_LEMMAS:
#            return False

        # If the first sense is a form-of, it's not a lemma
        # If the first sense is marked archaic, it's not a lemma
        for sense in w.senses:
            if sense.formtype:
                return False

            if sense.qualifier and re.match(r"(archaic|dated|obsolete|rare)", sense.qualifier):
                return False

            break # Only look at the first sense

        return True

    def get_resolved_lemmas(self, word, form, formtypes, max_depth=3):
        """
        follows a word to its final lemma
        word is a Word object that may or may not be a lemma
        form is the form that claimed a relationship with word, used to filter out non-reciprocal lemmas
        formtypes: any relationships 'form' claims to have to 'word', else None
        Returns a list of Word objects, may contain duplicates
        """

        lemmas = []

        if self.word_is_lemma(word):
            #print("****" , word.word, "is lemma")
            return [word]

        primary_lemma = True
        for lemma, lemma_formtypes in word.form_of.items():

 #           print("****" , word, formtypes)

            w = next(self.wordlist.get_words(lemma, word.pos), None)
            if not w:
                continue

#            if "f" in formtypes and w.forms and word.word not in w.forms.get("f"):
 #               print("******** skipping undeclared feminine")
#                continue

            if self.word_is_lemma(w):
                # Ignore lemmas that are listed below forms
                if primary_lemma:
                    lemmas.append(w)
                elif word.word == self.DEBUG_WORD:
                     print(word.word, word.pos, "ignoring secondary lemma", lemma, lemma_formtypes, w.word, w.pos)

            elif max_depth>0:
                primary_lemma = False
                for redirect in self.wordlist.get_words(lemma, word.pos):
                    lemmas += self.get_resolved_lemmas(redirect, lemma, lemma_formtypes, max_depth-1)
                    break # Only look at the first word

            else:
                print(f"Lemma recursion exceeded: {word.word} {word.pos} -> {lemma}", file=sys.stderr)
                return []

        return lemmas

    def get_preferred_lemmas(self, form, filter_word=None, filter_pos=None):
        """
        form - the form to find lemmas
        filter_word - if provided, return only lemmas matching the given filter_word
        filter_pos - if provided, return only lemmas matching the given pos

        Return a list of lemma objects
        """

        lemmas = []

        unresolved = self.get_unresolved_items(form, filter_pos)

        # Remove rare form of before resolving lemmas
        filtered = [x for x in unresolved if not self.is_rare_lemma(x[0])]
        unresolved = filtered if filtered else unresolved


        if not unresolved and self.allforms.get_lemmas(form, filter_pos):
            print("No matching lemmas", form, filter_pos, self.allforms.get_lemmas(form, filter_pos))
        if form == self.DEBUG_WORD:
            print(form, "unresolved items", [(l.word, l.pos, formtypes) for l, formtypes in unresolved])
        for w, formtypes in unresolved:
            resolved_lemmas = self.get_resolved_lemmas(w, form, formtypes)
            if form == self.DEBUG_WORD:
                print(self.DEBUG_WORD, f"  resolved {w.word}:{w.pos} to", [(l.word, l.pos) for l in resolved_lemmas])
            lemmas += resolved_lemmas

        if not lemmas:
            lemmas = [w for w,_ in unresolved]

        if filter_word or filter_pos:
            lemmas = self.filter_lemmas(lemmas, filter_word, filter_pos)

        filtered_lemmas = self.filter_rare_lemmas(lemmas)
        if len(lemmas) != len(filtered_lemmas):
            print("filter_rare", form, len(lemmas), len(filtered_lemmas))
        lemmas = filtered_lemmas if filtered_lemmas else lemmas

        filtered_lemmas = self.filter_secondary_lemmas(lemmas)
        if len(lemmas) != len(filtered_lemmas):
            print("filter_rare", form, len(lemmas), len(filtered_lemmas))
        lemmas = filtered_lemmas if filtered_lemmas else lemmas

        if not filter_pos or filter_pos == "v":
            lemmas = self.filter_rare_verbs(lemmas)

        return lemmas

    def get_claimed_lemmas(self, form, pos):
        """ Returns a list of (lemma_obj, [formtypes]) for a given form, pos """

        seen = set()
        items = []

        for word in self.wordlist.get_words(form, pos):
            if self.word_is_lemma(word):
                if word not in seen:
                    items.append((word, None))
                    seen.add(word)
                continue

            for lemma, formtypes in word.form_of.items():
                for lemma_obj in self.wordlist.get_words(lemma, word.pos):
                    if lemma_obj not in seen:
                        items.append((lemma_obj, formtypes))
                        seen.add(lemma_obj)
#                    else:
#                        print("dup", form, pos, lemma_obj.word)
        return items

    def get_unresolved_items(self, form, pos):
        items = []


        # An allforms entry will list lemmas that declare the form as well
        # as lemmas that the form declares itself to be a form of
        #
        # To get the list of claimed forms, do a dictionary lookup of the
        # given form/pos and add everything
        #
        # Then check all of the items in the allforms entry and add any
        # that weren't found in the dictionary lookup
        #
        # Forms may not be listed in the dictionary simply because they're rarely-used
        # conjugations of rare verbs, or because the dictionary has been stripped
        # of generated verbs

        items = self.get_claimed_lemmas(form, pos)
        seen = { lemma for lemma, formtypes in items }

        for lemma in self.get_declaring_lemmas(form, pos):
            if lemma not in seen:
                items.append((lemma, None))
                seen.add(lemma)


        # If no lemmas were found to declare this form and the dictionary doesn't
        # list it as a 'form of' anything, take whatever happens to be in allforms
        #
        # This assumes that everything listed by allforms has at least one useful word
        # Try to filter the lemmas, but if there's nothing left, take all the words
        if not items:
            seen = set()
            for poslemma in self.allforms.get_lemmas(form, pos):
                lemma_pos, lemma = poslemma.split("|")
                all_words = list(self.wordlist.get_words(lemma, lemma_pos))
                lemmas = [w for w in all_words if self.word_is_lemma(w)]
                new_items = lemmas if lemmas else all_words
                for item in new_items:
                    if item not in seen:
                        seen.add(item)
                        if item not in items:
                            items.append((item, None))

        return items

    def get_declaring_lemmas(self, form, pos):
        """ Returns a list of Word objects with a matching pos that declare the given form """

        items = []
        for poslemma in self.allforms.get_lemmas(form, pos):

            lemma_pos, lemma = poslemma.split("|")
#            print(form, "poslemma", lemma_pos, lemma)
            for word in self.wordlist.get_words(lemma, lemma_pos):
#                print(word.word, word.pos, self.word_is_lemma(word), word.has_form(form))
                if self.word_is_lemma(word) and word.has_form(form):
                    # TODO: get formtypes?
                    items.append(word)


        return items


    def filter_lemmas(self, lemmas, filter_word, filter_pos):

        res = []
        for l in lemmas:
            if l in res:
                continue
            if filter_word and l.word != filter_word:
                continue
            if filter_pos and l.pos != filter_pos:
                continue
            res.append(l)
        return res


    def filter_rare_verbs(self, lemmas):

        seen = {l.word for l in lemmas if l.pos == "v"}

        for preferred, nonpreferred in self._verb_fixes:
            if preferred in seen and nonpreferred in seen:
                lemmas = [ l for l in lemmas if l.pos != "v" or l.word != nonpreferred ]

        return lemmas

    def get_all_pos(self, lemmas):
        return sorted(set(l.pos for l in lemmas))

    def get_ranked_usage(self, word, possible_lemmas, use_lemma=False):
        """
        Returns a list of (word, pos, count), sorted by count, descending
        """

        all_pos = self.get_all_pos(possible_lemmas)
        freeling_fixes = []
        # Wiktionary considers tuyo, suyo, cuyo, vuestro, etc to be determiners,
        # but freeling classifies them as adj or art or pron
        # TODO: if "determiner" in all_pos and "adj" or "art" in sentence_pos,
        # treat the adj/art as determiner
        if not use_lemma and "determiner" in all_pos:
            for alt in ["art", "adj", "pron"]:
                if alt not in all_pos:
                    all_pos.append(alt)
                    freeling_fixes.append(alt)

        usage = []
        if use_lemma:
            for lemma in possible_lemmas:
                item = (lemma.word, lemma.pos)
                if item not in usage:
                    usage.append(item)
        else:
            for pos in all_pos:
                usage.append(("@" + word, pos))

        usage_count = [ (word, pos, self.sentences.get_usage_count(word, pos)) for word, pos in usage ]
        res = sorted(usage_count, key=lambda k: int(k[2]), reverse=True)

        if freeling_fixes:
            res = [ (word, pos, count) if pos not in freeling_fixes else (word, "determiner", count) for word, pos, count in res ]
            # TODO: this may result in an extra item of both "art" and "adj" were added

        # If no usage found
        if res[0][2] == 0 and not use_lemma:
            sentence_pos = self.sentences.get_all_pos("@"+word)
            if sentence_pos:

                # In sentences the past participles are marked "verb" instead of "v"
                # so that the summed verb forms don't overwhelm the summed adjective of noun forms
                # However, if we've made it this far and haven't found anything, count it explicitly
                # as a verb
                if "v" in all_pos and "verb" in sentence_pos:
                    res = [ (word, "v", self.sentences.get_usage_count(word, "verb")) ]
                    res += [ (word, pos, 0) for word, pos in usage if pos != "v" ]
                    #print(f"{word}: using 'verb' count instead of 'v'")
                    return res

        return res

    def get_freq_probs(self, word, all_pos):
        pos_by_prob = self.probs.get_pos_probs(word, all_pos)
        if not pos_by_prob:
            return

        sorted_pos_by_prob = [(None,pos,count) for pos,count in sorted(pos_by_prob.items(), key=lambda x: x[1], reverse=True)]

        if not (len(sorted_pos_by_prob) == 1 or sorted_pos_by_prob[0][2] > 2*sorted_pos_by_prob[1][2]):
            return

        ranked_pos = [pos for word,pos,count in sorted_pos_by_prob]
        best_pos = ranked_pos[0]

        # Sometimes wiktionary and freeling disagree about the POS for a word, in which case
        # the sentences database will be tagged with freeling's preference and there will
        # be no usage count for any of the wiktionary POS (example 'esas' - wikipedia says determiner/pronoun,
        # but freeling tags it as an adjective

        if best_pos not in all_pos and "determiner" in all_pos and "determiner" not in ranked_pos and best_pos in ["adj", "art"]:
            sorted_pos_by_prob[0][1] = "determiner"

        return sorted_pos_by_prob

    def get_ranked_pos(self, word, possible_lemmas, use_lemma=False):
        """
        Returns a list of all possible parts of speech, sorted by frequency of use
        """

        all_pos = self.get_all_pos(possible_lemmas)

        if not all_pos:
            return None

        if len(all_pos) == 1:
            return [(None,all_pos[0],1)]

        pos_rank = self.get_ranked_usage(word, possible_lemmas, use_lemma)

        if word == self.DEBUG_WORD:
            print("get_ranked_pos:posrank", word, use_lemma, pos_rank)

        pos_with_usage = [ pos for word,pos,count in pos_rank if count > 0 ]

        if len(pos_with_usage) == 1:
            return sorted(pos_rank, key=lambda k: int(k[2]), reverse=True)

        # If there's enough usage data in the sentences, let them decide:
        # - preferred pos has at least 10 usages and 1.3* more than the secondary
        # - preferred pos has at least 4 usages and secondary <= 1
        if (   (pos_rank[0][2] >= 10 and pos_rank[0][2] >= 1.3*(pos_rank[1][2]))
            or (pos_rank[0][2] >= 4 and pos_rank[0][2] >= 3*(pos_rank[1][2]))
            ):
            return pos_rank

        # No sentence usage or equal sentence usage, check the prob table
        if not use_lemma and self.probs:
            res = self.get_freq_probs(word, all_pos)
            if res:
                if word == self.DEBUG_WORD:
                    print("get_ranked_pos, using probs table:", sorted_pos_by_prob)
                return res

        # If anything has more sentence usage, take it
        if pos_rank[0][2] > pos_rank[1][2]:
            return pos_rank

        if word == self.DEBUG_WORD:
            print("get_ranked_pos:3")

        # If there's still a tie, take non-verbs over verbs
        # If there's still a tie, use the lemam forms
        # Still tied? prefer adj > noun > non-verb > verb

        top_count = pos_rank[0][2]

        # prefer non-verbs over verbs
        if top_count > 0 or use_lemma:
            for i, (form, pos, count) in enumerate(pos_rank):
                if count != top_count:
                    break
                if pos != "v":
                    count += 1
                pos_rank[i] = (form, pos, count)

        if pos_rank[0][2] > pos_rank[1][2]:
            return pos_rank

        # Try with lemma forms
        if not use_lemma:
            return self.get_ranked_pos(word, possible_lemmas, use_lemma=True)

        # prefer adj > noun > anything > verb
        top_count = pos_rank[0][2]
        for i, (form, pos, count) in enumerate(pos_rank):
            if count != top_count:
                break
            if pos == "adj":
                count += 3
            elif pos == "n":
                count += 2
            elif pos != "v":
                count += 1

            pos_rank[i] = (form, pos, count)

        return sorted(pos_rank, key=lambda k: int(k[2]), reverse=True)

    flags_defs = {
        "UNKNOWN": "Word does not appear in lemma database or dictionary",
        "NOUSAGE": "Multiple POS, but no sentences for any usage",
        "PRONOUN": "Ignoring pronouns",
        "LETTER": "Letter",
        "NODEF": "No definition",
        "NOSENT": "No sentences",
        "FUZZY": "Only has fuzzy sentance matches",
        "DUPLICATE": "Duplicate usage of word with different POS",
        "DUPLICATE-ADJ-ADV": "Adverb duplicates existing adjective",
        "DUPLICATE-ADJ-NOUN": "Noun duplicates existing adjective",
        "DUPLICATE-REFLEXIVE": "Reflexive verb duplicase existing non-reflexive verb",
    }

    def get_word_flags(self, word, pos):
        flags = []
        pos = pos.lower()
        if pos == "unknown":
            flags.append("UNKNOWN")

        if pos == "none":
            flags.append("NOUSAGE")

        if pos == "pron":
            flags.append("PRONOUN")

        if pos == "letter":
            flags.append("LETTER")

        if not self.wordlist.has_word(word, pos):
            flags.append("NODEF")

        res = self.sentences.get_sentences([[word, pos]], 1)
        if not len(res["sentences"]):
            flags.append("NOSENT")

        else:
            if res["matched"] == "literal":
                flags.append("LITERAL")
            elif res["matched"] == "fuzzy":
                flags.append("FUZZY")

        # remove reflexive verbs if the non-reflexive verb is already on the list
       # if word.endswith("rse") and pos == "v" and (word[:-2],"v") in freq:
       #     flags.append("DUPLICATE-REFLEXIVE")
       #
#        if pos == "v" and any(self.is_irregular_verb(w) for w in self.wordlist.get_words(word, pos)):
#            flags.append("IRREGULAR")

        return flags


    def get_lemma_freq(self, lines):

        lemma_freq = {}
        for form, item in lines.items():
            pos,count,lemma = item
            if not lemma:
                lemma = form

            if not pos:
                pos = "none"

            tag = (lemma, pos)

            if tag not in lemma_freq:
                lemma_freq[tag] = {"count": 0, "usage": []}

            lemma_freq[tag]["count"] += count
            lemma_freq[tag]["usage"].append(f"{count}:{form}")

            if form == self.DEBUG_WORD:
                print("###", form, "counting", item)

        return lemma_freq

    def build_freqlist(self, lines):

        lemma_freq = self.get_lemma_freq(lines)

        freq = {}
        wordusage = {}
        count = 1
        for tag, item in sorted(lemma_freq.items(), key=lambda x: (x[1]["count"]*-1, x[0])):
            word, pos = tag

            flags = self.get_word_flags(word, pos)

            # Check for repeat usage
            if word not in wordusage:
                wordusage[word] = {}

            wordusage[word][pos] = item["count"]
            #wordusage[word].append(pos)

            freq[tag] = {
                "count": item["count"],
                "word": word,
                "pos": pos,
                "flags": flags,
                "usage": item["usage"],
            }

            count += 1

        repeatusage = {}
        for word in wordusage:
            if len(wordusage[word].keys()) > 1:
                repeatusage[word] = wordusage[word]

        for word, all_pos in repeatusage.items():
            best_count = -1
            best_pos = ""
            for pos, count in all_pos.items():
                # ignore anything that's already flagged for dismissal
                if len(freq[(word,pos)]["flags"]):
                    continue
                if count > best_count:
                    best_count = count
                    best_pos = pos

            popular_pos = []
            for pos, count in all_pos.items():
                if count < best_count:
                    freq[(word, pos)]["flags"].append("DUPLICATE")

        return freq

    def is_primary_lemma(self, word_obj):
        for w in self.wordlist.get_words(word_obj.word, word_obj.pos):
            if not self.word_is_lemma(w):
                return False
            if w == word_obj:
                return True
        return False

    def filter_secondary_lemmas(self, lemmas):
        filtered_lemmas = [lemma for lemma in lemmas if self.is_primary_lemma(lemma)]
        return filtered_lemmas if filtered_lemmas else lemmas

    def is_rare_lemma(self, word_obj):
        """
        Returns False if word_obj has any non-form sense not flagged rare/archaic
        """

        has_nonrare_sense = False
        for sense in word_obj.senses:
            if not (sense.qualifier and re.match(r"(archaic|dated|obsolete|rare)", sense.qualifier)) and \
                not (sense.gloss and re.match(r"(archaic|dated|obsolete|rare) form of", sense.gloss)):
                    return False
            else:
                has_nonrare_sense = True
        return has_nonrare_sense

    def filter_rare_lemmas(self, lemmas):
        return [lemma for lemma in lemmas if not self.is_rare_lemma(lemma)]

    def get_most_frequent_lemma(self, entries, word, pos, possible_lemmas):

        lemmas = []
        for lemma in possible_lemmas:
            if lemma.pos == pos and lemma.word not in lemmas:
                lemmas.append(lemma.word)

        if word == self.DEBUG_WORD:
            print(word, pos, "get_most_frequent_lemma_list", lemmas)

        if len(lemmas) == 1:
            return lemmas[0]

        if not lemmas:
            return

        if word in lemmas:
            return word

        best = None
        best_count = -1

        # Pick the more common lemma
        # NOTE: this only looks at the count for the raw lemma, not the count of the lemma plus all of its forms
        for lemma in lemmas:
            _,count,_ = entries.get(lemma, [None, -1, None])
            if count > best_count:
                best = lemma
                best_count = count
            if word == self.DEBUG_WORD:
                print("###", word, "get_best_lemma", lemmas, "best:", best, best_count)

        # Still nothing, just take the first lemma
        # TODO: this only applies to a few words in the 50k dataset:
        # still, it could be better resolved by getting the full count for each lemma and taking the more common
        #
        ### fine get_best_lemma ['finar', 'finir'] no best, defaulting to first finar
        ### reviste get_best_lemma ['rever', 'revestir', 'revistar'] no best, defaulting to first rever
        ### cierne get_best_lemma ['cerner', 'cernir'] no best, defaulting to first cerner
        ### ciernes get_best_lemma ['cerner', 'cernir'] no best, defaulting to first cerner
        ### mima get_best_lemma ['mimar', 'mimir'] no best, defaulting to first mimar
        ### adujo get_best_lemma ['aducir', 'adujar'] no best, defaulting to first aducir
        ### revisten get_best_lemma ['revestir', 'revistar'] no best, defaulting to first revestir
        ### tamales get_best_lemma ['tamal', 'tamale'] no best, defaulting to first tamal

        if best is None and len(lemmas):

            usage = [(self.sentences.get_usage_count(l.word, pos), l.word) for l in possible_lemmas]
            ranked = sorted(usage, key=lambda x: (x[0]*-1, x[1]))
            if word == self.DEBUG_WORD:
                print("###", word, pos, "get_best_lemma", lemmas, "no best, using sentences frequency", ranked)

            if ranked[0][0] == ranked[1][0]:
                print("###", word, pos, "get_best_lemma", lemmas, "no best, no sentences frequency", ranked)

            return ranked[0][1]

        return best
