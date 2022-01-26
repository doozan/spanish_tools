#!/usr/bin/python3

import argparse
import os
import re
import sys

from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms
from .spanish_sentences import sentences as spanish_sentences
from .probability import PosProbability

DEBUG_WORD="afueras"

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
        self.freq = {}
        self.all_lemmas = {}
        self.load_ignore(ignore_data)

    def load_ignore(self, ignore_data):
        self.ignore = {line.strip() for line in ignore_data if line.strip() and not line.strip().startswith("#")}

    def process(self, freqlist, minuse=0):
        self.freq = {}
        self.all_lemmas = {}

        entries = self.init_list(freqlist)
        self.resolve_lemmas(entries)
        self.resolve_plurals(entries)
        self.build_freqlist(entries)

        yield("count,spanish,pos,flags,usage")
        for k, item in sorted(
            self.all_lemmas.items(), key=lambda item: (item[1]["count"]*-1, item[1]["word"])
        ):
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

    def init_list(self, freqlist):
        """
        freqlist is an iterable of strings formatted as "[@]word[:pos][ N]"
          @ - optional, word will be treated as an exact lemma, without being resolved further
          word - the word form
          :pos - optional - word will be treated as the given part of speech
          N - count, optional, must be preceeded by a space - the number of occurances of the word
              if N is invalid or not specified, an arbitrary value will be assigned,
              giving greater value to the words appearing earliest in the iterable

        returns: { "form": (pos, count, [lemma1, lemma2]), ... }

        note: pos will be NULL if the word can be a plural multiple types of pos
        """
        # TODO: instead or NULL, return a list of the possible POS?

        lines = {}

        # Read all the lines and do an initial lookup of lemmas
        for linenum, line in enumerate(freqlist):
            word, _, count = line.strip().partition(" ")
            word, _, pos_override = word.partition(":")

            if not count or not count.isdigit():
                if count:
                    word = word + " " + count
                count = str(100000-linenum)

            if word in self.ignore:
                continue

            lemmas = None
            if word.startswith("@"):
                lemmas = [ word[1:] ]
                word = word[1:]

            if pos_override:
                pos = [pos_override]
            else:

                if self.maybe_plural(word):
                    pos = self.get_good_pos(word)
                    #print("maybe plural", word, pos, self.all_forms.get_lemmas(word))
                    #if not len(pos) > 1:
                    #    print("maybe plural", word, pos, self.all_forms.get_lemmas(word))
                    if word == DEBUG_WORD:
                        print("###", word, "maybe_plural", pos)
                else:
                    # TODO: instead of get_ranked_pos, make a new get_best_pos ?
                    # returns multi value if it can't be determined
                    #  - when would they get resolved? how?
                    posrank = self.get_ranked_pos(word)
                    if word == DEBUG_WORD:
                        print("###", word, "ranked_pos", posrank)

                    pos = posrank[:1] if posrank else []

            if not lemmas and len(pos) == 1:
                lemmas = self.get_lemmas(word, pos[0])
                if word == DEBUG_WORD:
                    print("###", word, "getting lemmas", lemmas, posrank)

            lines[word] = (pos, count, lemmas)

        return lines

    def resolve_lemmas(self, lines):

        # Run through the lines again and use the earlier counts to
        # pick best lemmas from words with multiple lemmas
        for word, item in lines.items():
            pos,count,lemmas = item

            if not lemmas or len(lemmas) == 1:
                continue

            if not pos or len(pos) > 1:
                continue

            if word == DEBUG_WORD:
                print("###", word, "resolving lemmas", item)

            lemma = self.get_best_lemma(word, lemmas, pos[0])
            lines[word] = (pos, count, [lemma])

    def resolve_plurals(self, lines):

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
        for word, item in lines.items():
            good_pos,count,lemmas = item
            if not good_pos or len(good_pos) <= 1:
                continue

            if word == DEBUG_WORD:
                print("###", word, "resolving plurals", item)


            # Plurals should use the same POS as the singular, unless the plural usage is more common
            # in which case it should use get_best_pos
            best = None
            best_count = -1

            # Special handling for feminine plurals, stay with the feminine
            # form instead of using the masculine lemma
            if word.endswith("as"):
                item = lines.get(word[:-1])
                if item:
                    lemma_posrank, lemma_count, lemma_lemmas = item
                    if int(lemma_count) > int(count):
                        best = word[:-1]
                        best_count = int(lemma_count)

            if not best:

                checked_lemmas = []
                for poslemma in self.get_preferred_poslemmas(word):
                    p,lemma = poslemma.split("|")
                    if lemma in checked_lemmas:
                        continue

                    item = lines.get(lemma)
                    if not item:
                        continue

                    lemma_posrank, lemma_count, lemma_lemmas = item
                    if not lemma_posrank:
                        continue

                    if lemma_posrank[0] == "v" or lemma_posrank[0] not in good_pos:
                        continue

                    if int(lemma_count) > best_count:
                        best = lemma
                        best_count = int(lemma_count)

            if word == DEBUG_WORD:
                print("##", word, good_pos, count, lemmas, checked_lemmas, best, lines.get(best))

            # If the singular is more popular than the plural, use it
            # sometimes the form is a lemma (gracias, iterj) so the count
            # will be equal
            if best_count > int(count):
                _posrank, _count, _lemmas = lines[best]
                pos = _posrank
                lemmas = _lemmas

                if word == DEBUG_WORD:
                    print(word, "following singular", best)


                #print("resolved plural", word, count, best)

            # No singular form has more usage than the plural,
            # fallback to handling it like any other word
            else:
                #print("popular plural", word, count, best)
                if word == DEBUG_WORD:
                    print(word, "popular plural, not following", best)

                posrank = self.get_ranked_pos(word)
                pos = posrank[:1]
                lemmas = self.get_lemmas(word, pos[0])

                assert lemmas

                if len(lemmas) > 1:
                    lemmas = [self.get_best_lemma(word, lemmas, pos[0])]

            lines[word] = (pos, count, lemmas)
        return

    def maybe_plural(self, word):
        """
        returns True if the form could be a plural
        A form may be plural if it ends with 's' and has any non-verb lemmas that don't match the form
        """
        if not word.endswith("s"):
            return False

        poslemmas = self.all_forms.get_lemmas(word)
        nonverb_lemmas = [x.split("|")[1] for x in poslemmas if not x.startswith("v|")]

        if word == DEBUG_WORD:
            print("###", word, "checking if plural", nonverb_lemmas, poslemmas)

        if len(nonverb_lemmas) and any(x != word for x in nonverb_lemmas):
            return True

    def get_lemmas(self, word, pos):
        """ Returns a list of all possible lemmas for a given word,pos """
        poslemmas = self.all_forms.get_lemmas(word, [pos])
        if word == DEBUG_WORD:
            print("found:", word, pos, poslemmas)
        return [x.split("|")[1] for x in sorted(poslemmas)] if poslemmas else [word]

    def get_preferred_poslemmas(self, word, pos=[]):
        """ Returns a list of preferred lemmas for a given word, pos """
        lemmas = []
        for x in self.all_forms.get_lemmas(word, pos):
            pos, lemma = x.split("|")
            if x not in lemmas and not self.is_rare_lemma(self.wordlist, lemma, pos):
                lemmas.append(x)

        return sorted(lemmas)

    def get_good_pos(self, word):
        """
        Returns a list of all POS for a given word form, excluding
        POS that only have dated/archaic usage
        """
        all_pos = []
        for x in self.all_forms.get_lemmas(word):
            pos, lemma = x.split("|")
            if pos not in all_pos and not self.is_rare_lemma(self.wordlist, lemma, pos):
                all_pos.append(pos)

        return sorted(all_pos)

    def get_ranked_usage(self, word, all_pos, use_lemma=False):
        """
        Returns a list of (word, pos, count), sorted by count, descending
        """

        usage = []
        for pos in all_pos:
            if use_lemma:
                for lemma in self.get_lemmas(word, pos):
                    usage.append((lemma, pos))
            else:
                usage.append(("@" + word, pos))

        res = [ (word, pos, self.sentences.get_usage_count(word, pos)) for word, pos in usage ]
        return sorted(res, key=lambda k: int(k[2]), reverse=True)


    def get_ranked_pos(self, word, use_lemma=False, use_count=False):
        """
        Returns a list of all possible parts of speech, sorted by frequency of use
        """

        all_pos = self.get_good_pos(word)

        if word == DEBUG_WORD:
            print("get_ranked_pos", word, all_pos, use_lemma, use_count)

        if not all_pos:
            return []

        if len(all_pos) == 1:
            return all_pos

        pos_rank = self.get_ranked_usage(word, all_pos, use_lemma)

        if word == DEBUG_WORD:
            print("get_ranked_pos:posrank", word, pos_rank)

        pos_with_usage = [ pos for word,pos,count in pos_rank if count > 0 ]

        if word == DEBUG_WORD:
            print("get_ranked_pos:posrank:with_usage", word, pos_with_usage)

