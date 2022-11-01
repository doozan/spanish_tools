#!/usr/bin/python3

import ijson
import re
import string

import sys

from collections import defaultdict, namedtuple

Phrase = namedtuple("Phrase", [ "form", "lemma", "start", "end" ])
Sentence = namedtuple("Sentence", [ "english", "spanish", "credits", "eng_id", "eng_user", "eng_score", "spa_id", "spa_user", "spa_score" ])

class SentenceBuilder():

    def __init__(self, allforms, freq, ngramdb, ignored_phrases=[]):
        self.allforms = allforms
        self.freq = freq
        self.ngramdb = ngramdb

        self.ignored_phrases = ignored_phrases

        self.ignored_phrases = ["a la", "lo que", "el que"]

        self.detected_phrases = defaultdict(int)
        self.all_phrases = self.make_all_phrases()


    def get_most_common_lemma(self, lemmas):

        if not lemmas:
            raise ValueError("lemmas must not be empty")

        if len(lemmas) == 1:
            return lemmas[0]

        scores = []
        for lemma in lemmas:
            if " " not in lemma:
                print("unhandled", lemma, lemmas, file=sys.stderr)
            count = self.ngramdb.get_count(lemma)
            scores.append((count,lemma))

        scores.sort()
        if scores[0][0] == scores[1][0]:
            #raise ValueError("Tied lemma scores", scores)
            print("Tied lemma scores", scores, file=sys.stderr)

        return scores[0][1]

    def make_all_phrases(self):
        all_phrases = {}
        all_phrases["alt_case"] = defaultdict(list)

        for orig_form, pos, lemma in self.allforms.all:
            if " " not in lemma or " " not in orig_form:
                continue

            if lemma in self.ignored_phrases:
                continue

            form = orig_form.lower()
            if form != orig_form:
                all_phrases["alt_case"][form].append(orig_form)

            size = len(form.split())
            if size not in all_phrases:
                all_phrases[size] = defaultdict(list)

            existing = all_phrases[size].get(form)
            lemmas = sorted(set(w.word for w in self.freq.get_preferred_lemmas(orig_form, None, pos)))
            if len(lemmas) > 1:
                lemma = self.get_most_common_lemma(lemmas)
            if existing and existing != lemma:
                lemma = self.get_most_common_lemma([existing, lemma])

            all_phrases[size][form] = lemma

#        print("alt case", len(all_phrases["alt_case"]), file=sys.stderr)
        return all_phrases

    def matches_c12n(self, phrase, case_words):
        # Verify that words with capitalization have matching capitalization
        # words that are uppercase in the phrase must match case in the sentence
        # words that are lowercase in the phrase are allowed to be uppercase in the sentence
        phrase_alt_cases = self.all_phrases["alt_case"].get(phrase)
        if not phrase_alt_cases:
            return True

        for case_phrase in phrase_alt_cases:
            matches = True
            for i, case_word in enumerate(case_phrase.split()):
                if case_word.lower() != case_word and case_words[i] != case_word:
                    matches = False
                    break
            if matches:
                return True

    def get_phrases(self, sentence):

        if " ".join(sentence.split()) != sentence:
            print("duplicate whitespace in sentence", [sentence], file=sys.stderr)
            return []
    #        raise ValueError("duplicate whitespace in sentence", [sentence])

        orig_words = sentence.split()
        case_words = [ re.sub('[^ a-záéíñóúüA-ZÁÉÍÓÚÜ0-9:]+', '', w) for w in orig_words ]
        words = [ w.lower() for w in case_words ]
        end = len(words)

        if len(sentence.split()) != len(words):
            print("complicated punctuation", [sentence])
            #raise ValueError("complicated punctuation", [sentence])

        phrases = []

        for start in range(end-1):
            for size in range(2,end-start+1):

                end = start+size
                sentence_phrase = " ".join(words[start:end])

                lemma = self.all_phrases[size].get(sentence_phrase)
                if lemma:
                    if self.matches_c12n(sentence_phrase, case_words[start:end]):
                        phrases.append(Phrase(sentence_phrase,lemma,start,end))


        # Detect phrases that are embedded within a larger phrase
        phrases.sort(key=lambda x: ((x.end-x.start)*-1, x.start))
        to_remove = set()
        for x in range(1, len(phrases)):
            small_phrase = phrases[x]
            for big_phrase in phrases[0:x]:
                if small_phrase.start >= big_phrase.start and small_phrase.end <= big_phrase.end:
                    to_remove.add(x)


