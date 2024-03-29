#!/usr/bin/python3

import argparse
import os
import re
import sys

from collections import defaultdict, namedtuple

from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.word import Word
from enwiktionary_wordlist.all_forms import AllForms

Entry = namedtuple("Entry", [ "pos", "count", "lemma" ])

class FrequencyList():

    def __init__(self, wordlist, allforms, ngprobs, ignore_data=[], debug_word=None):
        self.wordlist = wordlist
        self.allforms = allforms
        self.ngprobs = ngprobs
        self.load_ignore(ignore_data)
        self.DEBUG_WORD = debug_word
        self.forced_regs = {}

    def debug(self, form, *args):
        if form == self.DEBUG_WORD:
            print("#", form, *args, file=sys.stderr)

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
        for form, entry in entries.items():

            formtypes = set()
            for w in self.wordlist.get_iwords(entry.lemma, entry.pos):
                for formtype, forms in w.forms.items():
                    if form in forms:
                        if self.is_irregular_form(form, formtype, w):
                            formtype += "*"
                        formtypes.add(formtype)

            yield f"{form}, {entry.lemma}, {entry.count}, {', '.join(sorted(formtypes))}"

    def filter_names(self, freq):

        for k, item in freq.items():
            usage = item["usage"]
            word = item["word"]
            if not word[0].islower():
                continue

            usage.sort(key=lambda x: int(x.partition(":")[0]), reverse=True)
            while usage:
                count, _, form = usage[0].partition(":")
                if form[0].islower():
                    break
                item["count"] -= int(count)

                self.debug(word, "removing likely name", form, count)

#                print("Removing name: ", word, [form, usage[0]], file=sys.stderr)
                del usage[0]


    def process(self, freqlist, minuse=0):
        entries = self.find_lemmas(freqlist)
        freq = self.build_freqlist(entries)
        self.filter_names(freq)

        yield("count,spanish,pos,flags,usage")
        for k, item in sorted(freq.items(), key=lambda item: (item[1]["count"]*-1, item[1]["word"])):
            if minuse and item["count"] < minuse:
                break
            yield(
                ",".join(
                    [
                        str(item["count"]),
                        item["word"],
                        item["pos"],
                        "; ".join(item["flags"]),
                        "|".join(sorted(item["usage"], key=lambda x: int(x.partition(":")[0]), reverse=True)),
                    ]
                )
            )

    def find_lemmas(self, freqlist):

        """
        freqlist is an iterable of strings formatted as "[form|@lemma][:pos][\tN][\tcomponents]"
          form - the word form
          @ - if the word is preceeded by the @ character, it will be treated as lemma
          :pos - optional - word will be treated as the given part of speech
          N - count, optional, must be preceeded by a space - the number of occurances of the word
              if N is invalid or not specified, an arbitrary value will be assigned,
              giving greater value to the words appearing earliest in the iterable

        returns: { "form": (pos, count, lemma), ... }
        if the pos or lemma cannot be determined yet, they will be NULL and the word will be included
        in either the multilemma or the maybeplural list
        words that are not part of the spanish database will have NULL pos and lemma but will not be
        included in the multilemma or maybeplural lists
        """

        entries = {}
        multi_lemmas = []
        maybe_plurals = []

        # Read all the entries and do an initial lookup of lemmas
        for linenum, line in enumerate(freqlist):
            line = line.strip()
            modifiers = None
            count = None
            form, *splits = line.split("\t")
            if len(splits) > 1:
                modifiers = splits[1]
            if splits:
                count = splits[0]

            form, _, pos = form.partition(":")
            orig_form = form

            if form in self.ignore:
                continue

            if count:
                count = int(count)
            else:
                # If the list doesn't include a counter,
                # assign a value in descending order to preserve the list order
                count = 100000-linenum
                assert count > 0

            lemma = None
            if form.startswith("@"):
                lemma = form[1:]
                form = form[1:]

            orig_case = form
            if not pos:

                # Get alternate case forms
                if form == form.lower() or self.ngprobs.get_case_prob(form) < 10:
                    alt_case = self.ngprobs.get_preferred_case(form.lower())
                    if alt_case != form:
   #                     print("using alt case", form, alt_case)
                        self.debug(alt_case, "preferred_case", form)
                        form = alt_case

            preferred_lemmas = self.get_preferred_lemmas(form, lemma, pos)
            if not preferred_lemmas and orig_form != form:
                form = orig_form
                preferred_lemmas = self.get_preferred_lemmas(form, lemma, pos)

            self.debug(form, "possible lemmas", [(l.word, l.pos) for l in preferred_lemmas])

            if not pos:

                if self.maybe_plural(form, preferred_lemmas):
                    maybe_plurals.append((orig_case, preferred_lemmas))
                    self.debug(form, "maybe_plural")
                else:
                    pos = self.get_best_pos(form, preferred_lemmas)
                    self.debug(form, "best_pos", pos)

            if not lemma and pos:
                lemmas = []
                for l in preferred_lemmas:
                    if l.pos == pos and l.word not in lemmas:
                        lemmas.append(l.word)

                self.debug(form, "getting lemmas", lemmas, pos)

                if not lemmas:
                    raise ValueError("couldn't find lemma", form, pos)

                if len(lemmas) > 1:
                    multi_lemmas.append((orig_case, preferred_lemmas))
                    lemma = None
                    self.debug(form, "multi_lemma")
                else:
                    lemma = lemmas[0]

            entries[orig_case] = Entry(pos, count, lemma)

