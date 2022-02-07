#!/usr/bin/python3

import argparse
import os
import re
import sys

from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.word import Word
from enwiktionary_wordlist.all_forms import AllForms
from .spanish_sentences import sentences as spanish_sentences
from .probability import PosProbability

DEBUG_WORD=None # set by args

def mem_use():
    with open('/proc/self/status') as f:
        memusage = f.read().split('VmRSS:')[1].split('\n')[0][:-3]

    return int(memusage.strip())


class FrequencyList():

    def __init__(self, wordlist, allforms, sentences, ignore_data, probs):
        self.wordlist = wordlist
        self.all_forms = allforms
        self.sentences = sentences
        self.probs = probs
        self.load_ignore(ignore_data)
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
        entries, multi_lemmas, maybe_plurals = self.init_list(freqlist)
        self.resolve_lemmas(entries, multi_lemmas)
        self.resolve_plurals(entries, maybe_plurals)
        return entries

    def init_list(self, freqlist):
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
        # TODO: instead or NULL, return a list of the possible POS?

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

            if not pos:

                if self.maybe_plural(word):
                    maybe_plurals.append(word)
                    pos = None
                    if word == DEBUG_WORD:
                        print("###", word, "maybe_plural")
                else:
                    posrank = self.get_ranked_pos(word)
                    if word == DEBUG_WORD:
                        print("###", word, "ranked_pos", posrank)

                    # TODO: if get_ranked_pos has a tie,
                    # add the word to a new multi_pos list
                    # and resolve it later
                    pos = posrank[0] if posrank else None

            if not lemma and pos:
                lemmas = self.get_preferred_lemmas(word, pos)
                if word == DEBUG_WORD:
                    print("###", word, "getting lemmas", lemmas, pos)

                if not lemmas:
                    raise ValueError("couldn't find lemma", word, pos)

                if len(lemmas) > 1:
                    if word == DEBUG_WORD:
                        print("###", word, "multi_lemma")
                    multi_lemmas.append(word)
                    lemma = None
                else:
                    lemma = lemmas[0]

            lines[word] = (pos, count, lemma)
