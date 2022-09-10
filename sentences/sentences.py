import base64
import hashlib
import math
import os
import pickle
import re
import sys
from collections import defaultdict, namedtuple

Sentence = namedtuple("Sentence", [ "spanish", "english", "score", "spa_id", "eng_id", "spa_user", "eng_user" ])

def make_tag(word, pos):
    return pos.lower() + ":" + word.lower()

class SpanishSentences:

    def __init__(self, sentences="sentences.tsv", preferred=[], forced=[], ignored=[], tagfixes=[]):

        if self.load_cache(sentences, preferred, forced, ignored, tagfixes):
            return

        self.sentencedb = []
        self.grepdb = []
        self.tagdb = {}
        self.id_index = {}
        self.tagfixes = {}
        self.tagfix_sentences = {}
        self.filter_ids = {}
        self.forced_ids = {}
        self.forced_ids_source = {}

        tagfix_count = defaultdict(int)

        for datafile in tagfixes:
            with open(datafile) as infile:
                for line in infile:
                    line = line.strip()
                    if line.startswith("#") or not ":" in line:
                        continue
                    line,junk,id_string = line.partition("@")
                    oldword,oldpos,newword,newpos = line.split(":")

                    if len(id_string):
                        for sid in id_string.split(","):
                            sid = int(sid.strip())
                            if not sid in self.tagfix_sentences:
                                self.tagfix_sentences[sid] = {}
                            self.tagfix_sentences[sid][f"{oldword}:{oldpos}"] = [newword, newpos]
                    else:
                        self.tagfixes[f"{oldword}:{oldpos}"] = [newword, newpos]

        # Ignore list must be loaded before the main file
        for datafile in ignored:
            with open(datafile) as infile:
                self.filter_ids = set( int(line.strip().split(" ",1)[0]) for line in infile if not line.startswith("#") )

        index=0
        with open(sentences) as infile:
            for line in infile:
                res = re.match(r"([^\t]*)\t([^\t]*)\tCC-BY 2.0 \(France\) Attribution: tatoeba.org #([0-9]+) \(([^)]+)\) & #([0-9]+) \(([^)]+)\)\t([0-6])\t([0-6])\t([^\t]*)\n", line)
                if not res:
                    continue
                english,spanish,eng_id,eng_user,spa_id,spa_user,eng_score,spa_score,tag_str = res.groups()
                eng_id = int(eng_id)
                spa_id = int(spa_id)
                score = int(spa_score)*10 + int(eng_score)

                if eng_id in self.filter_ids or spa_id in self.filter_ids:
                    continue

                tags = { }
                for tag_items in tag_str[1:].split(":"):
                    tag,*items = tag_items.strip().split(",")
                    tags[tag] = items

                self.sentencedb.append( Sentence(spanish, english, score, spa_id, eng_id, spa_user, eng_user) )
                stripped = re.sub('[^ a-záéíñóúü]+', '', spanish.lower())
                self.grepdb.append(stripped)

                self.id_index[f"{spa_id}:{eng_id}"] = index

                self.add_tags_to_db(tags,index,spa_id, tagfix_count)
                index+=1

        for old,new in self.tagfixes.items():
            if old not in tagfix_count:
                print(f"Tagfix: {old} {new} does not match any sentences", file=sys.stderr)

        for sid,tagfixes in self.tagfix_sentences.items():
            for old,new in tagfixes.items():
                fixid = f"{old}@{sid}"
                if fixid not in tagfix_count:
                    print(f"Tagfix: {fixid} {new} does not match any sentences", file=sys.stderr)

        # Forced/preferred items must be processed last
        for datafile in preferred:
            load_overrides(datafile, "preferred")

        for datafile in preferred:
            load_overrides(datafile, "forced")

        self.save_cache(sentences, preferred, forced, ignored, tagfixes)


    def load_overrides(datafile, source):
        with open(datafile) as infile:

            for line in infile:
                line = line.strip()
                if line.startswith("#"):
                    continue
                word,pos,*forced_itemtags = line.split(",")
                wordtag = make_tag(word, pos)
                ids = self.itemtags_to_ids(forced_itemtags)
                if None in ids:
                    print(f"{source} sentences no longer exist for {word},{pos}, ignoring...", file=sys.stderr)
                    continue

                elif source == "preferred" and any(self.sentencedb[i].score < 55 for i in ids):
                    print(f"{source} sentences scores for {word},{pos} have dropped below 55, ignoring...", file=sys.stderr)
                    continue

                else:
                    self.forced_ids[wordtag] = ids
                    self.forced_ids_source[wordtag] = source



    def save_cache(self, sentences, preferred, forced, ignored, tagfixes):

        modfiles = preferred + forced + ignored + tagfixes
        cached = self.get_cache_filename(sentences, modfiles)

        print("saving cache", cached)

        with open(cached, "wb") as outfile:
            pickle.dump([
                self.sentencedb,
                self.grepdb,
                self.tagdb,
                self.id_index,
                self.tagfixes,
                self.tagfix_sentences,
                self.filter_ids,
                self.forced_ids,
                self.forced_ids_source,
                ], outfile)


    @classmethod
    def get_cache_filename(cls, sentences, modfiles):
        files = sentences + "::" + "::".join(sorted(modfiles))
        hash_obj = hashlib.sha1(bytes(files, "utf-8"))
        cid = str(base64.b32encode(hash_obj.digest()), "utf-8")

        return sentences + ".~" + cid

    def load_cache(self, sentences, preferred, forced, ignored, tagfixes):

        modfiles = preferred + forced + ignored + tagfixes
        cached = self.get_cache_filename(sentences, modfiles)

        if not os.path.exists(cached):
            return

        if any(os.path.getctime(f) > os.path.getctime(cached) for f in modfiles):
            return

        # check for cached version
        print("loading cached", cached)
        with open(cached, "rb") as infile:
            res = pickle.load(infile)

            self.sentencedb, \
            self.grepdb, \
            self.tagdb, \
            self.id_index, \
            self.tagfixes, \
            self.tagfix_sentences, \
            self.filter_ids, \
            self.forced_ids, \
            self.forced_ids_source = res

        return True

    # tags are in the form:
    # { pos: [word1, word2] }
    def add_tags_to_db(self, tags, index, sid, tagfix_count):
        for tagpos,words in tags.items():

            # Each past participle has both a part-verb and a part-adj tag
            # NOTE: part-verb will be tagged as "verb", while normal verbs are "v"
            # THIS IS INTENTIONAL, and is used to distinguish normal verb usage
            pos = tagpos[len("part-"):] if tagpos.startswith("part-") else tagpos

            for word in words:

                fixid = f"{word}:{pos}"
                newword,newpos = None,None
                if sid in self.tagfix_sentences:
                    newword,newpos = self.tagfix_sentences[sid].get(fixid,[None,None])
                if newword:
                    fixid = f"{word}:{pos}@{sid}"
                else:
                    newword,newpos = self.tagfixes.get(fixid,[None,None])

                if newword:
                    tagfix_count[fixid] += 1

                    word = newword
                    pos = newpos

                xword,*xlemmas = word.split("|")
                if not xlemmas:
                    xlemmas = [xword]

                for xword in [f'@{xword}'] + xlemmas:

                    tags = self.tagdb.get(xword)
                    if not tags:
                        tags = { pos: [index] }
                        self.tagdb[xword] = { pos: [index] }
                    else:
                        items = tags.get(pos)
                        if not items:
                            tags[pos] = [index]
                        else:
                            items.append(index)



    def get_ids_from_phrase(self, phrase):
        term = phrase.strip().lower()
        pattern = r"\b" + phrase.strip().lower() + r"\b"

        return [i for i, item in enumerate(self.grepdb) if term in item and re.search(pattern, item)]

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
                    self.sentencedb[x].spa_id not in seen and
                    self.sentencedb[x].eng_id not in seen]

            if len(forced_ids):
                source = self.forced_ids_source[wordtag]
                item_ids = forced_ids[:count]
                for x in item_ids:
                    seen.add(self.sentencedb[x].spa_id)
                    seen.add(self.sentencedb[x].eng_id)

            else:
                res = self.get_all_sentence_ids(word, pos)
                available_ids = [ x for x in res['ids'] if x not in item_ids ]
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

            # try to take a sentence from each pos and each form of each pos
            for pos,pos_ids in sentences.items():
                if len(res)>=count:
                    break

                if len(pos_ids)>idx:
                    res.append( { 'id': pos_ids[idx], 'pos': pos, 'source': source } )

        return res

    def select_best_ids(self, all_ids, count, seen):

        source = ""

        # Find the highest scoring sentences without repeating the english or spanish ids
        # prefer curated list (5/6) or sentences flagged as 5/5 (native spanish/native english)
        scored = {}
        for i in all_ids:
            s = self.sentencedb[i]
            score = s.score
            if not score in scored:
                scored[score] = set()
            scored[score].add(i)

        available = []
        selected = []
        needed = count

        # for each group of scored sentences:
        # if the group offers less than we need, add them all to ids
        # if it has more, add them all to available and let the selector choose
        for score in sorted( scored.keys(), reverse=True ):

            for i in sorted(scored[score]):
                s = self.sentencedb[i]
                if s.eng_id not in seen and s.spa_id not in seen:
                    seen.add(s.eng_id)
                    seen.add(s.spa_id)
                    available.append(i)

            if len(available) >= needed:
                break
            elif len(available):
                needed -= len(available)
                selected += available
                available = []

        available = sorted(available)

        if len(available) <= needed:
            selected += available

        else:
            step = len(available)/(needed+1.0)

            # select sentences over an even distribution of the range
            selected += [ available[math.ceil(i*step)] for i in range(needed) ]

        return selected

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

        sentence_ids = self.get_best_sentence_ids(items, count)
        source = sentence_ids[0]['source'] if sentence_ids else None
        sentences = [ self.sentencedb[i['id']] for i in sentence_ids ]
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