#            if form == self.DEBUG_WORD:
#                exit()

        # count all forms of all lemmas so far, used to pick
        # the most popular lemmas from words with multiple lemmas
        lemma_freq = self.get_lemma_freq(entries)

        for form, preferred_lemmas in multi_lemmas:
            entry = entries[form]

            lemma = self.get_most_frequent_lemma(lemma_freq, form, entry.pos, preferred_lemmas)

            entries[form] = entry._replace(lemma=lemma)

            self.debug(form, "resolving lemmas", entry, "to", lemma)

        lemma_freq = self.get_lemma_freq(entries)

        for form, preferred_lemmas in maybe_plurals:
            entry = self.resolve_plurals(entries, lemma_freq, form, preferred_lemmas)
            entries[form] = entry

        return entries


    def resolve_plurals(self, entries, lemma_freq, form, preferred_lemmas):

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
        count = entries[form].count

        self.debug(form, "resolving plurals")

        # Special handling for feminine plurals, stay with the feminine
        # form instead of using the masculine lemma
        if form.endswith("as"):
            lemma = entries.get(form[:-1], Entry(None,0,None))
            self.debug(form, "found feminine singular", lemma.pos, lemma.count, count)

            if lemma.count >= count:
                return Entry(lemma.pos, count, lemma.lemma)

        # If any possible singular lemmas has more uses than the plural, use it
        singular_entry = self.get_best_singular(entries, form, preferred_lemmas)
        if singular_entry:
            return singular_entry

        # No singular form has more usage than the plural,
        # fallback to handling it like any other word
        self.debug(form, "popular plural, not following")

        pos = self.get_best_pos(form, preferred_lemmas)
        lemma = self.get_most_frequent_lemma(lemma_freq, form, pos, preferred_lemmas)

        if not lemma:
            raise ValueError("No lemmas", form, pos, posrank, [(l.word,l.pos) for l in preferred_lemmas])

        return Entry(pos, count, lemma)

    def get_best_pos(self, form, preferred_lemmas):
        res = self.get_ranked_pos(form, preferred_lemmas)
        self.debug(form, "ranked_pos", res)
        if not res:
            return None

        if len(res) > 1 and res[0][2] == res[1][2]:
            print("ambiguous best pos", form, res, "using first", res[0], file=sys.stderr)

        form,pos,count = res[0]
        return pos

    def get_best_singular(self, entries, form, preferred_lemmas):

        count = entries[form].count

        # Plurals should use the same POS as the singular, unless the plural usage is more common
        # in which case it should use get_best_pos
        best = None
        checked_lemmas = []

        self.debug(form, "checking lemmas", [(l.pos, l.word) for l in preferred_lemmas])

        allowed_pos = self.get_all_pos(preferred_lemmas)
        for l in preferred_lemmas:

            if l.pos == "v":
                continue

            if l.word in checked_lemmas:
                continue
            checked_lemmas.append(l.word)

            item = entries.get(l.word)
            if not item:
                continue

            if not item.pos or item.pos not in allowed_pos:
                continue