#        if len(to_remove):
#            print("removing", sentence, phrases, to_remove, file=sys.stderr)
#        elif len(phrases)>2:
#            print(sentence, phrases, file=sys.stderr)

        # Remove embedded phrases
        for x in sorted(to_remove, reverse=True):
    #        print("del", x, len(phrases))
            del phrases[x]


        # Convert word offsets to character offsets
        char_offset_phrases = []
        for phrase in phrases:
            start_word = phrase.start
            end_word = phrase.end
            start_char = len(" ".join(orig_words[:start_word]))
            end_char = len(" ".join(orig_words[:end_word]))
            char_offset_phrases.append(Phrase(phrase.form, phrase.lemma, start_char, end_char))

            self.detected_phrases[phrase.lemma] += 1


    #    print(sentence)
    #    for phrase in char_offset_phrases:
    #        print(phrase.form, sentence[phrase.start:phrase.end])
        return char_offset_phrases


    def tag_to_pos(self, tag, word, is_phrase):

        lemma = tag["lemma"]
        ctag = tag["ctag"]

        pos = None
        if ctag.startswith("A"):  # and lemma not in ["el", "la", "uno"]:
            pos = "adj"
        elif ctag.startswith("C"):  # and lemma not in ["si", "que"]:
            if lemma not in ["y"]:
                pos = "conj"
        elif ctag.startswith("D"):
            pos = "art"
        elif ctag.startswith("I"):
            pos = "interj"
        elif ctag.startswith("N"):  # and lemma not in ["tom", "mary", "john", "maría"]:
            pos = "prop" if ctag == "NP" else "n"
        elif ctag.startswith("P"):
            pos = "pron"
        elif ctag.startswith("R"):
            if lemma not in ["no"]:
                pos = "adv"
        elif ctag.startswith("S"):
            # if lemma not in ["a", "con", "de", "en", "por", "para"]:
            pos = "prep"
        elif ctag.startswith("V"):
            pos = "part" if ctag.endswith("P") else "v"
        elif ctag.startswith("Z") and not word.isdigit():
            pos = "num"
            lemma = word
        if not pos:
            return []

        # let nouns be proper nouns if they start with an uppercase and most commonly occurr with the uppercase
        if pos == "n" and word[0].isupper() and self.freq.ngprobs.get_preferred_case(word.lower()) == word:
            pos = "prop"

        if pos == "prop":
            lemma = self.freq.ngprobs.get_preferred_case(word.lower())
        else:
            word = word.lower()


        # Use our lemmas so they're the same when we lookup against other things we've lemmatized
        if pos in ("n", "adj", "adv"):
            lemma = self.get_lemmas(word, pos)

        # Unless it's a phrase, then use their lemma
        elif "_" in lemma:
            lemma = word

        # fix for freeling not generating lemmas for verbs with a pronoun suffix
        elif pos == "v":
            if not lemma.endswith("r"):
                lemma = self.get_lemmas(word, pos)


        # Special handling for participles, add adjective and verb lemmas
        if pos == "part":
            adj_lemma = self.get_lemmas(word, "adj")
            adj_res = f"{word}|{adj_lemma}" if adj_lemma != word else word

            verb_lemma = self.get_lemmas(word, "part")
            if verb_lemma == word:
                # no verb
                return [("part-adj", adj_res)]

            verb_res = f"{word}|{verb_lemma}"
            # NOTE: part-verb doesn't match "v", but this is intentional
            return [("part-adj", adj_res), ("part-verb", verb_res)]

        if is_phrase:
            pos = "phrase-" + pos

        if word != lemma:
            return[(pos, f"{word}|{lemma}")]

        return[(pos, word)]

    @staticmethod
    def group_tags(pos_tags):
        res = {}
        for item in pos_tags:
            if not item:
                continue
            pos, wordtag = item
            if pos not in res:
                res[pos] = [wordtag]
            else:
                res[pos] += [wordtag]

        for pos, words in res.items():
            res[pos] = list(dict.fromkeys(words))

        return res

    @staticmethod
    def get_tags(phrase, all_pos):
        tags = []
        for pos in all_pos:
            if phrase.lemma == phrase.form:
                tags.append([pos, phrase.lemma])
            else:
                tags.append([pos, f"{phrase.form}|{phrase.lemma}"])

        if not tags:
            raise ValueError(form, all_pos)
