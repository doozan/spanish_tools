#!/usr/bin/python3

import argparse
import os
import re
import sys

from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms
from .spanish_sentences import sentences as spanish_sentences
from .probability import PosProbability

from .get_best_lemmas import is_good_lemma, get_best_lemmas

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
        lines = {}

        # Read all the lines and do an initial lookup of lemmas
        for linenum,line in enumerate(freqlist):
            pos = None
            word, _, count = line.strip().partition(" ")
            if not count or not count.isdigit():
                if count:
                    word = word + " " + count
                count = str(100000-linenum)

            if word in self.ignore:
                continue

            if ":" in word:
                word, _, pos = word.partition(":")

            # Delay ambiguous plurals until all lemmas have been processed
            elif self.maybe_plural(word):
                lines[word] = (None, count, None)
                continue

            if not pos:
                posrank = self.get_ranked_pos(word)
                pos = posrank[0] if posrank else "none"

            if word.startswith("@"):
                lemmas = [ word[1:] ]
            else:
                lemmas = self.get_lemmas(word, pos)

            lines[word] = (pos, count, lemmas)
            if len(lemmas) == 1:
                self.add_count(lemmas[0], pos, count, word)

        # Run through the lines again and use the earlier counts to
        # pick best lemmas from words with multiple lemmas
        for word, item in lines.items():

            pos,count,lemmas = item

            # delay processing of plurals
            if pos == None:
                continue

            if len(lemmas) > 1:
                print("multi-lemmas", word, pos, lemmas)
                lemma = self.get_best_lemma(word, lemmas, pos)
                lines[word] = (pos, count, [lemma])
                self.add_count(lemma, pos, count, word)

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

            pos,count,lemmas = item
            if pos != None:
                continue

            posrank = self.get_ranked_pos(word, lemmas, pos)
            pos = posrank[0] if posrank else "none"

            lemmas = self.get_lemmas(word, pos)
            if len(lemmas) == 1:
                lemma = lemmas[0]
            else:
                lemma = self.get_best_lemma(word, lemmas, pos)

            # If the plural resolves to a lemma already in the list, follow that lemma's pos/lemma
            if lemma != word:
                new_pos = None
                # feminine plurals should always follow the feminine singular
                if word.endswith("as") and word[:-1] in lines:
                    new_pos, _, new_lemmas = lines[word[:-1]]
                elif lemma in lines:
                    new_pos, _, new_lemmas = lines[lemma]

                if new_pos and (new_pos != pos or new_lemmas[0] != lemma):
                    # verify that word can actually be a form of the the given lemma, pos (eg the determiner sobre doesn't take sobres)
                    if any(self.wordlist.get_formtypes(new_lemmas[0], new_pos, word)):
                        print("override", word, lemma, pos, new_lemmas[0], new_pos)
                        lemma = new_lemmas[0]
                        pos = new_pos
                    else:
                        print("can't override", word, lemma, pos, new_lemmas[0], new_pos)

            lines[word] = (pos, count, [lemma])
            self.add_count(lemma, pos, count, word)
            continue

            # if there are verbs and non-verbs, remove the verbs
#            if any(p.startswith("v|") for p in pos_lemmas) \
#                and any(not p.startswith("v|") for p in pos_lemmas):
#                    pos_lemmas = [p for p in pos_lemmas if not p.startswith("v|")]

            if word == "bonos":
                print(word, pos_lemmas)

            if len(pos_lemmas) == 1:
                pos, lemma = pos_lemmas[0].split("|")
            else:
                best = -1
                for pos_lemma in pos_lemmas:
                    p, l = pos_lemma.split("|")
                    lemma_count = self.get_count(l, p)
                    if word == "bonos":
                        print(p, l, lemma_count)
                    if lemma_count > best:
                        best = lemma_count
                        pos = p
                        lemma = l

                if best == -1:
                    pos = "none"
                    lemma = word

                    posrank = self.get_ranked_pos(word)
                    pos = posrank[0] if posrank else "none"
                    lemma = self.get_lemmas(word, pos)[0]

                    if pos_lemmas:
                        print("NO LEMMAS FOUND", word, pos_lemmas, pos, lemma)

            lines[word] = (pos, count, [lemma])
            self.add_count(lemma, pos, count, word)

            if word == "bonos":
                print(lines[word])
