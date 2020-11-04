#!/usr/bin/python3

import argparse
import os
import re

from enwiktionary_wordlist.wordlist import Wordlist
import spanish_sentences

class FrequencyList():

    def __init__(self, wordlist, sentences):
        self.wordlist = wordlist
        self.sentences = sentences
        self.freq = {}
        self.all_lemmas = {}


    def process(self, freqlist, ignore_file):
        self.freq = {}
        self.all_lemmas = {}

        ignore = set()
        lines = {}

        # If there's an ignore list specified, load it
        if ignore_file:
            with open(ignore_file) as infile:
                ignore = {line.strip() for line in infile if not line.startswith("#") and line.strip()}

        # Read all the lines and do an initial lookup of lemmas
        for line in freqlist:
            word, count = line.strip().split(" ")
            if word in ignore:
                continue

            posrank = self.get_ranked_pos(word)
            pos = posrank[0] if posrank else "none"
            lemmas = self.get_lemmas(word, pos)
            lines[word] = (pos, count, lemmas)
            if len(lemmas) == 1:
                self.add_count(lemmas[0], pos, count, word)

        # Run through the lines again and use the earlier counts to
        # pick best lemmas from words with multiple lemmas
        for word, item in lines.items():
            pos,count,lemmas = item
            if len(lemmas) > 1:
                lemma = self.get_best_lemma(word, lemmas, pos)
                self.add_count(lemma, pos, count, word)

        self.build_freqlist()

        yield("count,spanish,pos,flags,usage")
        for k, item in sorted(
            self.all_lemmas.items(), key=lambda item: (item[1]["count"], item[1]["word"]), reverse=True
        ):
            if len(item["flags"]) == 1 and "LITERAL" in item["flags"]:
                item["flags"].append("CLEAR")

            if not len(item["flags"]):
                item["flags"].append("CLEAR")
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


    def get_lemmas(self, word, pos):

        lemmas = []
        formtypes = self.wordlist.all_forms.get(word, {}).get(pos, {})
        for formtype, form_lemmas in formtypes.items():
            lemmas += form_lemmas
        if not lemmas:
            return [word]

        # remove verb-se if verb is already in lemmas
        if pos == "verb":
            lemmas = [x for x in lemmas if not (x.endswith("se") and x[:-2] in lemmas)]


        # resolve lemmas that are "form of" other lemmas
        good_lemmas = set()
        for lemma in lemmas:
            for word_obj in self.wordlist.get_words(lemma, pos):
                good_lemmas |= set(self.wordlist.get_lemmas(word_obj).keys())

        return sorted(good_lemmas)

    def include_word(self, word, pos):
        for lemma in self.get_lemmas(word, pos):
            for word_obj in self.wordlist.get_words(lemma, pos):
                for sense in word_obj.senses:
                    if not re.match("(obsolete|archaic)", sense.qualifier) and \
                        not re.match("(obsolete|archaic) form of", sense.gloss):
                            return True


    def filter_pos(self, word, all_pos):
        """ Remove pos from list if all of its words are archaic/obsolete """

        res = []
        for pos in all_pos:
            if self.include_word(word, pos):
                res.append(pos)
        return res

    def get_ranked_pos(self, word, use_lemma=False):
        """
        Returns a list of all possible parts of speech, sorted by frequency of use
        """

        all_pos = self.wordlist.all_forms.get(word, {}).keys()
        all_pos = self.filter_pos(word, all_pos)

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

        # If there's a tie, take non-verbs over verbs
        # If there's still a tie, use the lemam forms
        # Still tied? prefer adj > noun > non-verb > verb
        if len(pos_rank) > 1 and pos_rank[0][2] == pos_rank[1][2]:

            top_count = pos_rank[0][2]

            # prefer non-verbs over verbs
            if top_count > 0 or use_lemma:
                for i, (form, pos, count) in enumerate(pos_rank):
                    if count != top_count:
                        break
                    if pos != "verb":
                        count += 1
                    pos_rank[i] = (form, pos, count)

                pos_rank = sorted(pos_rank, key=lambda k: int(k[2]), reverse=True)

            # Try with lemma forms
            if pos_rank[0][2] == pos_rank[1][2] and not use_lemma:
                return self.get_ranked_pos(word, use_lemma=True)

            for i, (form, pos, count) in enumerate(pos_rank):
                if count != top_count:
                    break
                if pos == "adj":
                    count += 3
                elif pos == "noun":
                    count += 2
                elif pos != "verb":
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
        "COMMON": "Common filler word",
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
        if word.endswith("rse") and pos == "verb" and (word[:-2],"verb") in self.all_lemmas:
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
            # flag the most common "filler" words (pronouns, articles, etc)
            if count < 200 and pos not in ["adj", "adv", "noun", "verb"]:
                flags.append("COMMON")

            # Check for repeat usage
            if word not in wordusage:
                wordusage[word] = {}
            #        else:
            #            flags.append("DUPLICATE")

            wordusage[word][pos] = item["count"]

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
                if count < (best_count / 2):
                    self.all_lemmas[(word, pos)]["flags"].append(
                        "LESSUSED-" + "-".join(all_pos)
                    )
                else:
                    popular_pos.append(pos)

            # only flag dups if the adjective usage isn't flagged
            if "adj" in popular_pos and len(self.all_lemmas[(word,"adj")]["flags"]) == 0:
                if "adv" in popular_pos:
                    self.all_lemmas[(word, "adv")]["flags"].append("DUPLICATE-ADJ-ADV")
                if "noun" in popular_pos:
                    self.all_lemmas[(word, "noun")]["flags"].append("DUPLICATE-ADJ-NOUN")