#        print(tags, file=sys.stderr)
        return tags

    def get_phrase_tags(self, pos_tags, sentence, phrases):
        phrase_tags = []

        for phrase in phrases:
            all_pos = list(self.allforms.get_form_pos(phrase.lemma))

            # If the phrase could be an interjection or another part of speech,
            # tag it as an interjection if it looks like an interjection,
            # otherwise tag it using the non-interjection parts of speech
            if len(all_pos) > 1 and "interj" in all_pos:
                if self.has_interjection(phrase.form, sentence):
                    phrase_tags += self.get_tags(phrase, ["interj"])
                else:
                    phrase_tags += self.get_tags(phrase, [p for p in all_pos if p != "interj"])
            else:
                phrase_tags += self.get_tags(phrase, all_pos)

        return phrase_tags

    def tag_interjections(self, pos_tags, sentence):

        res = []
        for pos, wordtag in pos_tags:
            word, _, _ = wordtag.partition("|")

            if pos != "interj" and self.allforms.has_form(word, "interj") and self.has_interjection(word, sentence):
                pos = "interj"

            res.append([pos, wordtag])

        return res

    @staticmethod
    def has_interjection(form, sentence):
        return bool(re.search(r"(^|[:;,.!¡¿]\ ?)" + re.escape(form) + r"([;,.!?]|$)", sentence, re.IGNORECASE))

    def get_lemmas(self, word, pos):

    #    lemmas = [x.split("|")[1] for x in allforms.get_lemmas(word, pos)]
    #    lemmas = freq.get_best_lemmas(wordlist, word, lemmas, pos)

        lemmas = sorted(set(w.word for w in self.freq.get_preferred_lemmas(word, None, pos)))
        if not lemmas:
            return word

        return "|".join(lemmas)


    @classmethod
    def get_sentence(cls, text):
        english, spanish, credits, eng_score, spa_score = text.split("\t")

        # de-prioritize meta sentences
        if "atoeba" in english:
            eng_score = spa_score = 0

        eng_id, eng_user, spa_id, spa_user = cls.parse_credits(credits)
        return Sentence(english, spanish, credits, int(eng_id), eng_user, int(eng_score), int(spa_id), spa_user, int(spa_score))

    @classmethod
    def iter_sentences(cls, filename):

        seen = set()
        with open(filename) as infile:
            for line in infile:
                sentence = cls.get_sentence(line.strip())

                wordcount = len(sentence.spanish.split())

                # ignore sentences with less than 6 or more than 15 spanish words
                if wordcount < 5 or wordcount > 15:
                    continue

                # ignore duplicates
                uniqueid = hash(sentence.spanish)
                if uniqueid in seen:
                    continue
                else:
                    seen.add(uniqueid)

                yield sentence

    @staticmethod
    def iter_tags(filename):
        with open(filename, "r", encoding="utf-8") as infile:
            items = ijson.kvitems(infile, "item")

            for k,v in items:
                if k == "sentences":
                    yield v


    def print_untagged_sentences(self, filename):

        for x, sentence in enumerate(self.iter_sentences(filename)):
            if x==0:
                print("")
            print(sentence.spanish)

    @staticmethod
    def parse_credits(text):
        """ returns eng_id, eng_user, spa_id, spa_user """
        res = re.match(
            r"CC-BY 2.0 \(France\) Attribution: tatoeba.org #([0-9]+) \(([^)]+)\) & #([0-9]+) \(([^)]+)\)",
            text
        )
        return res.groups()

    def print_credits(self, filename):

        users = defaultdict(list)

        for s in self.iter_sentences(filename):
            users[s.eng_user].append(s.eng_id)
            users[s.spa_user].append(s.spa_id)

        print(f"CC-BY 2.0 (France) Attribution: tatoeba.org")
        for user, sentences in sorted(
            users.items(), key=lambda item: (len(item[1]) * -1, item[0])
        ):
            count = len(sentences)
            if count > 1:
                print(f"{user} ({len(sentences)}) #{', #'.join(sorted(sentences))}\n")
            else:
                print(f"{user} #{', #'.join(sorted(sentences))}")


    word_chars = string.ascii_lowercase + "áéíóúüñ"
    word_chars += word_chars.upper()
    @classmethod
    def is_boundary(cls, c):
        return c not in cls.word_chars

    def get_original_form(self, tag, sentence, offset):
        """
        Verbs with pronoun suffixes are tokenized into to individual words by freeling
        This function yields the original, untokenized word
        Offset is used to adjust the begin/end tags because they're given as positions
        within the original source file, not within the sentence
        """

        if not "pos" in tag:
            return tag["form"]

        # Don't mess with multi-word stuff
        if "_" in tag["form"]:
            return tag["form"]

        if not tag["ctag"].startswith("V"):
            return tag["form"]

        start = int(tag["begin"])-offset
        end = int(tag["end"])-offset-1

        while start > 0 and not self.is_boundary(sentence[start-1]):
            start -= 1

        while end < len(sentence)-1 and not self.is_boundary(sentence[end+1]):
            end += 1

        word = sentence[start:end+1]
        return word

    def print_tagged_data(self, sentence_filename, tag_filename, verbose=False):
        tags_iter = self.iter_tags(tag_filename)
        sentence_iter = self.iter_sentences(sentence_filename)

        tagdata = {}
        seen = set()

        count = 0
        for sentence, tag_data in zip(sentence_iter, tags_iter):
            count += 1
            if not count % 1000 and verbose:
                print(count, end="\r", file=sys.stderr)

            sentence_tags = self.get_sentence_tags(sentence, tag_data)
            uniqueid = self.get_fingerprint(sentence_tags)
            if uniqueid in seen:
                continue
            seen.add(uniqueid)

            tag_str = " ".join(
                [f":{tag}," + ",".join(items) for tag, items in sentence_tags.items()]
            )

            print("\t".join(map(str, [
                sentence.english,
                sentence.spanish,
                sentence.credits,
                sentence.eng_score,
                sentence.spa_score,
                tag_str
                ])))


    def get_fingerprint(self, sentence_tags):
        # ignore sentences with the same adj/adv/noun/verb lemma combination
        unique_lemmas = set()
        for pos, tags in sentence_tags.items():
            pos = pos.removeprefix("phrase-")
            if pos not in ["adj", "adv", "n", "v", "part-adj", "part-verb"]:
                continue

            for t in tags:
                word, _, lemma = t.partition("|")
                if not lemma:
                    lemma = word

                if self.allforms.has_lemma(lemma, pos):
                    unique_lemmas.add(lemma)

        return hash(tuple(sorted(unique_lemmas)))

    def get_sentence_tags(self, sentence, tags):

        # Get phrases in sentences
        # Get phrase offsets
        phrases = self.get_phrases(sentence.spanish)

        # Discard interjection phrases that don't look like interjections
        phrases = [p for p in phrases if
            any(pos != "interj" for pos in self.allforms.get_form_pos(p.lemma))
            or self.has_interjection(p.form, sentence.spanish)]

        all_tags = self.get_all_tags(sentence.spanish, tags, phrases)
        all_tags += self.get_phrase_tags(all_tags, sentence.spanish, phrases)
        all_tags = self.tag_interjections(all_tags, sentence.spanish)

        grouped_tags = self.group_tags(all_tags)