#            print(word, lines[word])
#            if linenum > 10:
#                exit()

        return lines, multi_lemmas, maybe_plurals

    def resolve_lemmas(self, lines, multi_lemmas):

        print(f"resolving {len(multi_lemmas)} multi lemmas")

        # Run through the lines again and use the earlier counts to
        # pick best lemmas from words with multiple lemmas
        for word in multi_lemmas:
            item = lines[word]
            pos,count,_ = item

            lemmas = self.get_preferred_lemmas(word, pos)
            lemma = self.get_best_lemma(lines, word, lemmas, pos)

            lines[word] = (pos, count, lemma)

            if word == DEBUG_WORD:
                print("###", word, "resolving lemmas", item, "to", lemma)


    def resolve_plurals(self, lines, maybe_plurals):

        print(f"resolving {len(maybe_plurals)} maybe plurals")

        # Finally, process plurals after all other lemmas have been processed
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
        for word in maybe_plurals:
            item = lines[word]
            _,count,_ = item
            good_pos = self.get_good_pos(word)

            if word == DEBUG_WORD:
                print("###", word, "resolving plurals")

            # Plurals should use the same POS as the singular, unless the plural usage is more common
            # in which case it should use get_best_pos
            best = None
            best_count = -1

            # Special handling for feminine plurals, stay with the feminine
            # form instead of using the masculine lemma
            if word.endswith("as"):
                item = lines.get(word[:-1])
                if item:
                    lemma_pos, lemma_count, lemma_lemmas = item
                    if lemma_count > count:
                        best = word[:-1]
                        best_count = lemma_count

                if word == DEBUG_WORD and best:
                    print(word, "found feminine singular")

            checked_lemmas = []
            if not best:

                preferred = self.get_preferred_poslemmas(word)
                if word == DEBUG_WORD:
                    print(word, "checking lemmas", preferred)

                for poslemma in preferred:

                    p,lemma = poslemma.split("|")
                    if p == "v":
                        continue

                    if lemma in checked_lemmas:
                        continue
                    checked_lemmas.append(lemma)

                    item = lines.get(lemma)
                    if not item:
                        continue

                    if word == DEBUG_WORD:
                        print(word, "checking item", lemma, item, lemma_count, best_count, lemma_count>best_count)

                    lemma_pos, lemma_count, lemma_lemmas = item
                    if not lemma_pos:
                        if word == DEBUG_WORD:
                            print(word, "skipping item, no pos", lemma, item, lemma_count, best_count, lemma_count>best_count)
                        continue

                    #if lemma_pos == "v" or lemma_pos not in good_pos:
                    if lemma_pos not in good_pos:
                        continue

                    if lemma_count > best_count:
                        best = lemma
                        best_count = lemma_count

            if word == DEBUG_WORD:
                print("##", word, good_pos, count, checked_lemmas, best, lines.get(best))

            # If the singular is more popular than the plural, use it
            # sometimes the form is a lemma (gracias, iterj) so the count
            # will be equal
            if best_count > count:
                _pos, _count, _lemma = lines[best]
                pos = _pos
                lemma = _lemma

                if word == DEBUG_WORD:
                    print(word, "following singular", best)


                #print("resolved plural", word, count, best)

            # No singular form has more usage than the plural,
            # fallback to handling it like any other word
            else:
                #print("popular plural", word, count, best)
                if word == DEBUG_WORD:
                    print(word, "popular plural, not following", best, lines.get(best))

                posrank = self.get_ranked_pos(word)
                if not posrank:
                    raise ValueError("no posrank", word, self.all_forms.get_lemmas(word))
                pos = posrank[0]
                lemmas = self.get_preferred_lemmas(word, pos)

                if not lemmas:
                    raise ValueError("No lemmas", word, pos, posrank)

                lemma = self.get_best_lemma(lines, word, lemmas, pos) if len(lemmas) > 1 else lemmas[0]

            lines[word] = (pos, count, lemma)
        return

    def maybe_plural(self, word):
        """
        returns True if the form could be a plural
        A form may be plural if it ends with 's' and has any non-verb lemmas that don't match the form
        """
        if not word.endswith("s"):
            return False

        poslemmas = self.all_forms.get_lemmas(word)
        nonverb_lemmas = sorted(set(x.split("|")[1] for x in poslemmas if not x.startswith("v|")))

        if word == DEBUG_WORD:
            print("###", word, "checking if plural", nonverb_lemmas, poslemmas)

        if len(nonverb_lemmas) and any(x != word for x in nonverb_lemmas):
            return True

    def get_preferred_lemmas(self, word, pos):
        """ Returns a list of preferred lemmas for a given word, pos """
        lemmas = []
        all_lemmas = sorted(set(poslemma.split("|")[1] for poslemma in self.all_forms.get_lemmas(word, pos)))
        preferred_lemmas = [lemma for lemma in all_lemmas if not self.is_rare_lemma(self.wordlist, lemma, pos)]
        if preferred_lemmas:
            return preferred_lemmas
        return all_lemmas

    def get_preferred_poslemmas(self, word, pos=[]):
        """ Returns a list of preferred lemmas for a given word, pos """
        lemmas = []
        for x in self.all_forms.get_lemmas(word, pos):
            pos, lemma = x.split("|")
            if x not in lemmas and not self.is_rare_lemma(self.wordlist, lemma, pos):
                lemmas.append(x)

        return sorted(lemmas)

    def get_all_pos(self, word):
        return sorted(set(x.split("|")[0] for x in self.all_forms.get_lemmas(word)))

    def get_good_pos(self, word):
        """
        Returns a list of all POS for a given word form, excluding
        POS that only have dated/archaic usage
        """
        good_pos = set()
        for x in self.all_forms.get_lemmas(word):
            pos, lemma = x.split("|")
            if not self.is_rare_lemma(self.wordlist, lemma, pos):
                good_pos.add(pos)

        return sorted(good_pos)

    def get_ranked_usage(self, word, all_pos, use_lemma=False):
        """
        Returns a list of (word, pos, count), sorted by count, descending
        """

        new_all_pos = list(all_pos)
        freeling_fixes = []
        # Wiktionary considers tuyo, suyo, cuyo, vuestro, etc to be determiners,
        # but freeling classifies them as adj or art or pron
        # TODO: if "determiner" in all_pos and "adj" or "art" in sentence_pos,
        # treat the adj/art as determiner
        if not use_lemma and "determiner" in new_all_pos:
            for alt in ["art", "adj", "pron"]:
                if alt not in new_all_pos:
                    new_all_pos.append(alt)
                    freeling_fixes.append(alt)

        usage = []
        for pos in new_all_pos:
            if use_lemma:
                for lemma in self.get_preferred_lemmas(word, pos):
                    usage.append((lemma, pos))
            else:
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
                if "v" in new_all_pos and "verb" in sentence_pos:
                    res = [ (word, "v", self.sentences.get_usage_count(word, "verb")) ]
                    res += [ (word, pos, 0) for word, pos in usage if pos != "v" ]
                    #print(f"{word}: using 'verb' count instead of 'v'")
                    return res

                #print(word, "no usage for", new_all_pos, "but usage found for", sentence_pos)



        return res


    def get_ranked_pos(self, word, use_lemma=False):
        """
        Returns a list of all possible parts of speech, sorted by frequency of use
        """

        all_pos = self.get_good_pos(word)
        if not all_pos:
            all_pos = self.get_all_pos(word)

        if word == DEBUG_WORD:
            print("get_ranked_pos", word, all_pos, use_lemma)

        if not all_pos:
            return []

        if len(all_pos) == 1:
            return all_pos

        pos_rank = self.get_ranked_usage(word, all_pos, use_lemma)

        if word == DEBUG_WORD:
            print("get_ranked_pos:posrank", word, pos_rank)

        pos_with_usage = [ pos for word,pos,count in pos_rank if count > 0 ]

        if word == DEBUG_WORD:
            print("get_ranked_pos:posrank:with_usage", word, pos_with_usage, all_pos)

