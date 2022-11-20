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
                continue

    def get_sentences(self, word, pos, limit):
        forced_ids = self.forced_ids.get((word,pos), [])

        sentences = []
        for forced_id in forced_ids:
            spa_id, eng_id = forced_id
            sentence = self.sentences.get_sentence(spa_id)
            sentences.append(sentence)
            if len(sentences) == limit:
                break

        if not sentences:
            return ""
        return self.format_sentences(sentences)

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