#                exit()



        self.build_freqlist()

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

    def maybe_plural(self, word):
        """ returns true if the form could be a plural """
        if not word.endswith("s"):
            return False

        if word.startswith("@"):
            return False

        forms = self.all_forms.get_lemmas(word)
        if len(forms) < 2:
            return False

        # Check if it's a lemma with usage
        posrank = self.get_ranked_pos(word)
        first_lemma = self.get_lemmas(word, posrank[0])[0]
        if first_lemma == word:
            return False

        if len(list(f for f in forms if not f.endswith("|"+word))) >= 1:
            return True

    def get_lemmas(self, word, pos):

        lemmas = []
        forms = self.all_forms.get_lemmas(word)
        for form_pos,lemma in [x.split("|") for x in sorted(forms)]:
            if form_pos != pos:
                continue
            if lemma not in lemmas:
                lemmas.append(lemma)
        if not lemmas:
            return [word]

        # remove verb-se if verb is already in lemmas
        if pos == "v":
            lemmas = [x for x in lemmas if not (x.endswith("se") and x[:-2] in lemmas)]

        # resolve lemmas that are "form of" other lemmas
        good_lemmas = set()
        for lemma in lemmas:
            for word_obj in self.wordlist.get_words(lemma, pos):
                good_lemmas |= set(self.wordlist.get_lemmas(word_obj).keys())

        return sorted(good_lemmas)

    def include_word(self, word, pos):
        """ Returns True if the word/pos has a useful sense """
        for lemma in self.get_lemmas(word, pos):
            if is_good_lemma(self.wordlist, lemma, pos):
                return True

    def filter_pos(self, word, all_pos):
        """ Remove pos from list if all of its words are archaic/obsolete """

        res = []
        for pos in all_pos:
            if self.include_word(word, pos):
                res.append(pos)
        return res

    def get_pos(self, word):
        forms = self.all_forms.get_lemmas(word)
        all_pos = []
        for pos,lemma in [x.split("|") for x in sorted(forms)]:
            if pos not in all_pos:
                all_pos.append(pos)

        return self.filter_pos(word, all_pos)

    def get_ranked_pos(self, word, use_lemma=False, use_count=False):
        """
        Returns a list of all possible parts of speech, sorted by frequency of use
        """

        all_pos = self.get_pos(word)

        if not all_pos:
            return []

        if len(all_pos) == 1:
            return all_pos

        usage = []
        for pos in all_pos:
            if use_lemma:
                for lemma in self.get_lemmas(word, pos):
                    usage.append((lemma, pos))
            else:
                usage.append(("@" + word, pos))

        pos_rank = self.rank_usage(usage)
        pos_with_usage = [ pos for word,pos,count in pos_rank if count > 0 ]

#        if word == "gracias":
#            print(word, all_pos, use_lemma)
#            print(pos_rank)
#            print(pos_with_usage)

        if len(pos_with_usage) == 1:
            return pos_with_usage

        # If preferred pos has at least 10 usages and is at least double the second use it
        if pos_rank[0][2] > 10 and pos_rank[0][2] >= 2*(pos_rank[1][2]):
            return [pos for form,pos,count in sorted(pos_rank, key=lambda k: int(k[2]), reverse=True)]

        # If there are usage sentences for multiple pos, let the probabilities table pick
        if not use_lemma:
            pos_by_prob = self.probs.get_pos_probs(word, pos_with_usage)
            if pos_by_prob:
                sorted_pos_by_prob = [(word,pos,count) for pos,count in sorted(pos_by_prob.items(), key=lambda x: x[1])]

                if len(sorted_pos_by_prob) == 1 or sorted_pos_by_prob[0][2] > sorted_pos_by_prob[1][2]:
                    return [pos for word,pos,count in sorted_pos_by_prob]

        # If the probabilities table doesn't work, take the pos used most in the sentences
        if pos_rank[0][2] > pos_rank[1][2]:
            return [pos for form,pos,count in sorted(pos_rank, key=lambda k: int(k[2]), reverse=True)]

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

        # Try with lemma forms
        if pos_rank[0][2] == pos_rank[1][2] and not use_lemma:
            return self.get_ranked_pos(word, use_lemma=True, use_count=use_count)

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

        return [pos for form,pos,count in sorted(pos_rank, key=lambda k: int(k[2]), reverse=True)]


    def rank_usage(self, usage):
        """
        Ranks a list of (word, pos) tuples according to their usage
        Returns a list of (word, pos, count), sorted by count, descending
        """

        res = [ (word, pos, self.sentences.get_usage_count(word, pos)) for word, pos in usage ]

        return sorted(res, key=lambda k: int(k[2]), reverse=True)


    def add_count(self, word, pos, count, origword):
        tag = (word, pos)
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

    def build_freqlist(self):
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
        lemmas = get_best_lemmas(self.wordlist, word, lemmas, pos)
        if len(lemmas) == 1:
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


def build_freq(params=None):
    flist, args = init_freq(params)
    make_list(flist, args.infile, args.outfile, args.minuse)

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


if __name__ == "__main__":
    build_freq(sys.argv[1:])