#        if word == DEBUG_WORD:
#            print(word, all_pos, use_lemma)
#            print(pos_rank)
#            print(pos_with_usage)

        if len(pos_with_usage) == 1:
            return pos_with_usage

        # If only one pos has usage, or
        if ( #(pos_rank[0][2] and not pos_rank[1][2]) or
             # preferred pos has at least 10 usages and is notably more used than the secondary
            (pos_rank[0][2] >= 10 and pos_rank[0][2] >= 1.3*(pos_rank[1][2]))
             # preferred pos has at least 4 usages and triple the secondary
            or (pos_rank[0][2] >= 4 and pos_rank[0][2] >= 3*(pos_rank[1][2]))
            ):
            if word == DEBUG_WORD:
                print("get_ranked_pos, found common sentence usage", pos_rank)
            return [pos for form,pos,count in pos_rank]

        if word == DEBUG_WORD:
            print("get_ranked_pos - no overwhelming sentence use", pos_rank)



        # No sentence usage or equal sentence usage, check the prob table
        if not use_lemma:

            pos_by_prob = self.probs.get_pos_probs(word, all_pos)
            if word == DEBUG_WORD:
                print("get_ranked_pos:XX", pos_by_prob)
            if pos_by_prob:
                sorted_pos_by_prob = [(word,pos,count) for pos,count in sorted(pos_by_prob.items(), key=lambda x: x[1], reverse=True)]

                if word == DEBUG_WORD:
                    print("get_ranked_pos:XX+", sorted_pos_by_prob)

                if len(sorted_pos_by_prob) == 1 or sorted_pos_by_prob[0][2] > 2*sorted_pos_by_prob[1][2]:
                    res = [pos for word,pos,count in sorted_pos_by_prob]

                    if word == DEBUG_WORD:
                        print("get_ranked_pos:XX++", res)

                    # Sometimes wiktionary and freeling disagree about the POS for a word, in which case
                    # the sentences database will be tagged with freeling's preference and there will
                    # be no usage count for any of the wiktionary POS (example 'esas' - wikipedia says determiner/pronoun,
                    # but freeling tags it as an adjective

                    if res[0] not in all_pos and "determiner" in all_pos and "determiner" not in res and res[0] in ["adj", "art"]:
                        res[0] = "determiner"

                    if word == DEBUG_WORD:
                        print("get_ranked_pos:XX+!", res, all_pos)

                    return res

        all_pos = self.get_good_pos(word)

        if word == DEBUG_WORD:
            print("get_ranked_pos:2")


        # If the probabilities table doesn't work, take the pos used most in the sentences
        if pos_rank[0][2] > pos_rank[1][2]:
            return [pos for form,pos,count in sorted(pos_rank, key=lambda k: int(k[2]), reverse=True)]

        if word == DEBUG_WORD:
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

            pos_rank = sorted(pos_rank, key=lambda k: int(k[2]), reverse=True)

        if word == DEBUG_WORD:
            print("get_ranked_pos:4")

        # Try with lemma forms
        if pos_rank[0][2] == pos_rank[1][2] and not use_lemma:
            return self.get_ranked_pos(word, use_lemma=True)

        if word == DEBUG_WORD:
            print("get_ranked_pos:5")

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

        if word == DEBUG_WORD:
            print("get_ranked_pos:6")

        return [pos for form,pos,count in sorted(pos_rank, key=lambda k: int(k[2]), reverse=True)]

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

            if form == DEBUG_WORD:
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

    def get_best_lemma(self, entries, word, lemmas, pos):
        lemmas = self.get_best_lemmas(self.wordlist, word, lemmas, pos)
        if lemmas and len(lemmas) == 1:
            return lemmas[0]

        best = "_NOLEMMA"
        best_count = -1

        # Pick the more common lemma
        # NOTE: this only looks at the count for the raw lemma, not the count of the lemma plus all of its forms
        for lemma in lemmas:
            _,count,_ = entries.get(lemma, [None, -1, None])
            if count > best_count:
                best = lemma
                best_count = count
            if word == DEBUG_WORD:
                print("###", word, "get_best_lemma", lemmas, "best:", best, best_count)

        # Still nothing, just take the first lemma
        if best == "_NOLEMMA" and len(lemmas):
