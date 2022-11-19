import html
import math
import sys
from collections import defaultdict

OLD=True
#OLD=False

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

    def load_overrides(self, *args):
        if OLD:
            self.old_load_overrides(*args)
        else:
            self.new_load_overrides(*args)


    def new_load_overrides(self, datafile, source):
        print("loading", datafile, file=sys.stderr)
        with open(datafile) as infile:

            for line in infile:

                line = line.strip()
                if line.startswith("#"):
                    continue
                word,pos,*forced_pairs = line.split(",")

                ids = []
                for pair in forced_pairs:
                    spa_id, eng_id = pair.split(":")
                    ids.append((spa_id, eng_id))

                self.forced_ids[(word,pos)] = ids
                self.forced_ids_source[(word,pos)] = source
                continue


    def old_load_overrides(self, datafile, source):
        print("loading", datafile, file=sys.stderr)
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

    def get_pos_sentences(self, word, pos, limit, seen=None, allowed_sources=[]):
        if seen is None:
            seen = set()

        forced_sentences, forced_source = self.get_forced_sentences(word, pos, limit, seen)
        if forced_sentences:
            return forced_sentences, forced_source

        sentences, source = self.sentences.get_sentences(word, pos, allowed_sources)
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


    def get_sentences(self, *args):
        if OLD:
            return self.old_get_sentences(*args)
        else:
            return self.new_get_sentences(*args)


    def new_get_sentences(self, items, limit):
        word, pos = items[0]
        seen = set()
        sentences, source = self.get_forced_sentences(word, pos, limit, seen)

#        print(len(self.forced_ids), self.forced_ids.get((word, pos)))
#        print(word, pos, [(s.spa_id, s.spanish) for s in sentences])
#        exit(1)

        if not sentences:
            return ""
        return self.format_sentences(sentences)


    def old_get_sentences(self, items, limit):


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

#            # If the first item doesn't match any sentences, return nothing
#            if not all_sentences:
#                return ""

            self.store_sentences(word, pos, pos_sentences, pos_source)


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

        if not best_sentences:
            return ""

#        if len(items) > 1:
#            if len(set([x for x,y in items])) > 1:
#                with open("get_sentences", "a") as outfile:
#                    print(items, file=outfile)

        if OLD:
            word, pos = items[0]
            with open("sentences.selected", "a") as outfile:
                ids = [ f"{s.spa_id}:{s.eng_id}" for s in best_sentences ]
                print(",".join([word,pos] + ids), file=outfile)

#        print(items, [(s.spa_id, s.spanish) for s in best_sentences])
#        exit(1)

        self.store_credits(best_sentences)
        return self.format_sentences(best_sentences)

    @staticmethod
    def format_sentences(sentences):
        return "\n".join(
            f'<span class="spa">{html.escape(item.spanish)}</span>\n' \
            f'<span class="eng">{html.escape(item.english)}</span>'
            for item in sentences
        )

    def store_credits(self, sentences):
        for sentence in sentences:
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


    def store_sentences(self, word, pos, sentences, source):

        if source not in ("preferred", "exact") and " " not in word:
            return

        if not sentences or len(sentences) != 3:
            return

        if not all(sentence.score >= 55 for sentence in sentences):
            return

        tag = (word, pos)
        if tag in self.dumpable_sentences:
            return

        ids = [ f"{s.spa_id}:{s.eng_id}" for s in sentences ]
        self.dumpable_sentences[tag] = ids


    # (spanish, english, score, spa_id, eng_id)
    def dump_sentences(self, filename):

        try:
            with open(filename, "r") as dumpfile:
                # TODO: this seek probably does nothing
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
