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

def make_tag(word, pos):
    return pos.lower() + ":" + word.lower()

class SpanishSentences:

    def __init__(self, sentences, preferred, forced, ignored, tagfixes):

        self.forced_ids = {}
        self.forced_ids_source = {}

        dbfilename = self.get_database_filename(sentences, ignored, tagfixes)
        if os.path.exists(dbfilename) and not self.is_database_valid(dbfilename, sentences, ignored, tagfixes):
            os.remove(dbfilename)

        init_db = not os.path.exists(dbfilename)

        self.dbcon = sqlite3.connect(dbfilename)
        self.dbcon.execute('PRAGMA synchronous=OFF;')
        self.dbcon.row_factory = sqlite3.Row

        if init_db:
            self._init_db(sentences, ignored, tagfixes)

        # Forced/preferred items must be processed last
        for datafile in preferred:
            self.load_overrides(datafile, "preferred")

        for datafile in forced:
            self.load_overrides(datafile, "forced")

        print("sentences loaded")


    def _init_db(self, sentences, ignored, tagfixes):
        print("initalizing sentences database", file=sys.stderr)
#        self.dbcon.execute('''CREATE TABLE english(id UNIQUE, sentence, user_id INT, user_score)''')
#        self.dbcon.execute('''CREATE TABLE spanish(id UNIQUE, sentence, user_id INT, user_score, tag_str, verb_score INT)''')
#        self.dbcon.execute('''CREATE TABLE spanish_english(spa_id INT, eng_id INT, UNIQUE(spa_id, eng_id))''')

        self.dbcon.execute('''CREATE TABLE sentences(id INT UNIQUE, english, spanish, eng_score INT, spa_score INT, tag_str, eng_id INT, eng_user, spa_id INT, spa_user, verb_score INT, UNIQUE(spa_id, eng_id))''')
        self.dbcon.execute('''CREATE TABLE spanish_grep(spa_id UNIQUE, text TEXT)''')
        self.dbcon.execute('''CREATE TABLE lemmas(lemma, pos, spa_id INT, id INT, UNIQUE(lemma, pos, spa_id))''')
        self.dbcon.execute('''CREATE TABLE forms(form, pos, spa_id INT, id INT, UNIQUE(form, pos, spa_id))''')

        self.tagfixes = {}
        self.tagfix_sentences = {}
        self.filter_ids = {}

        self.tagfix_count = defaultdict(int)

        for datafile in tagfixes:
            with open(datafile) as infile:
                for line in infile:
                    line = line.strip()
                    if line.startswith("#") or not ":" in line:
                        continue
                    line,_,id_string = line.partition("@")
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

        self.dbcon.commit()

    def process_line(self, index, english, spanish, credits, eng_score, spa_score, tag_str, verb_score=None):

        eng_id, eng_user, spa_id, spa_user = SentenceBuilder.parse_credits(credits)
        if eng_id in self.filter_ids or spa_id in self.filter_ids:
            return

        self.add_sentence(index, english, spanish, credits, eng_score, spa_score, tag_str)
        self.add_spanish_grep(spa_id, spanish)
        #self.add_tags_to_db(tag_str, spa_id)
        self.add_tags_to_db(tag_str, index, spa_id)

        return True


    def add_sentence(self, index, english, spanish, credits, eng_score, spa_score, tag_str, verb_score=None):

        if verb_score is None:
            verb_score = 0

        eng_id, eng_user, spa_id, spa_user = SentenceBuilder.parse_credits(credits)

        self.dbcon.execute("INSERT INTO sentences VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", \
            (index, english, spanish, eng_score, spa_score, tag_str, eng_id, eng_user, spa_id, spa_user, verb_score))


    def add_spanish_grep(self, spa_id, sentence):
        stripped = re.sub('[^ a-záéíñóúü]+', '', sentence.strip().lower())
        self.dbcon.execute("INSERT OR IGNORE INTO spanish_grep VALUES (?, ?)", (spa_id, stripped))

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

                    sentence = self.get_sentence(spa_id, eng_id)
                    if not sentence:
                        print(f"{source} sentences no longer exist for {word},{pos}, ignoring...", file=sys.stderr)
                        valid = False
                        break

                    ids.append(sentence.id)

                    if source == "preferred":

                        if sentence.score < 55:
                            print(f"{source} score for {word},{pos} has dropped below 55, ignoring...", file=sys.stderr)
                            valid = False
                            break

                        if not self.has_lemma(word, pos, sentence.id):
                            if self.has_lemma(word, "phrase-" + pos, sentence.id):
                                print(f"{source} sentences for {word},{pos} contain phrases, ignoring...", file=sys.stderr)
                                valid = False
                                break

                            elif pos == "interj":
                                print(f"! {source} sentences no longer has {word},{pos}, ignoring...", file=sys.stderr)
                                valid = False
                                break

                if valid:
                    wordtag = make_tag(word, pos)

                    # TODO: instead of sentence ids, use (spa_id, eng_id)
                    self.forced_ids[wordtag] = ids
                    self.forced_ids_source[wordtag] = source


    @classmethod
    def get_database_filename(cls, sentences, *modfiles):
        allfiles = [f for files in modfiles for f in files]
        print(allfiles)
        files = sentences + "::" + "::".join(sorted(allfiles))
        hash_obj = hashlib.sha1(bytes(files, "utf-8"))
        cid = str(base64.b32encode(hash_obj.digest()), "utf-8")

        return sentences + ".~" + cid

    @staticmethod
    def is_database_valid(database, sentences, *modfiles):
        allfiles = [sentences] + [f for files in modfiles for f in files]

        if not os.path.exists(database):
            return False

        return all(os.path.getctime(database) > os.path.getctime(f) for f in allfiles)

    @staticmethod
    def str_to_tags(tag_str):
        # return { pos: [word1, word2] }

        tags = {}
        for tag_items in tag_str[1:].split(":"):
            tag,*items = tag_items.strip().split(",")
            tags[tag] = items
        return tags

    def add_tags_to_db(self, tag_str, index, spa_id):
        for tagpos,words in self.str_to_tags(tag_str).items():

            # Each past participle has both a part-verb and a part-adj tag
            # NOTE: part-verb will be tagged as "verb", while normal verbs are "v"
            # THIS IS INTENTIONAL, and is used to distinguish normal verb usage
            pos = tagpos[len("part-"):] if tagpos.startswith("part-") else tagpos

            for word in words:

                fixid = f"{word}:{pos}"
                newword,newpos = None,None
                if spa_id in self.tagfix_sentences:
                    newword,newpos = self.tagfix_sentences[spa_id].get(fixid,[None,None])
                if newword:
                    fixid = f"{word}:{pos}@{spa_id}"
                else:
                    newword,newpos = self.tagfixes.get(fixid,[None,None])

                if newword:
                    self.tagfix_count[fixid] += 1

                    word = newword
                    pos = newpos

                xword,*xlemmas = word.split("|")
                if not xlemmas:
                    xlemmas = [xword]

                self.add_form(xword, pos, spa_id, index)
                for xlemma in xlemmas:
                    self.add_lemma(xlemma, pos, spa_id, index)

    def add_lemma(self, lemma, pos, spa_id, index):
        self.dbcon.execute("INSERT OR IGNORE INTO lemmas VALUES (?, ?, ?, ?)", (lemma, pos, spa_id, index))

    def add_form(self, form, pos, spa_id, index):
        self.dbcon.execute("INSERT OR IGNORE INTO forms VALUES (?, ?, ?, ?)", (form, pos, spa_id, index))

    def get_ids_from_phrase(self, phrase):
        term = re.sub('[^ a-záéíñóúü]+', '', phrase.strip().lower())

        rows = self.dbcon.execute("SELECT spa_id, text FROM spanish_grep WHERE text LIKE ?", (f"%{phrase}%",))
        pattern = r"\b" + phrase.strip().lower() + r"\b"
        return [spa_id for spa_id, item in rows if re.search(pattern, item)]


    def get_ids_from_form(self, form):
        rows = self.dbcon.execute("SELECT DISTINCT id FROM forms WHERE form=?", (form,))
        return sorted([x[0] for x in rows])

    # if pos is set it return only results matching that word,pos
    # if it's not set, return all results matching the keyword
    def get_ids_from_lemma(self, lemma, pos):

        if not pos:
            rows = self.dbcon.execute("SELECT DISTINCT id FROM lemmas WHERE lemma=?", (lemma,))
        else:
            rows = self.dbcon.execute("SELECT DISTINCT id FROM lemmas WHERE lemma=? AND POS=?", (lemma,pos))

        return sorted([x[0] for x in rows])

    def has_lemma(self, lemma, pos, spa_id):
        return any(self.dbcon.execute("SELECT * FROM lemmas WHERE lemma=? AND POS=? and id=? LIMIT 1", (lemma,pos,spa_id)))

    def get_eng_id(self, idx):
        return next(self.dbcon.execute("SELECT eng_id FROM sentences WHERE id = ?", (idx,)))["eng_id"]

    def get_spa_id(self, idx):
        return next(self.dbcon.execute("SELECT spa_id FROM sentences WHERE id = ?", (idx,)))["spa_id"]

    def get_forced_ids(self, word, pos):
        wordtag = make_tag(word, pos)

        source = self.forced_ids_source.get(wordtag)
        return self.forced_ids.get(wordtag,[]), source

    def get_best_sentences(self, items, count):

        sentences = {}
        source = None
        seen = set()

        for word, pos in items:
            item_ids = []

            # Only allow literal matches for the primary pos
            allow_literal = not sentences
            pos_sentences, pos_source = self.get_pos_sentences(word, pos, count, seen, allow_literal)
            if pos_sentences:
                sentences[pos] = pos_sentences
                if not source:
                    source = pos_source

        # Take the first sentence from each pos, then the second, etc
        # until 'count' sentences have been selected
        best_ids = []
        for idx in range(count):
            for pos, pos_ids in sentences.items():
                if len(best_ids)==count:
                    break
                if len(pos_ids)>idx:
                    best_ids.append(pos_ids[idx])

        sentences = [self.get_sentence_by_index(index) for index in best_ids]
        return sentences, source


    def get_pos_sentences(self, word, pos, limit, seen, allow_literal):

        # if there are multiple word/pos pairs specified, ideally use results from each equally
        # However, if one item doesn't have enough results we will use more results from this item
        # Thus, we need to retrieve "limit" items, as we could be using them all if the other has none

        item_ids = []
        source = None

        forced_ids, forced_source = self.get_forced_ids(word, pos)
        if len(forced_ids):
            for x in forced_ids:
                spa_id = self.get_spa_id(x)
                eng_id = self.get_eng_id(x)
                if spa_id not in seen and eng_id not in seen:
                    item_ids.append(x)
                seen.add(spa_id)
                seen.add(eng_id)
                if len(item_ids) == limit:
                    break

        if item_ids:
            source = forced_source

        else:
            res = self.get_all_sentence_ids(word, pos)
            available_ids = [ x for x in res['ids'] ]
            if allow_literal:
                source = res['source']
                best_sentences = self.select_best_sentences(available_ids, limit, seen)
                item_ids = [s.id for s in best_sentences]

            # Only accept 'literal' matches for the first pos
            elif res['source'] not in [ 'literal' ]:
                best_sentences = self.select_best_sentences(available_ids, limit, seen)
                item_ids = [s.id for s in best_sentences]

        return item_ids, source


    def select_best_sentences(self, all_ids, count, seen):

        source = ""

        #all_sentences = [self.get_sentence_by_spa_id(idx) for idx in all_ids]
        all_sentences = [self.get_sentence_by_index(idx) for idx in all_ids]

        # Find the highest scoring sentences without repeating the english or spanish ids
        # prefer curated list (5/6) or sentences flagged as 5/5 (native spanish/native english)
        scored = defaultdict(set)
        for sentence in all_sentences:
            score = sentence.score
            scored[score].add(sentence)

        available = []
        selected = []
        needed = count

        # for each group of scored sentences:
        # if the group offers less than we need, add them all to ids
        # if it has more, add them all to available and let the selector choose
        for score in sorted( scored.keys(), reverse=True ):

            for sentence in sorted(scored[score], key=lambda x: x.id):
                eng_id = sentence.eng_id
                spa_id = sentence.spa_id
                if eng_id not in seen and spa_id not in seen:
                    seen.add(eng_id)
                    seen.add(spa_id)
                    available.append(sentence)

            if len(available) >= needed:
                break
            elif len(available):
                needed -= len(available)
                selected += available
                available = []

        available = sorted(available, key=lambda x: x.id)

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

        ids = self.get_ids_from_lemma(lookup, pos)

        if not ids:
            if pos != "phrase":
                source = "phrase"
                phrase_pos = "phrase-" + pos
                ids = self.get_ids_from_lemma(lookup, phrase_pos)

            if not ids:
                source = "literal"

                if pos == "phrase":
                    ids = self.get_ids_from_phrase(lookup)
                    ids = [self.get_sentence_by_spa_id(spa_id).id for spa_id in ids]

                elif pos != "INTERJ":
                    ids = self.get_ids_from_form(lookup)

        return { "ids": ids, "source": source }

    def get_sentences(self, items, count, forced_items=[]):

        sentences, source = self.get_best_sentences(items, count)
        return { "sentences": sentences, "matched": source }

    def get_sentence_by_spa_id(self, idx):
        row = next(self.dbcon.execute(f"SELECT * from sentences WHERE spa_id = ?", (idx,)))
        return Sentence(row)

    def get_sentence_by_index(self, idx):
        row = next(self.dbcon.execute(f"SELECT * from sentences WHERE id = ?", (idx,)))
        return Sentence(row)

    def get_sentence(self, spa_id, eng_id):
        row = next(self.dbcon.execute(f"SELECT * from sentences WHERE spa_id = ? AND eng_id = ?", (spa_id,eng_id)), None)
        if row:
            return Sentence(row)

class Sentence():
    def __init__(self, row):
        self._db_values = row

    def __getattr__(self, attr):
        return self._db_values[attr]

    @property
    def score(self):
        return self.spa_score*10 + self.eng_score

    @property
    def credits(self):
        return f"CC-BY 2.0 (France) Attribution: tatoeba.org #{self.eng_id} ({self.eng_user}) & #{self.spa_id} ({self.spa_user})"