#            print("###", word, "get_best_lemma", lemmas, "no best, defaulting to first", lemmas[0])
            return lemmas[0]

        return best

    @staticmethod
    def is_rare_lemma(wordlist, lemma, pos):
        # Returns True if all senses of the given lemma, pos are rare/archaic
        for word_obj in wordlist.get_words(lemma, pos):
            for sense in word_obj.senses:
                # Skip form senses because we're only looking at lemmas
                # TODO: This may be too aggressive, it's discarding (val, noun, Apocopic form of "valle")
                if sense.formtype:
                    continue
                if not (sense.qualifier and re.match(r"(archaic|dated|obsolete|rare)", sense.qualifier)) and \
                    not (sense.gloss and re.match(r"(archaic|dated|obsolete|rare) form of", sense.gloss)):
                        return False
        return True

    @staticmethod
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

    # Some verbs can have the same forms, hard code a list of
    # preferred verbs, lesser verb
    _verb_fixes = [
       ("creer", "crear"),
       ("salir", "salgar"),
       ("salir", "salar"),
       ("prender", "prendar"),
    ]

    @classmethod
    def get_best_lemmas(cls, wordlist, word, lemmas, pos):
        """
        Return the most likely lemmas for a given word, pos from a list of lemmas
        """
        if word == DEBUG_WORD:
            print("###", word, "get_best_lemmas0", lemmas)

        # remove verb-se if verb is already in lemmas
        if pos == "v":
            lemmas = [x for x in lemmas if not (x.endswith("se") and x[:-2] in lemmas)]

        if word == DEBUG_WORD:
            print("###", word, "get_best_lemmas1", lemmas)

        # Hardcoded fixes for some verb pairs
        if pos == "v":
            for preferred, nonpreferred in cls._verb_fixes:
                if preferred in lemmas and nonpreferred in lemmas:
                    lemmas.remove(nonpreferred)

        if word == DEBUG_WORD:
            print("###", word, "get_best_lemmas2", lemmas)

        # remove dated/obsolete
        new_lemmas = [lemma for lemma in lemmas if not cls.is_rare_lemma(wordlist, lemma, pos)]
        if new_lemmas:
            lemmas = new_lemmas
        elif word == DEBUG_WORD:
            print("###", word, "get_best_lemmas3 - all are dated/obsolete")

        if word == DEBUG_WORD:
            print("###", word, "get_best_lemmas3", lemmas)

        if len(lemmas) == 1:
            return lemmas

        # discard any lemmas that don't declare this form in their first definition
        new_lemmas = [lemma for lemma in lemmas if cls.form_in_lemma(wordlist, word, lemma, pos)]
        if new_lemmas:
            lemmas = new_lemmas
        elif word == DEBUG_WORD:
            print("###", word, "get_best_lemmas4 - all are not first declared")

        if word == DEBUG_WORD:
            print("###", word, "get_best_lemmas4", lemmas)

        if len(lemmas) == 1:
            return lemmas

        # if one lemma is the word, use that
        if word in lemmas:
            return [word]

        return lemmas


