import base64
import hashlib
import math
import os
import pickle
import re
import sys
import sqlite3

from collections import defaultdict, namedtuple
from .sentence_builder import SentenceBuilder

class Sentence():
    def __init__(self, english, spanish, credits, eng_score, spa_score, tag_str, verb_score=None):
        self.english = english
        self.spanish = spanish
        self.eng_id, self.eng_user, self.spa_id, self.spa_user = SentenceBuilder.parse_credits(credits)
        self.eng_score = int(eng_score)
        self.spa_score = int(spa_score)
        self.tag_str = tag_str
        self.verb_score = 0 if verb_score is None else verb_score

    @property
    def score(self):
        return self.spa_score*10 + self.eng_score

    @property
    def credits(self):
        return f"CC-BY 2.0 (France) Attribution: tatoeba.org #{self.eng_id} ({self.eng_user}) & #{self.spa_id} ({self.spa_user})"

    @property
    def tags(self):
        tags = {}
        for tag_items in self.tag_str[1:].split(":"):
            tag,*items = tag_items.strip().split(",")
            tags[tag] = items
        return tags



#Sentence = namedtuple("Sentence", [ "spanish", "english", "score", "spa_id", "eng_id", "spa_user", "eng_user", "verb_score" ])

def make_tag(word, pos):
    return pos.lower() + ":" + word.lower()

class SpanishSentences:

    def __init__(self, sentences="sentences.tsv", preferred=[], forced=[], ignored=[], tagfixes=[], dbfilename=None):

#        if dbfilename:
#            existing = os.path.exists(dbfilename)
#
#            self.dbcon = sqlite3.connect(dbfilename)
#            self.dbcon.execute('PRAGMA synchronous=OFF;')
#
#            if existing:
#                return
#
#        else:
#            self.dbcon = sqlite3.connect(":memory:")
#
        self.dbcon = sqlite3.connect(":memory:")
        self.dbcon.execute('''CREATE TABLE english(id UNIQUE, sentence, user_id INT, user_score)''')
        self.dbcon.execute('''CREATE TABLE spanish(id UNIQUE, sentence, user_id INT, user_score, tag_str, verb_score INT)''')
        self.dbcon.execute('''CREATE TABLE spanish_grep(id UNIQUE, text TEXT)''')
        self.dbcon.execute('''CREATE TABLE spanish_english(spa_id INT, eng_id INT, UNIQUE(spa_id, eng_id))''')
        self.dbcon.execute('''CREATE TABLE words(word, pos, spa_id INT, UNIQUE(word, pos, spa_id))''')


        self.add_counter = 0

        if not preferred:
            preferred = []
        if not forced:
            forced = []
        if not ignored:
            ignored = []
        if not tagfixes:
            tagfixes = []

#        if self.load_cache(sentences, preferred, forced, ignored, tagfixes):
#            return

        self.sentencedb = []
#        self.grepdb = []
#        self.tagdb = defaultdict(lambda: defaultdict(list))
        self.id_index = {}
        self.tagfixes = {}
        self.tagfix_sentences = {}
        self.filter_ids = {}
        self.forced_ids = {}
        self.forced_ids_source = {}

        self.tagfix_count = defaultdict(int)

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
                row = line.rstrip().split("\t")

                if len(row) < 6:
                    continue

                if self.process_line(index, *row):
                    index+=1

        for old,new in self.tagfixes.items():
            if old not in self.tagfix_count:
                print(f"Tagfix: {old} {new} does not match any sentences", file=sys.stderr)

        for sid,fixes in self.tagfix_sentences.items():
            for old,new in fixes.items():
                fixid = f"{old}@{sid}"
                if fixid not in self.tagfix_count:
                    print(f"Tagfix: {fixid} {new} does not match any sentences", file=sys.stderr)

        # Forced/preferred items must be processed last
        for datafile in preferred:
            self.load_overrides(datafile, "preferred")

        for datafile in forced:
            self.load_overrides(datafile, "forced")