#        if word == DEBUG_WORD:
#            print(word, all_pos, use_lemma)
#            print(pos_rank)
#            print(pos_with_usage)

        if len(pos_with_usage) == 1:
            return pos_with_usage

        if word == DEBUG_WORD:
            print("get_ranked_pos:0")

        # If preferred pos has at least 10 usages and is at least double the second use it
        if pos_rank[0][2] > 10 and pos_rank[0][2] >= 2*(pos_rank[1][2]):
            return [pos for form,pos,count in sorted(pos_rank, key=lambda k: int(k[2]), reverse=True)]

        if word == DEBUG_WORD:
            print("get_ranked_pos:1")


        # Sometimes wiktionary and freeling disagree about the POS for a word, in which case
        # the sentences database will be tagged with freeling's preference and there will
        # be no usage count for any of the wiktionary POS (example 'esas' - wikipedia says determiner/pronoun,
        # but freeling tags it as an adjective

        # If there are usage sentences for multiple pos, let the probabilities table pick
        if not use_lemma:
            pos_by_prob = self.probs.get_pos_probs(word, all_pos)
            if word == DEBUG_WORD:
                print("get_ranked_pos:XX", pos_by_prob)
            if pos_by_prob:
                sorted_pos_by_prob = [(word,pos,count) for pos,count in sorted(pos_by_prob.items(), key=lambda x: x[1])]

                if word == DEBUG_WORD:
                    print("get_ranked_pos:XX+", sorted_pos_by_prob)
                if len(sorted_pos_by_prob) == 1 or sorted_pos_by_prob[0][2] > sorted_pos_by_prob[1][2]:
                    return [pos for word,pos,count in sorted_pos_by_prob]

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
            return self.get_ranked_pos(word, use_lemma=True, use_count=use_count)

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


    def add_count(self, word, pos, count, origword):
        if not pos:
            pos = ["none"]
        tag = (word, pos[0])
        if tag not in self.freq:
            self.freq[tag] = {"count": 0, "usage": []}

        self.freq[tag]["count"] += int(count)
        self.freq[tag]["usage"].append(count + ":" + origword)


    def get_count(self, word, pos):
        tag = (word, pos)
        if tag not in self.freq:
            return -1
        return self.freq[tag]["count"]


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
        if word.endswith("rse") and pos == "v" and (word[:-2],"v") in self.all_lemmas:
            flags.append("DUPLICATE-REFLEXIVE")

        return flags

    def build_freqlist(self, lines):

        for word, item in lines.items():
            pos,count,lemmas = item
            if not lemmas:
                lemmas = [word]
            elif len(lemmas) != 1:
                raise ValueError(word, item)
            self.add_count(lemmas[0], pos, count, word)
            if word == DEBUG_WORD:
                print("###", word, "counting", item)

        wordusage = {}
        count = 1
        for tag, item in sorted(
            self.freq.items(), key=lambda item: (item[1]["count"], item[0]), reverse=True
        ):
            word, pos = tag

            flags = self.get_word_flags(word, pos)

            # Check for repeat usage
            if word not in wordusage:
                wordusage[word] = {}

            wordusage[word][pos] = item["count"]
            #wordusage[word].append(pos)

            self.all_lemmas[tag] = {
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
                if len(self.all_lemmas[(word,pos)]["flags"]):
                    continue
                if count > best_count:
                    best_count = count
                    best_pos = pos

            popular_pos = []
            for pos, count in all_pos.items():
                if count < best_count:
                    self.all_lemmas[(word, pos)]["flags"].append("DUPLICATE")

    def get_best_lemma(self, word, lemmas, pos):
        lemmas = self.get_best_lemmas(self.wordlist, word, lemmas, pos)
        if lemmas and len(lemmas) == 1:
            return lemmas[0]

        best = "_NOLEMMA"
        best_count = -1

        # Pick the more common lemma
        for lemma in lemmas:
            count = self.get_count(lemma, pos)
            if count > best_count:
                best = lemma
                best_count = count

        # Still nothing, just take the first lemma
        if best == "_NOLEMMA" and len(lemmas):
            return lemmas[0]

        return best

    @staticmethod
    def is_rare_lemma(wordlist, lemma, pos):
        # Returns True if all senses of the given lemma, pos are rare/archaic
        for word_obj in wordlist.get_words(lemma, pos):
            for sense in word_obj.senses:
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

    @classmethod
    def get_best_lemmas(cls, wordlist, word, lemmas, pos):
        """
        Return the most likely lemmas for a given word, pos from a list of lemmas
        """

        # remove verb-se if verb is already in lemmas
        if pos == "v":
            lemmas = [x for x in lemmas if not (x.endswith("se") and x[:-2] in lemmas)]

        # Hardcoded fixes for some verb pairs
        if pos == "v":
            if "creer" in lemmas and "crear" in lemmas:
                lemmas.remove("crear")
            if "salir" in lemmas and "salgar" in lemmas:
                lemmas.remove("salgar")

        # remove dated/obsolete
        new_lemmas = [lemma for lemma in lemmas if not cls.is_rare_lemma(wordlist, lemma, pos)]
        if new_lemmas:
            lemmas = new_lemmas
        if len(lemmas) == 1:
            return lemmas

        # discard any lemmas that don't declare this form in their first definition
        new_lemmas = [lemma for lemma in lemmas if cls.form_in_lemma(wordlist, word, lemma, pos)]
        if new_lemmas:
            lemmas = new_lemmas
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
    parser.add_argument("--low-mem", help="Use less memory", action='store_true', default=False)
    parser.add_argument("--minuse", help="Require a lemmas to have a least N total uses", default=0, type=int)
    parser.add_argument("--infile", help="Usage list")
    parser.add_argument("--outfile", help="outfile (defaults to stdout)", default="-")
    parser.add_argument("extra", nargs="*", help="Usage list")
    args = parser.parse_args(params)

    probs = PosProbability(args.probs)

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

    with open(args.dictionary) as wordlist_data:
        cache_words = not args.low_mem
        wordlist = Wordlist(wordlist_data, cache_words=cache_words)

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

def build_freq(params=None):
    flist, args = init_freq(params)
    make_list(flist, args.infile, args.outfile, args.minuse)

if __name__ == "__main__":
    build_freq(sys.argv[1:])

