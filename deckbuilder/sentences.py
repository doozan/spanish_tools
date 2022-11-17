import html
import math
import sys
from collections import defaultdict

class SentenceSelector():

    def __init__(self, sentences, preferred, forced):
        self.sentences = sentences

        self.forced_ids = {}
        self.forced_ids_source = {}

        self.credits = {}
        self.dumpable_sentences = {}

        # Forced/preferred items must be processed last
        for datafile in preferred:
            self.load_overrides(datafile, "preferred")

        for datafile in forced:
            self.load_overrides(datafile, "forced")

    def load_overrides(self, datafile, source):
        with open(datafile) as infile:

            for line in infile:

                line = line.strip()
                if line.startswith("#"):
                    continue
                word,pos,*forced_pairs = line.split(",")

                ids = []
                valid = True
                for pair in forced_pairs:
                    spa_id, eng_id = pair.split(":")

                    sentence = self.sentences.get_sentence(spa_id)
                    if not sentence:
                        print(f"{source} sentences no longer exist for {word},{pos}, ignoring...", file=sys.stderr)
                        valid = False
                        break

                    ids.append((sentence.spa_id, sentence.eng_id))

                    if source == "preferred":

                        if sentence.score < 55:
                            print(f"{source} score for {word},{pos} has dropped below 55, ignoring...", file=sys.stderr)
                            valid = False
                            break

                        if not self.sentences.has_lemma(word, pos, sentence.spa_id):
                            if self.sentences.has_lemma(word, "phrase-" + pos, sentence.spa_id):
                                print(f"{source} sentences for {word},{pos} contain phrases, ignoring...", file=sys.stderr)
                                valid = False
                                break

                            elif pos == "interj":
                                print(f"! {source} sentences no longer has {word},{pos}, ignoring...", file=sys.stderr)
                                valid = False
                                break

                if valid:
                    self.forced_ids[(word,pos)] = ids
                    self.forced_ids_source[(word,pos)] = source


    def get_forced_ids(self, word, pos):
        forced_ids = self.forced_ids.get((word,pos))
        if not forced_ids:
            return [], None
        source = self.forced_ids_source.get((word,pos))
        return forced_ids, source

    def get_forced_sentences(self, word, pos, limit, seen):
        forced_ids, forced_source = self.get_forced_ids(word, pos)

        sentences = []
        for forced_id in forced_ids:
            spa_id, eng_id = forced_id
            if spa_id not in seen and eng_id not in seen:
                sentence = self.sentences.get_sentence(spa_id)
                sentences.append(sentence)
            seen.add(spa_id)
            seen.add(eng_id)
            if len(sentences) == limit:
                break

        return sentences, forced_source

    def get_pos_sentences(self, word, pos, limit, seen, allowed_sources):

        forced_sentences, forced_source = self.get_forced_sentences(word, pos, limit, seen)
        if forced_sentences:
            return forced_sentences, forced_source

        sentences, source = self.sentences.get_all_sentences(word, pos, allowed_sources)
        best_sentences = self.select_best_sentences(sentences, limit, seen)
        return best_sentences, source

    def select_best_sentences(self, all_sentences, limit, seen):

        # Find the highest scoring sentences without repeating the english or spanish ids
        # prefer curated list (5/6) or sentences flagged as 5/5 (native spanish/native english)
        scored = defaultdict(list)
        for sentence in all_sentences:
            score = sentence.score
            scored[score].append(sentence)

        selected = []

        # for each group of scored sentences:
        # if the group offers less than we need, add them all to ids
        # if it has more, add them all to available and let the selector choose
        for score in sorted( scored.keys(), reverse=True ):

            needed = limit-len(selected)
            if needed < 1:
                break

            available = []
            for sentence in scored[score]:
                eng_id = sentence.eng_id
                spa_id = sentence.spa_id
                if eng_id not in seen and spa_id not in seen:
                    seen.add(eng_id)
                    seen.add(spa_id)
                    available.append(sentence)

            if len(available) <= needed:
                selected += available
            else:
                step = len(available)/(needed+1.0)

                # select sentences over an even distribution of the range
                selected += [ available[math.ceil(i*step)] for i in range(needed) ]


        return selected

    def _get_sentences(self, items, limit):

        all_sentences = {}
        source = None
        seen = set()

        for word, pos in items:
            allowed_sources = ["exact", "phrase"]
            # Only allow literal matches for the primary pos
            if not all_sentences:
                allowed_sources.append("literal")

            # if there are multiple word/pos pairs specified, ideally use results from each equally
            # However, if one item doesn't have enough results we will use more results from this item
            # Thus, we need to retrieve "limit" items, as we could be using them all if the other has none
            pos_sentences, pos_source = self.get_pos_sentences(word, pos, limit, seen, allowed_sources)
            if pos_sentences:
                all_sentences[pos] = pos_sentences
                if not source:
                    source = pos_source

        # Take the first sentence from each pos, then the second, etc
        # until 'limit' sentences have been selected
        best_sentences = []
        for idx in range(limit):
            for pos, sentences in all_sentences.items():
                if len(sentences)>idx:
                    best_sentences.append(sentences[idx])
                if len(best_sentences) == limit:
                    break
            if len(best_sentences) == limit:
                  break

        return { "sentences": best_sentences, "matched": source }
















    def get_sentences(self, items, count):

        results = self._get_sentences(items, count)
        self.store_credits(results)

        if len(results["sentences"]):
            return self.format_sentences(results["sentences"])

        return ""

    @staticmethod
    def format_sentences(sentences):
        return "\n".join(
            f'<span class="spa">{html.escape(item.spanish)}</span>\n' \
            f'<span class="eng">{html.escape(item.english)}</span>'
            for item in sentences
        )

    def store_credits(self, results):
        for sentence in results["sentences"]:
            spa_user = sentence.spa_user
            eng_user = sentence.eng_user
            spa_id = sentence.spa_id
            eng_id = sentence.eng_id

            for user in [spa_user, eng_user]:
                if user not in self.credits:
                    self.credits[user] = []
            self.credits[spa_user].append(str(spa_id))
            self.credits[eng_user].append(str(eng_id))


    def dump_credits(self, filename):
        with open(filename, "w") as outfile:
            outfile.write(
                f"The definitions in this deck come from wiktionary.org and are used in accordance with the with the CC-BY-SA license.\n\n"
            )
            outfile.write(
                f"The sentences in this deck were contributed to tatoeba.org by the following users and are used in accordance with the CC-BY 2.0 license:\n\n"
            )
            for user, sentences in sorted(
                self.credits.items(), key=lambda item: (len(item[1]) * -1, item[0])
            ):
                count = len(sentences)
                if count > 1:
                    if count > 5:
                        outfile.write(
                            f"{user} ({len(sentences)}) #{', #'.join(sorted(sentences[:3]))} and {len(sentences)-3} others\n"
                        )
                    else:
                        outfile.write(
                            f"{user} ({len(sentences)}) #{', #'.join(sorted(sentences))}\n"
                        )
                else:
                    outfile.write(f"{user} #{', #'.join(sorted(sentences))}\n")




    def store_sentences(self, lookups):

        for word, pos in lookups:
            tag = (word, pos)
            if tag in self.dumpable_sentences:
                continue

            results = self._get_sentences([[word, pos]], 3)
            if not results:
                continue

            if results["matched"] not in ("preferred", "exact") and " " not in word:
                continue

            if len(results["sentences"]) != 3:
                continue

            if all(sentence.score >= 55 for sentence in results["sentences"]):
                ids = [ f"{sentence.spa_id}:{sentence.eng_id}" for sentence in results["sentences"] ]
                self.dumpable_sentences[tag] = ids


    # (spanish, english, score, spa_id, eng_id)
    def dump_sentences(self, filename):

        try:
            with open(filename, "r") as dumpfile:
                dumpfile.seek(0)
                for line in dumpfile:
                    line = line.strip()
                    word,pos,*forced_itemtags = line.split(",")
                    wordtag = (word, pos)
                    if wordtag not in self.dumpable_sentences:
                        self.dumpable_sentences[wordtag] = forced_itemtags
        except IOError:
            pass

        print(f"dumping {len(self.dumpable_sentences)} sentences to {filename}")
        with open(filename, "w") as dumpfile:
            dumpfile.seek(0)
            dumpfile.truncate()
            for tag, ids in sorted(self.dumpable_sentences.items()):
                word, pos = tag
                row = [word, pos] + ids

                dumpfile.write(",".join(row))
                dumpfile.write("\n")
