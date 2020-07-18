import sys
import math
import re
import os
import json

class sentences:

    def __init__(self, datafile):

        self.grepdb = []
        self.sentencedb = []
        self.tagdb = {}
        self.tagfixes = {}
        self.filter_ids = {}

        if not os.path.isfile(datafile):
            raise FileNotFoundError(f"Cannot open file: '{datafile}'")

        # Tagfixes must be loaded before the main file
        datafixes = datafile + ".tagfixes"
        if os.path.isfile(datafixes):
            with open(datafixes) as infile:
                for line in infile:
                    line = line.strip()
                    if line.startswith("#") or not ":" in line:
                        continue
                    oldword,oldpos,newword,newpos = line.split(":")

                    if oldword not in self.tagfixes:
                        self.tagfixes[oldword] = {}
                    self.tagfixes[oldword][oldpos] = [newword, newpos]

        # Tagfixes must be loaded before the main file
        datafixes = datafile + ".filter"
        if os.path.isfile(datafixes):
            with open(datafixes) as infile:
                for line in infile:
                    line = line.strip()
                    if line.startswith("#"):
                        continue
                    self.filter_ids[int(line.split(" ")[0])] = 1


        index=0
        with open(datafile) as infile:
            data = json.load(infile)
            for line in data:
                score, eng_id, eng_user, spa_id, spa_user, english, spanish, tags = line
                stripped = self.strip_sentence(spanish).strip()

                if eng_id in self.filter_ids or spa_id in self.filter_ids:
                    continue

                self.sentencedb.append( (spanish, english, score, spa_id, eng_id) )
                self.grepdb.append(stripped)

                self.add_tags_to_db(tags,index)
                index+=1

    def strip_sentence(self, string):
        stripped = re.sub('[^ a-zA-ZáéíñóúüÁÉÍÑÓÚÜ]+', '', string).lower()
        return re.sub(' +', ' ', stripped)

    # tags are in the form:
    # { pos: [word1, word2] }
    def add_tags_to_db(self, tags, index):
        for tagpos,words in tags.items():

            # Past participles count as both adjectives and verbs
            allpos = [ "part", "adj", "verb" ] if tagpos == "part" else [ tagpos ]

            for ipos in allpos:
                for iword in words:
                    pos = ipos

                    wordlist = [iword]
                    if iword in self.tagfixes and pos in self.tagfixes[iword]:
                        wlist,pos = self.tagfixes[iword][ipos]
                        wordlist = wlist.split("|")

                    for word in wordlist:

                        if word not in self.tagdb:
                            self.tagdb[word] = {}

                        if pos not in self.tagdb[word]:
                            self.tagdb[word][pos] = []

                        self.tagdb[word][pos].append(index)


    def get_ids_from_phrase(self, phrase):
        pattern = r"\b" + phrase.strip().lower() + r"\b"

        matches = []
        index = 0
        for item in self.grepdb:
            if re.search(pattern, item):
                matches.append(index)
            index+=1

        return matches


    def get_ids_from_word(self, word):
        return self.get_ids_from_tag("@"+word, "")


    # if pos is set it return only results matching that word,pos
    # if it's not set, return all results matching the keyword
    def get_ids_from_tag(self, word, pos):

        if word not in self.tagdb:
            return []

        results = set()
        if not pos:
            for item in self.tagdb[word]:
                results.update(self.tagdb[word][item])
        elif pos in self.tagdb[word]:
            results = self.tagdb[word][pos]
        else:
            return []

        return list(results)

    def get_sentences_from_ids(self, ids):
        sentences = []
        sentences = [ self.sentencedb[idx] for idx in ids ]
        return sentences

    def get_best_sentence_ids(self, lookup, pos, count, forced_ids):

        ids = []
        source = ""

        res = self.get_all_sentence_ids(lookup, pos)
        # remove forced ids, strip duplicates and sort
        available = sorted(set(res['ids']) - set(forced_ids))

        if forced_ids:
            if len(forced_ids) > count:
                source = "forced"
                forced_ids = forced_ids[:count]
            else:
                source = f"forced/{res['source']}"
            count = count-len(forced_ids)
        else:
            source = res['source']

        if len(available) <= count:
            ids = available
        else:
            # prefer curated list (5/6) or sentences flagged as 5/5 (native spanish/native english)
            best = [ i for i in available if self.sentencedb[i][2] >= 56 ]
            if len(best) < count:
                best = [ i for i in available if self.sentencedb[i][2] >= 55 ]
            if len(best) < count:
                best = [ i for i in available if self.sentencedb[i][2] >= 54 ]

            if len(best) >= count:
                available = best

            step = len(available)/(count+1.0)

            # select sentences over an even distribution of the range
            ids = [ available[math.ceil((i)*step)] for i in range(count) ]

        return { "ids": forced_ids + ids, "source": source }

    def get_all_sentence_ids(self, lookup, pos):
        ids = []
        lookup = lookup.strip().lower()
        pos = pos.lower()
        source = "exact"

        if pos in [ "phrase" ] or " " in lookup:
            ids = self.get_ids_from_phrase(lookup)
        else:
            word = lookup.strip()
            ids = self.get_ids_from_tag(word, pos)

            if not len(ids):
                source = "literal"
                if pos != "INTERJ":
                    ids = self.get_ids_from_word(word)

        return { "ids": ids, "source": source }

    def itemtags_to_ids(self, items):
        return [ idx for idx in range(0,len(self.sentencedb)) if f"{self.sentencedb[idx][3]}:{self.sentencedb[idx][4]}" in items ]

    def get_sentences(self, lookup, pos, count, forced_items=[]):

        # Convert sentence id to index of sentencedb
        forced_ids = []
        if forced_items and len(forced_items):
            forced_ids = self.itemtags_to_ids(forced_items)

        res = self.get_best_sentence_ids(lookup, pos, count, forced_ids)

        sentences = self.get_sentences_from_ids(res['ids'])
        return { "sentences": sentences, "matched": res['source'] }


    def get_all_pos(self, word):
        word = word.lower()
        if word in self.tagdb:
            return list(self.tagdb[word].keys())
        return []

    def get_usage_count(self, word, pos):
        if word in self.tagdb and pos in self.tagdb[word]:
            return len(self.tagdb[word][pos])
        else:
            return 0
