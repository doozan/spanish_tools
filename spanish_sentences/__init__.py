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
                    word,oldpos,newpos = line.split(":")

                    if word not in self.tagfixes:
                        self.tagfixes[word] = {}
                    self.tagfixes[word][oldpos] = newpos

        index=0
        with open(datafile) as infile:
            data = json.load(infile)
            for line in data:
                extras, english, spanish, tags = line
                stripped = self.strip_sentence(spanish).strip()

                self.sentencedb.append( (spanish, english) )
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

            for pos in allpos:
                for word in words:

                    if word not in self.tagdb:
                        self.tagdb[word] = {}

                    if word in self.tagfixes and pos in self.tagfixes[word]:
                        pos = self.tagfixes[word][pos]

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


    def get_sentences_from_ids(self, available, count):
        sentences = []
        ids = []

        # strip duplicates and sort
        available = sorted(list(set(available)))

        results = len(available)
        if results <= count:
            ids = range(0,results)
        else:
            step = results/(count+1.0)

            # select sentences over an even distribution of the range
            ids = [ math.ceil((i+1)*step) for i in range(count) ]

    # Randomly select sentences
    #        while count>0:
    #            rnd = random.randint(0,results)-1
    #            if rnd in ids:
    #                continue
    #            ids.append(rnd)
    #            count-=1
    #        ids = sorted(ids)

        for idx in ids:
            sentences.append(self.sentencedb[available[idx]])

        return(sentences)

    def get_sentence_ids(self, lookup, pos):
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

    def get_sentences(self, lookup, pos, count):
        res = self.get_sentence_ids(lookup, pos)

        sentences = self.get_sentences_from_ids(res['ids'], count)
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