#            self.debug(form, "checking item", l.word, item, item.count, best.count, item.count>best.count)

            if not best or item.count > best.count:
                best = item

        # If the singular is more popular than the plural, use it
        # sometimes the form is a lemma (gracias, iterj) so the count
        # will be equal
        if best and best.count > count:
            self.debug(form, "following singular", best)

            return best._replace(count=count)


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

    def is_lemma(self, w):
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

            if self.is_rare_qualifier(sense.qualifier):
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

        if max_depth<3:
            print("resolving deep lemma", word.word, word.pos, form, formtypes, max_depth, file=sys.stderr)

        lemmas = []

        if self.is_lemma(word):
            return [word]

        primary_lemma = True
        for lemma, lemma_formtypes in word.form_of.items():
            w = next(self.wordlist.get_iwords(lemma, word.pos), None)
            if not w:
                continue

            if self.is_lemma(w):
                # Ignore lemmas that are listed below forms
                if primary_lemma:
                    lemmas.append(w)
                else:
                     self.debug(word.word, word.pos, "ignoring secondary lemma", lemma, lemma_formtypes, w.word, w.pos)

            elif max_depth>0:
                primary_lemma = False
                lemmas += self.get_resolved_lemmas(w, lemma, lemma_formtypes, max_depth-1)

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

        # workaround for "part"/"v" splits
        # "abierto" is "part", but its lemma "abrir" is "v"
        # Use "part" above to get the list of lemmas, then use "v" below to filter the lemmas
        if filter_pos == "part":
            filter_pos = "v"

        unresolved = self.get_unresolved_items(form, filter_pos)
        self.debug(form, "get_preferred_lemmas", filter_word, filter_pos)
        self.debug(form, "  unresolved items", [(l.word, l.pos, formtypes) for l, formtypes in unresolved])
        if not unresolved:
            self.debug("  no unresolved items, using get_all_lemmas instead")
            unresolved = [(item, None) for item in self.get_all_lemmas(form, filter_pos)]

        if not unresolved and self.allforms.get_lemmas(form, filter_pos):
            print("No matching lemmas", form, filter_pos, self.allforms.get_lemmas(form, filter_pos), file=sys.stderr)

        # Remove rare form of before resolving lemmas
        filtered = [x for x in unresolved if not self.is_rare_lemma(x[0])]
        unresolved = filtered if filtered else unresolved

        self.debug(form, f"  unresolved items ({len(filtered)} passed filter)", [(l.word, l.pos, formtypes) for l, formtypes in unresolved])
        lemmas = []
        for w, formtypes in unresolved:
            resolved_lemmas = self.get_resolved_lemmas(w, form, formtypes)
            self.debug(form, f"  resolved {w.word}:{w.pos} to", [(l.word, l.pos) for l in resolved_lemmas])
            lemmas += resolved_lemmas

        if not lemmas:
            lemmas = [w for w,_ in unresolved]

        if filter_word or filter_pos:
            lemmas = self.filter_lemmas(lemmas, filter_word, filter_pos)
            self.debug(form, f"  filtered {filter_word}/{filter_pos}, remaining", [(l.word, l.pos) for l in lemmas])

        # Remove rare lemmas from resolved lemmas
        filtered_lemmas = self.filter_rare_lemmas(lemmas)
        if len(lemmas) != len(filtered_lemmas):
            self.debug(form, "filtered rare", len(lemmas), [(l.word, l.pos) for l in lemmas], len(filtered_lemmas), [(l.word, l.pos) for l in filtered_lemmas])
        lemmas = filtered_lemmas if filtered_lemmas else lemmas

        # Remove lemmas that appear after a form definition (ie, non-primary lemmas)
        filtered_lemmas = self.filter_secondary_lemmas(lemmas)
        if len(lemmas) != len(filtered_lemmas):
            self.debug(form, "filtered secondary", len(lemmas),  len(filtered_lemmas))
        lemmas = filtered_lemmas if filtered_lemmas else lemmas

        return lemmas

    def get_claimed_lemmas(self, form, pos):
        """ Returns a list of (lemma_obj, [formtypes]) for a given form, pos """

        seen = set()
        items = []

        for word in self.wordlist.get_iwords(form, pos):
            self.debug(form, "claimed", word.word, word.pos, [form, pos])
            if self.is_lemma(word):
                if word not in seen:
                    items.append((word, None))
                    seen.add(word)
                continue

            for lemma, formtypes in word.form_of.items():
                target_pos = None if "onlyin" in formtypes else word.pos
                for lemma_obj in self.wordlist.get_iwords(lemma, target_pos):
                    if lemma_obj not in seen:
                        items.append((lemma_obj, formtypes))
                        seen.add(lemma_obj)

        return items

    def filter_verified_claims(self, form, items):
        """ items is a list of (lemma_obj, [formtypes])
        Returns a list in the same format of the items whose claims
        are validated by a similar declaration in the lemma """

        # TODO: allow formtypes that can't be verified "alternative spelling of", etc
        # [ "form", "alt", "old", "rare", "spell" ]
        return [x for x in items if self.is_lemma(x[0]) or x[0].has_form(form)]

    def get_unresolved_items(self, form, pos):
        """ returns a list of (Word, formtypes) """

        items = []


        # An allforms entry will list lemmas that declare the form as well
        # as lemmas that the form claims to be a form of
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

        claimed_lemmas = self.get_claimed_lemmas(form, pos)
        filtered = self.filter_verified_claims(form, claimed_lemmas)
        if filtered != items:
            self.debug(form, pos, "filtered claims", len(items), len(filtered))
        items = filtered if filtered else claimed_lemmas
        seen = { lemma for lemma, formtypes in items }

        for lemma in self.get_declaring_lemmas(form, pos):
            if lemma not in seen:
                items.append((lemma, None))
                seen.add(lemma)

        return items


    def get_all_lemmas(self, form, pos):
        """ Returns at least one Word for each lemma associated with the form in allforms
        If the lemma has multiple Words, it excludes words that are non-lemmas """

        items = []
        for poslemma in self.allforms.get_lemmas(form, pos):

            lemma_pos, lemma = poslemma.split("|")
            self.debug(form, "get all lemmas", poslemma)

            # for compatability with wiktionary, participles are stored as pos "part"
            # with the lemma being the verb
            # change "part" to "v" so that lookups will successfully find the verb
            if lemma_pos == "part":
                all_words = self.wordlist.get_words(lemma, "v")
            else:
                all_words = self.wordlist.get_words(lemma, lemma_pos)

            if not all_words:
                all_words = [w[0] for w in self.get_unresolved_items(lemma, lemma_pos)]

            lemmas = [w for w in all_words if self.is_lemma(w)]
            new_items = lemmas if lemmas else all_words
            for item in new_items:
                if item not in items:
                    items.append(item)

        return items

    def get_declaring_lemmas(self, form, pos):
        """ Returns a list of Word objects with a matching pos that declare the given form """

        items = []
        for poslemma in self.allforms.get_lemmas(form, pos):

            lemma_pos, lemma = poslemma.split("|")

            # for compatability with wiktionary, participles are stored as pos "part"
            # with the lemma being the verb
            # change "part" to "v" so that lookups will successfully find the verb 
            if lemma_pos == "part":
                lemma_pos = "v"
            self.debug(form, "declaring poslemma", lemma_pos, lemma)
            for word in self.wordlist.get_iwords(lemma, lemma_pos):
                self.debug(form, "declaring", word.word, word.pos, self.is_lemma(word), word.has_form(form))
                if self.is_lemma(word) and word.has_form(form):
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


    def get_all_pos(self, lemmas):
        return sorted(set(l.pos for l in lemmas))

    def get_freq_probs(self, form, all_pos):
        pos_by_prob = self.ngprobs.get_pos_probs(form, all_pos)
        if not pos_by_prob:
            return

        sorted_pos_by_prob = [(None,pos,count) for pos,count in sorted(pos_by_prob.items(), key=lambda x: x[1], reverse=True)]

        if not (len(sorted_pos_by_prob) == 1 or sorted_pos_by_prob[0][2] > 2*sorted_pos_by_prob[1][2]):
            return

        ranked_pos = [pos for form, pos, count in sorted_pos_by_prob]
        best_pos = ranked_pos[0]

        return sorted_pos_by_prob

    def get_ranked_pos(self, form, possible_lemmas):
        """
        Returns a list of (word, pos, count), sorted by count, descending
        """

        all_pos = self.get_all_pos(possible_lemmas)

        if not all_pos:
            return None

        if len(all_pos) == 1:
            return [(None,all_pos[0],1)]

        if "num" in all_pos:
            return [ (form, "num", 1) ] + [ (form, pos, 0) for pos in all_pos if pos != "num" ]

        ng_usage_count = [ (form, pos, self.ngprobs.get_usage_count(form, pos)) for pos in all_pos ]
        ng_usage_count.sort(key=lambda k: (int(k[2])*-1, k[1], k[0]))

        if form == self.DEBUG_WORD:
            print("ng_probs", ng_usage_count)

        return ng_usage_count

    flags_defs = {
        "UNKNOWN": "Word does not appear in lemma database or dictionary",
        "PRONOUN": "Ignoring pronouns",
        "LETTER": "Letter",
        "NODEF": "No definition",
        "FUZZY": "Only has fuzzy sentance matches",
        "DUPLICATE": "Duplicate usage of word with different POS",
        "DUPLICATE-ADJ-ADV": "Adverb duplicates existing adjective",
        "DUPLICATE-ADJ-NOUN": "Noun duplicates existing adjective",
        "DUPLICATE-REFLEXIVE": "Reflexive verb duplicase existing non-reflexive verb",
    }

    def get_flags(self, form, pos):
        flags = []
        pos = pos.lower()

        if not pos:
            raise ValueError(form, "no pos")

        if pos == "none":
            return ["NOUSAGE"]

        if not self.wordlist.has_word(form, pos):
            raise ValueError(form, "no def")

        # remove reflexive verbs if the non-reflexive verb is already on the list
       # if form.endswith("rse") and pos == "v" and (form[:-2],"v") in freq:
       #     flags.append("DUPLICATE-REFLEXIVE")
       #