def init_freq(params):

    parser = argparse.ArgumentParser(description="Lemmatize frequency list")
    parser.add_argument("--ignore", help="List of words to ignore")
    parser.add_argument("--dictionary", help="Dictionary file name", required=True)
    parser.add_argument("--allforms", help="All-forms file name")
    parser.add_argument("--probs", help="Probability data file")
    parser.add_argument("--sentences", help="Sentences file name (DEFAULT: sentences.tsv)")
    parser.add_argument(
        "--data-dir",
        help="Directory contaning the dictionary (DEFAULT: SPANISH_DATA_DIR environment variable or 'spanish_data')",
    )
    parser.add_argument(
        "--custom-dir",
        help="Directory containing dictionary customizations (DEFAULT: SPANISH_CUSTOM_DIR environment variable or 'spanish_custom')",
    )
    parser.add_argument("--formtypes", help="Create a formtypes list intsead of a lemma list", action='store_true')
    parser.add_argument("--low-mem", help="Use less memory", action='store_true', default=False)
    parser.add_argument("--minuse", help="Require a lemmas to have a least N total uses", default=0, type=int)
    parser.add_argument("--infile", help="Usage list")
    parser.add_argument("--outfile", help="outfile (defaults to stdout)", default="-")
    parser.add_argument("--debug", help="debug specific word")
    parser.add_argument("extra", nargs="*", help="Usage list")
    args = parser.parse_args(params)

    probs = PosProbability(args.probs)

    global DEBUG_WORD
    DEBUG_WORD = args.debug

    # allow first positional argument to replace undeclared --infile
    if args.infile == parser.get_default("infile") and args.extra:
        args.infile = args.extra.pop(0)

    args = parser.parse_args(params)

    if not args.sentences:
        args.sentences = "sentences.tsv"

    if not args.data_dir:
        args.data_dir = os.environ.get("SPANISH_DATA_DIR", "spanish_data")

    if not args.custom_dir:
        args.custom_dir = os.environ.get("SPANISH_CUSTOM_DIR", "spanish_custom")

    cache_words = not args.low_mem
    wordlist = Wordlist.from_file(args.dictionary, cache_words=cache_words)

    print("wordlist", mem_use(), file=sys.stderr)
    ignore_data = open(args.ignore) if args.ignore else []

    if args.allforms:
        allforms = AllForms.from_file(args.allforms)
    else:
        allforms = AllForms.from_wordlist(wordlist)
    print("all_forms", mem_use(), file=sys.stderr)

    sentences = spanish_sentences(
        sentences=args.sentences, data_dir=args.data_dir, custom_dir=args.custom_dir
    )
    print("sentences", mem_use(), file=sys.stderr)

    flist = FrequencyList(wordlist, allforms, sentences, ignore_data, probs)
    ignore_data.close()

    return flist, args

def make_list(flist, infile, outfile, minuse):

    with open(infile) as _infile:
        if outfile and outfile != "-":
            _outfile = open(outfile, "w")
        else:
            _outfile = sys.stdout

        for line in flist.process(_infile, minuse):
            _outfile.write(line)
            _outfile.write("\n")

        if outfile:
            _outfile.close()

def make_formtypes_list(flist, infile, outfile):

    with open(infile) as _infile:
        if outfile and outfile != "-":
            _outfile = open(outfile, "w")
        else:
            _outfile = sys.stdout

        for line in flist.formtypes(_infile):
            _outfile.write(line)
            _outfile.write("\n")

        if outfile:
            _outfile.close()

def build_freq(params=None):
    flist, args = init_freq(params)
    if args.formtypes:
        make_formtypes_list(flist, args.infile, args.outfile)
    else:
        make_list(flist, args.infile, args.outfile, args.minuse)

if __name__ == "__main__":
    build_freq(sys.argv[1:])