#        interj = self.get_interjections(sentence.spanish)
#        if interj:
#            grouped_tags["interj"] = list(map(str.lower, interj))

        return grouped_tags

    def get_all_tags(self, spanish, tags, phrases):
        all_tags = []
        first = True
        for s in tags:
            for t in s["tokens"]:
                if first:
                    offset = int(t["begin"])
                    first = False

                start = int(t["begin"])-offset
                end = int(t["end"])-offset

                is_phrase = any(p.start <= start and p.end >= end for p in phrases)

                form = self.get_original_form(t, spanish, offset)
                pos_tags = []
                for word in sorted(set([form, t["form"]])):
                    pos_tags += self.tag_to_pos(t, word, is_phrase)
                if not pos_tags:
                    continue
                pos_tags = sorted(list(set(pos_tags)))
                all_tags += pos_tags
                for pos_tag in pos_tags:
                    pword, _, plemma = pos_tag[1].partition("|")
                    if not plemma:
                        plemma = pword
                    if "_" in plemma:
                        for word, lemma in zip(pword.split("_"), plemma.split("_")):
                            if word != lemma:
                                all_tags.append(["split", f"{word}|{lemma}"])
                            else:
                                all_tags.append(["split", f"{word}"])

        return all_tags

    def print_detected_phrases():
        for lemma, count in sorted(self.detected_phrases.items(), key=lambda x: x[1]):
            if count > 20:
                print(lemma, count, file=sys.stderr)