#        if pos == "v" and any(self.is_irregular_verb(w) for w in self.wordlist.get_words(word, pos)):
#            flags.append("IRREGULAR")

        return flags


    def get_lemma_freq(self, entries):

        lemma_freq = {}
        for form, entry in entries.items():
            lemma = entry.lemma if entry.lemma else form
            pos = entry.pos if entry.pos else "none"

            tag = (lemma, pos)

            if tag not in lemma_freq:
                lemma_freq[tag] = {"count": 0, "usage": []}

            lemma_freq[tag]["count"] += entry.count
            lemma_freq[tag]["usage"].append(f"{entry.count}:{form}")

            self.debug(form, "counting", entry)

        return lemma_freq

    def build_freqlist(self, entries):

        lemma_freq = self.get_lemma_freq(entries)

        freq = {}
        usage = defaultdict(dict)
        count = 1

        for tag, item in sorted(lemma_freq.items(), key=lambda x: (x[1]["count"]*-1, x[0])):
            lemma, pos = tag

            flags = self.get_flags(lemma, pos)

            usage[lemma][pos] = item["count"]

            freq[tag] = {
                "count": item["count"],
                "word": lemma,
                "pos": pos,
                "flags": flags,
                "usage": item["usage"],
            }

            count += 1

        repeatusage = {}
        for lemma in usage:
            if len(usage[lemma].keys()) > 1:
                repeatusage[lemma] = usage[lemma]

        for lemma, all_pos in repeatusage.items():
            best_count = -1
            best_pos = ""
            for pos, count in all_pos.items():
                # ignore anything that's already flagged for dismissal
                if len(freq[(lemma, pos)]["flags"]):
                    continue
                if count > best_count:
                    best_count = count
                    best_pos = pos

            popular_pos = []
            for pos, count in all_pos.items():
                if count < best_count:
                    freq[(lemma, pos)]["flags"].append("DUPLICATE")

        return freq

    def is_primary_lemma(self, word):
        for w in self.wordlist.get_iwords(word.word, word.pos):
            if not self.is_lemma(w):
                return False
            if w == word:
                return True
        return False

    def filter_secondary_lemmas(self, lemmas):
        filtered_lemmas = [lemma for lemma in lemmas if self.is_primary_lemma(lemma)]
        return filtered_lemmas if filtered_lemmas else lemmas

    def is_rare_qualifier(self, qualifier):
        return qualifier and re.match(r"(archaic|dated|obsolete|rare|poco usad|desusad)", qualifier)

    def is_rare_lemma(self, word):
        """
        Returns False if word has any non-form sense not flagged rare/archaic
        """

        has_nonrare_sense = False
        for sense in word.senses:
            if not self.is_rare_qualifier(sense.qualifier) and \
                not (sense.gloss and re.match(r"(archaic|dated|obsolete|rare) form of", sense.gloss)):
                    return False
            else:
                has_nonrare_sense = True
        return has_nonrare_sense

    def filter_rare_lemmas(self, lemmas):
        return [lemma for lemma in lemmas if not self.is_rare_lemma(lemma)]

    def get_most_frequent_lemma(self, lemma_freq, form, pos, possible_lemmas):

        lemmas = []
        for lemma in possible_lemmas:
            if lemma.pos == pos and lemma.word not in lemmas:
                lemmas.append(lemma.word)

        self.debug(form, pos, "get_most_frequent_lemma_list", lemmas)

        if len(lemmas) == 1:
            return lemmas[0]

        if not lemmas:
            return

        if form in lemmas:
            return form

        best = None
        best_count = -1

        # Pick the more common lemma
        # NOTE: this only looks at the count for the raw lemma, not the count of the lemma plus all of its forms
        for lemma in lemmas:
            count = lemma_freq.get((lemma, pos), {}).get("count",-1)
            if count > best_count:
                best = lemma
                best_count = count
            self.debug(form, "get_best_lemma", lemmas, "best:", best, best_count)

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

            usage = [(self.ngprobs.get_usage_count(lemma, pos), lemma) for lemma in lemmas]
            ranked = sorted(usage, key=lambda x: (x[0]*-1, x[1]))
            self.debug(form, pos, "get_best_lemma", lemmas, "no best, using ngprobs frequency", ranked)
            print("$$$$", [form, pos], "get_best_lemma", ranked)

            if ranked[0][0] == ranked[1][0]:
                print("###", form, pos, "get_best_lemma", lemmas, "no best, using first item", ranked)

            return ranked[0][1]

        return best