#    def word_is_only_form(self, word, lemma, pos):
#        if word == lemma:
#            return True
##
#        words = self.wordlist.get_words(lemma, pos)
#        for formtype, forms in words[0].forms.items():
##            if word in forms:
#                return False
#
#        return True

    def word_is_feminine(self, word, pos):
        words = self.wordlist.get_words(word, pos)
        return words[0].pos == "f"

    def word_is_masculine(self, word, pos):
        words = self.wordlist.get_words(word, pos)
        return words[0].pos == "m"
#        return "f" not in word.pos:
#            return True

    def form_in_lemma(self, form, lemma, pos):
        if form == lemma:
            return True

        words = self.wordlist.get_words(lemma, pos)
        for formtype, forms in words[0].forms.items():
            if form in forms:
                return True

    def get_best_lemma(self, word, lemmas, pos):
        """
        Return the most frequently used lemma from a list of lemmas
        """

        # Hardcoded fixes for some verb pairs
        if pos == "verb":
            if "creer" in lemmas and "crear" in lemmas:
                lemmas.remove("crear")
            if "salir" in lemmas and "salgar" in lemmas:
                lemmas.remove("salgar")

        best = "_NOLEMMA"
        best_count = -1

#        if word in ["media"]: # , "dispuestas", "hincha", "zurra", "cierne"]:
#            import pdb; pdb.set_trace()

        # discard any lemmas that don't declare this form in their first definition
        lemmas = [lemma for lemma in lemmas if self.form_in_lemma(word, lemma, pos)]
        if len(lemmas) == 1:
            return lemmas[0]

        # If word is a feminine noun that could be a lemma or could
        # be a form of a masculine noun (hamburguesa), remove the
        # masculine lemma
        if pos == "noun":
            if any(self.word_is_feminine(lemma, pos) for lemma in lemmas):
                lemmas = [lemma for lemma in lemmas if not self.word_is_masculine(lemma, pos)]
                if len(lemmas) == 1:
                    return lemmas[0]

        # if one lemma is the word, use that
        if word in lemmas:
            return word

        # Pick the more common lemma
        for lemma in lemmas:
            if self.get_count(lemma, pos) > best_count:
                best = lemma

        # Still nothing, just take the first lemma
        if best == "_NOLEMMA" and len(lemmas):
            return lemmas[0]

        return best




if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Lemmatize frequency list")
    parser.add_argument("file", help="Frequency list")
    parser.add_argument("--ignore", help="List of words to ignore")
    parser.add_argument("--dictionary", help="Dictionary file name", required=True)
    parser.add_argument("--sentences", help="Sentences file name (DEFAULT: sentences.tsv)")
    parser.add_argument(
        "--data-dir",
        help="Directory contaning the dictionary (DEFAULT: SPANISH_DATA_DIR environment variable or 'spanish_data')",
    )
    parser.add_argument(
        "--custom-dir",
        help="Directory containing dictionary customizations (DEFAULT: SPANISH_CUSTOM_DIR environment variable or 'spanish_custom')",
    )
    args = parser.parse_args()

    if not args.sentences:
        args.sentences = "sentences.tsv"

    if not args.data_dir:
        args.data_dir = os.environ.get("SPANISH_DATA_DIR", "spanish_data")

    if not args.custom_dir:
        args.custom_dir = os.environ.get("SPANISH_CUSTOM_DIR", "spanish_custom")

    with open(args.dictionary) as infile:
        wordlist = Wordlist(infile)

    sentences = spanish_sentences.sentences(
        sentences=args.sentences, data_dir=args.data_dir, custom_dir=args.custom_dir
    )

    flist = FrequencyList(wordlist, sentences)

    with open(args.file) as infile:
        for line in flist.process(infile, args.ignore):
            print(line)
