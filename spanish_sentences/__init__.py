import sys
import math
import re
import os
import json

IDX_SPANISH=0
IDX_ENGLISH=1
IDX_SCORE=2
IDX_SPAID=3
IDX_ENGID=4

def make_tag(word, pos):
    return pos.lower() + ":" + word.lower()

class sentences:

    def __init__(self, sentences="sentences.json", data_dir=None, custom_dir=None):

        self.grepdb = []
        self.sentencedb = []
        self.tagdb = {}
        self.id_index = {}
        self.tagfixes = {}
        self.tagfix_count = {}
        self.filter_ids = {}
        self.forced_ids = {}
        self.forced_ids_source = {}

        if not data_dir:
            data_dir = os.environ.get("SPANISH_DATA_DIR", "spanish_data")

        if not custom_dir:
            custom_dir = os.environ.get("SPANISH_CUSTOM_DIR", "spanish_custom")

        dataprefix = os.path.splitext(sentences)[0]

        # Tagfixes must be loaded before the main file
        for datafile in [ os.path.join(dirname, dataprefix + ".tagfixes") for dirname in [ data_dir, custom_dir ] if dirname ]:
            if not os.path.isfile(datafile):
                continue
            with open(datafile) as infile:
                for line in infile:
                    line = line.strip()
                    if line.startswith("#") or not ":" in line:
                        continue
                    oldword,oldpos,newword,newpos = line.split(":")

                    if oldword not in self.tagfixes:
                        self.tagfixes[oldword] = {}
                    self.tagfixes[oldword][oldpos] = [newword, newpos]

        # Ignore list must be loaded before the main file
        for datafile in [ os.path.join(dirname, dataprefix + ".ignore") for dirname in [ data_dir, custom_dir ] if dirname ]:
            if not os.path.isfile(datafile):
                continue
            with open(datafile) as infile:
                self.filter_ids = set( int(line.strip().split(" ",1)[0]) for line in infile if not line.startswith("#") )

        datafile = os.path.join(data_dir, sentences)
        if not os.path.isfile(datafile):
            raise FileNotFoundError(f"Cannot open file: '{datafile}'")

        index=0
        with open(datafile) as infile:
            data = json.load(infile)
            for line in data:
                score, eng_id, eng_user, spa_id, spa_user, english, spanish, tags = line
                stripped = self.strip_sentence(spanish).strip()

                if eng_id in self.filter_ids or spa_id in self.filter_ids:
                    continue

                self.sentencedb.append( [spanish, english, score, spa_id, eng_id] )
                self.grepdb.append(stripped)

                self.id_index[f"{spa_id}:{eng_id}"] = index

                self.add_tags_to_db(tags,index)
                index+=1

        for word,target in self.tagfixes.items():
            if word not in self.tagfix_count:
                print(f"Tagfix: {word} {target} does not match any sentences", file=sys.stderr)

        # Forced/preferred items must be processed last
        for source in [ "preferred", "forced" ]:
            for datafile in [ os.path.join(dirname, dataprefix + "." + source) for dirname in [ data_dir, custom_dir ] if dirname ]:
                if not os.path.isfile(datafile):
                    continue
                with open(datafile) as infile:

                    for line in infile:
                        line = line.strip()
                        if line.startswith("#"):
                            continue
                        word,pos,*forced_itemtags = line.split(",")
                        wordtag = make_tag(word, pos)
                        ids = self.itemtags_to_ids(forced_itemtags)
                        if None in ids:
                            if source == "preferred":
                                print(f"preferred sentences no longer exist for {word},{pos}, ignoring...", file=sys.stderr)
                                continue
                            else:
                                for index in range(len(forced_itemtags)):
                                    if self.forced_ids[wordtag][index] is None:
                                        raise ValueError(f"{source} sentences {forced_itemtags[index]} for {word},{pos} not found in database")
                        else:
                            self.forced_ids[wordtag] = ids
                            self.forced_ids_source[wordtag] = source


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

                    if iword in self.tagfixes and pos in self.tagfixes[iword]:
                        count = self.tagfix_count.get(iword,0)
                        self.tagfix_count[iword] = count+1

                        iword,pos = self.tagfixes[iword][ipos]


                    xword,junk,xlemma = iword.partition("|")
                    if not xlemma:
                        xlemma = xword

                    for word in [ f'@{xword}',xlemma ]:

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


    def get_best_sentence_ids(self, items, count):

        sentences = {}
        source = None

        seen = set()
        for word, pos in items:
            # if there are multiple word/pos pairs specified, ideally use results from each equally
            # However, if one item doesn't have enough results we will use more results from this item
            # Thus, we need to retrieve "count" items, as we could be using them all if the other has none

            item_ids = []

            wordtag = make_tag(word, pos)
            forced_ids = [x for x in self.forced_ids.get(wordtag,[]) if
                    self.sentencedb[x][IDX_SPAID] not in seen and 
                    self.sentencedb[x][IDX_ENGID] not in seen]
            if len(forced_ids):
                source = self.forced_ids_source[wordtag]
                item_ids = forced_ids[:count]
                seen |= set( [ self.sentencedb[x][IDX_SPAID] for x in item_ids ] )
                seen |= set( [ self.sentencedb[x][IDX_ENGID] for x in item_ids ] )

            else:
                res = self.get_all_sentence_ids(word, pos)
                available_ids = set(res['ids']) - set(item_ids)
                if not source:
                    source = res['source']
                    item_ids = self.select_best_ids(available_ids, count, seen)

                # Only accept 'literal' matches for the first pos
                elif res['source'] not in [ 'literal' ]:
                    item_ids = self.select_best_ids(available_ids, count, seen)



            sentences[pos] = item_ids

        res = []
        for idx in range(count):
            if len(res)>=count:
                break
            for pos,pos_ids in sentences.items():
                if len(res)>=count:
                    break

                if len(pos_ids)>idx:
                    res.append( { 'id': pos_ids[idx], 'pos': pos, 'source': source } )

        return res

    def select_best_ids(self, available, count, seen):

        ids = []
        source = ""

        # Find the hightest scoring sentences without repeating the english or spanish ids
        # prefer curated list (5/6) or sentences flagged as 5/5 (native spanish/native english)
        scored = {}
        for i in available:
            s = self.sentencedb[i]
            score = s[IDX_SCORE]
            if not score in scored:
                scored[score] = { 'ids': set(), 'eng_ids': set(), 'spa_ids': set() }
            scored[score]['ids'].add(i)
            scored[score]['eng_ids'].add(s[IDX_ENGID])
            scored[score]['spa_ids'].add(s[IDX_SPAID])

        available = []
        for score in sorted( scored.keys(), reverse=True ):
            for i in scored[score]['ids']:
                s = self.sentencedb[i]
                if s[IDX_ENGID] not in seen and s[IDX_SPAID] not in seen:
                    seen.add(s[IDX_ENGID])
                    seen.add(s[IDX_SPAID])
                    available.append(i)

                if len(available) >= count:
                    break

            if len(available) >= count:
                break

        available = sorted(available)

        if len(available) <= count:
            ids = available

        else:
            step = len(available)/(count+1.0)

            # select sentences over an even distribution of the range
            ids = [ available[math.ceil(i*step)] for i in range(count) ]

        return ids

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
        return [ self.id_index.get(tag) for tag in items ]

    def get_sentences(self, items, count, forced_items=[]):

        res = self.get_best_sentence_ids(items, count)
        source = res[0]['source'] if len(res) else None
        sentences = []
        for item in res:
            data = self.sentencedb[item['id']]
            sentences.append(data + [item['pos']])

        return { "sentences": sentences, "matched": source }


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
