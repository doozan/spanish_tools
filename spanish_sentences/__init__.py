import sys
import math
import re
import os

class sentences:

    def __init__(self, datafile):

        self.grepdb = []
        self.sentencedb = []
        self.tagdb = {}
        self.tagfixes = {}

        if not os.path.isfile(datafile):
            print("Cannot find data file:", datafile)

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
            for line in infile:
                english, spanish, tagged, extras = line.split("\t",4)
                stripped = self.strip_sentence(spanish).strip()
                tagged = tagged.strip()

                self.tag_interjections(spanish, index)
                self.sentencedb.append( (spanish, english) )
                self.grepdb.append(stripped)

                for tag in tagged.split(" "):
                    self.add_tag_to_db(tag,index)
                index+=1


    def strip_sentence(self, string):
        stripped = re.sub('[^ a-zA-ZáéíñóúüÁÉÍÑÓÚÜ]+', '', string).lower()
        return re.sub(' +', ' ', stripped)

    def get_interjections(self, string):

        pattern = r"""(?x)(?=          # use lookahead as the separators may overlap (word1. word2, blah blah) should match word1 and word2 using "." as a separator
            (?:^|[:;,.¡!¿]\ ?)         # Punctuation (followed by an optional space) or the start of the line
            ([a-zA-ZáéíñóúüÁÉÍÑÓÚÜ]+)  # the interjection
            (?:[;,.!?]|$)              # punctuation or the end of the line
        )"""
        return re.findall(pattern, string, re.IGNORECASE)


    # tags usually look like noun:word
    # but can also look look noun:word1|word1|word2

    def add_tag_to_db(self, tag, index):
        pos,word = tag.split(":")

        for word in list(dict.fromkeys(word.split("|"))):
            word = word.lower()
            if word not in self.tagdb:
                self.tagdb[word] = {}

            if word in self.tagfixes and pos in self.tagfixes[word]:
                pos = self.tagfixes[word][pos]

            if pos not in self.tagdb[word]:
                self.tagdb[word][pos] = []

            self.tagdb[word][pos].append(index)



    def tag_interjections(self, sentence, index):
        for word in self.get_interjections(sentence):
            self.add_tag_to_db("interj:"+word, index)

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


    def get_best_pos(self, word, all_pos=None, debug=False):
        word = word.lower()

        best_pos = ""
        best_count = -1
        if word in self.tagdb:
            if not all_pos:
                all_pos = self.tagdb[word]
            for pos in all_pos:
                pos = pos.lower()
                if pos in self.tagdb[word]:
                    count = len(self.tagdb[word][pos])
                    if debug:
                        print(count,word,pos)
                    if count > best_count:
                        best_pos = pos
                        best_count = count
                elif debug:
                    print(0,word,pos)

        return { 'count': best_count, 'pos': best_pos }