#        self.save_cache(sentences, preferred, forced, ignored, tagfixes)

        print("sentences loaded")

    def process_line(self, index, english, spanish, credits, eng_score, spa_score, tag_str, verb_score=None):

        eng_id, eng_user, spa_id, spa_user = SentenceBuilder.parse_credits(credits)
        return self.add_sentence(index, english, spanish, credits, eng_score, spa_score, tag_str)


    def add_sentence(self, index, english, spanish, credits, eng_score, spa_score, tag_str, verb_score=None):
        sentence = Sentence(english, spanish, credits, eng_score, spa_score, tag_str, verb_score)

        if sentence.eng_id in self.filter_ids or sentence.spa_id in self.filter_ids:
            return

        self.sentencedb.append(sentence)
        #self.add_spanish_grep(sentence.spa_id, spanish)
        self.add_spanish_grep(index, spanish)

        self.id_index[f"{sentence.spa_id}:{sentence.eng_id}"] = index

        self.add_tags_to_db(sentence.tags, index, sentence.spa_id)

        return True

    def add_spanish_grep(self, spa_id, sentence):
        stripped = re.sub('[^ a-záéíñóúü]+', '', sentence.strip().lower())
#        self.grepdb.append(stripped)
        self.dbcon.execute("INSERT OR IGNORE INTO spanish_grep VALUES (?, ?)", (spa_id, stripped))

    def load_overrides(self, datafile, source):
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

                elif source == "preferred" and any( i not in self.get_ids_from_tag(word, pos)
                        and i in self.get_ids_from_tag(word, "phrase-" + pos) for i in ids):
                    print(f"{source} sentences for {word},{pos} contain phrases, ignoring...", file=sys.stderr)
                    continue


                elif source == "preferred" and pos == "interj" \
                        and any( i not in self.get_ids_from_tag(word, pos) for i in ids):
                    print(f"! {source} sentences no longer has interj for {word}, ignoring...", file=sys.stderr)
                    continue

                else:
                    self.forced_ids[wordtag] = ids
                    self.forced_ids_source[wordtag] = source



    def save_cache(self, sentences, preferred, forced, ignored, tagfixes):

        print(preferred, forced, ignored, tagfixes, file=sys.stderr)
        modfiles = preferred + forced + ignored + tagfixes
        cached = self.get_cache_filename(sentences, modfiles)

        print("saving cache", cached, file=sys.stderr)

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
    def add_tags_to_db(self, tags, index, sid):
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
                    self.tagfix_count[fixid] += 1

                    word = newword
                    pos = newpos

                xword,*xlemmas = word.split("|")
                if not xlemmas:
                    xlemmas = [xword]

                for xword in [f'@{xword}'] + xlemmas:
                    self.add_tag(xword, pos, index)

    def add_tag(self, word, pos, index):
        # TODO: index should be spa_id
        self.dbcon.execute("INSERT OR IGNORE INTO words VALUES (?, ?, ?)", (word, pos, index))

    def get_ids_from_phrase(self, phrase):
        term = re.sub('[^ a-záéíñóúü]+', '', phrase.strip().lower())

        rows = self.dbcon.execute("SELECT id, text FROM spanish_grep WHERE text LIKE ?", (f"%{phrase}%",))
        pattern = r"\b" + phrase.strip().lower() + r"\b"
        return [i for i, item in rows if re.search(pattern, item)]

#        return [i for i, item in enumerate(self.grepdb) if term in item and re.search(pattern, item)]




    def get_ids_from_word(self, word):
        return self.get_ids_from_tag("@"+word, "")


    # if pos is set it return only results matching that word,pos
    # if it's not set, return all results matching the keyword
    def get_ids_from_tag(self, word, pos):

        if not pos:
            rows = self.dbcon.execute("SELECT DISTINCT spa_id FROM words WHERE word=?", (word,))
        else:
            rows = self.dbcon.execute("SELECT DISTINCT spa_id FROM words WHERE word=? AND POS=?", (word,pos))

        return sorted([x[0] for x in rows])


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

        if " " in lookup:
            pos = "phrase"

        ids = self.get_ids_from_tag(lookup, pos)

        if not ids:
            if pos != "phrase":
                source = "phrase"
                pos = "phrase-" + pos
                ids = self.get_ids_from_tag(lookup, pos)

            if not ids:
                source = "literal"

                if pos == "phrase":
                    ids = self.get_ids_from_phrase(lookup)

                elif pos != "INTERJ":
                    ids = self.get_ids_from_word(lookup)

        return { "ids": ids, "source": source }

    def itemtags_to_ids(self, items):
        return [ self.id_index.get(tag) for tag in items ]

    def get_sentences(self, items, count, forced_items=[]):

        sentence_ids = self.get_best_sentence_ids(items, count)
        source = sentence_ids[0]['source'] if sentence_ids else None
        sentences = [ self.sentencedb[i['id']] for i in sentence_ids ]
        return { "sentences": sentences, "matched": source }
