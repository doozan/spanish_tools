import base64
import hashlib
import locale
import os
import re
import sys
import sqlite3

from collections import defaultdict
from .sentence_builder import SentenceBuilder

locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

class SpanishSentences:

    def __init__(self, sentences, ignored, tagfixes):
        self._all_spanish = None

        dbfilename = self.get_database_filename(sentences, ignored, tagfixes)
        if os.path.exists(dbfilename) and self.is_database_expired(dbfilename, sentences, ignored, tagfixes):
            os.remove(dbfilename)

        must_init_db = not os.path.exists(dbfilename)

        self.dbcon = sqlite3.connect(dbfilename)
        self.dbcon.execute('PRAGMA synchronous = OFF;')
        self.dbcon.execute('PRAGMA foreign_keys = ON;')
        self.dbcon.row_factory = sqlite3.Row

        if must_init_db:
            self._init_db(sentences, ignored, tagfixes)

        print("sentences loaded", file=sys.stderr)

    def _init_db(self, sentences, ignored, tagfixes):
        print("initalizing sentences database", file=sys.stderr)

        self.dbcon.execute('''CREATE TABLE sentences(id INTEGER NOT NULL PRIMARY KEY, sentence TEXT, user TEXT, score INT)''')
        self.dbcon.execute('''CREATE TABLE spanish_english(spa_id INTEGER PRIMARY KEY REFERENCES sentences, eng_id INT REFERENCES sentences)''')

        self.dbcon.execute('''CREATE TABLE spanish_grep(spa_id INTEGER PRIMARY KEY REFERENCES sentences, text TEXT)''')

        self.dbcon.execute('''CREATE TABLE lemmas(lemma TEXT, pos TEXT, spa_id INTEGER REFERENCES sentences, UNIQUE(lemma, pos, spa_id))''')
        self.dbcon.execute('''CREATE INDEX idx__lemmas__spa_id ON lemmas(spa_id)''')

        self.dbcon.execute('''CREATE TABLE forms(form TEXT, pos TEXT, spa_id INTEGER REFERENCES sentences, UNIQUE(form, pos, spa_id))''')
        self.dbcon.execute('''CREATE INDEX idx__forms__spa_id ON forms(spa_id)''')

        self.dbcon.execute('''CREATE TABLE spanish_extra(spa_id INTEGER PRIMARY KEY REFERENCES sentences, verb_score INT)''')

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

        with open(sentences) as infile:
            for line in infile:
                row = line.rstrip().split("\t")

                if len(row) < 6:
                    continue

                self.process_line(*row)

        for old,new in self.tagfixes.items():
            if old not in self.tagfix_count:
                print(f"Tagfix: {old} {new} does not match any sentences", file=sys.stderr)

        for sid,fixes in self.tagfix_sentences.items():
            for old,new in fixes.items():
                fixid = f"{old}@{sid}"
                if fixid not in self.tagfix_count:
                    print(f"Tagfix: {fixid} {new} does not match any sentences", file=sys.stderr)

        self.dbcon.commit()

    def process_line(self, english, spanish, credits, eng_score, spa_score, tag_str, verb_score=None):

        eng_id, eng_user, spa_id, spa_user = SentenceBuilder.parse_credits(credits)
        if eng_id in self.filter_ids or spa_id in self.filter_ids:
            return

        self.add_sentence(spa_id, spanish, spa_user, spa_score)
        self.add_sentence(eng_id, english, eng_user, eng_score)
        self.add_pair(spa_id, eng_id)

        self.add_spanish_grep(spa_id, spanish)
        self.add_tags_to_db(tag_str, spa_id)

        self.add_spanish_extra(spa_id, verb_score)

        return True

    def add_pair(self, spa_id, eng_id):
        self.dbcon.execute("INSERT INTO spanish_english VALUES(?, ?)", (spa_id, eng_id))

    def add_sentence(self, sid, sentence, user, score):
        self.dbcon.execute("INSERT OR IGNORE INTO sentences VALUES(?, ?, ?, ?)", (sid, sentence, user, score))

    def add_spanish_grep(self, spa_id, sentence):
        stripped = re.sub('[^ a-záéíñóúü]+', '', sentence.strip().lower())
        self.dbcon.execute("INSERT OR IGNORE INTO spanish_grep VALUES (?, ?)", (spa_id, stripped))

    def add_spanish_extra(self, spanish_id, verb_score):
        self.dbcon.execute("INSERT OR IGNORE INTO spanish_extra VALUES(?, ?)", (spanish_id, verb_score))

    @classmethod
    def get_database_filename(cls, sentences, *modfiles):
        allfiles = [f for files in modfiles for f in files]
        files = sentences + "::" + "::".join(sorted(allfiles))
        hash_obj = hashlib.sha1(bytes(files, "utf-8"))
        cid = str(base64.b32encode(hash_obj.digest()), "utf-8")

        return sentences + ".~" + cid

    @staticmethod
    def is_database_expired(database, sentences, *modfiles):
        allfiles = [sentences] + [f for files in modfiles for f in files]

        if not os.path.exists(database):
            return True

        return any(os.path.getctime(f) > os.path.getctime(database) for f in allfiles)

    @staticmethod
    def str_to_tags(tag_str):
        # return { pos: [word1, word2] }

        tags = {}
        for tag_items in tag_str[1:].split(":"):
            tag,*items = tag_items.strip().split(",")
            tags[tag] = items
        return tags

    def add_tags_to_db(self, tag_str, spa_id):
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

                self.add_form(xword, pos, spa_id)
                for xlemma in xlemmas:
                    self.add_lemma(xlemma, pos, spa_id)

    def add_lemma(self, lemma, pos, spa_id):
        self.dbcon.execute("INSERT OR IGNORE INTO lemmas VALUES (?, ?, ?)", (lemma, pos, spa_id))

    def add_form(self, form, pos, spa_id):
        self.dbcon.execute("INSERT OR IGNORE INTO forms VALUES (?, ?, ?)", (form, pos, spa_id))

    def get_sentences_with_phrase(self, phrase):
        term = re.sub('[^ a-záéíñóúü]+', '', phrase.strip().lower())

        rows = self.dbcon.execute("SELECT spa_id, text FROM spanish_grep WHERE text LIKE ?", (f"%{phrase}%",))
        pattern = r"\b" + phrase.strip().lower() + r"\b"
        return [self.get_sentence(spa_id) for spa_id, item in rows if re.search(pattern, item)]

    def get_sentences_with_form(self, form):
        rows = self.dbcon.execute("SELECT DISTINCT spa_id FROM forms WHERE form=?", (form,))
        return [self.get_sentence(x[0]) for x in rows]

    def get_sentences_with_lemma(self, lemma, pos=None):
        if not pos:
            rows = self.dbcon.execute("SELECT DISTINCT spa_id FROM lemmas WHERE lemma=?", (lemma,))
        else:
            rows = self.dbcon.execute("SELECT DISTINCT spa_id FROM lemmas WHERE lemma=? AND POS=?", (lemma,pos))

        return [self.get_sentence(x[0]) for x in rows]

    def has_lemma(self, lemma, pos, spa_id):
        return any(self.dbcon.execute("SELECT * FROM lemmas WHERE lemma=? AND POS=? and spa_id=? LIMIT 1", (lemma,pos,spa_id)))

    def get_sentences(self, lookup, pos, allowed_sources=[]):
        """Returns [sentences], "source" """

        sentences = []

        lookup = lookup.strip()

        if " " in lookup:
            pos = "phrase"

        if not allowed_sources or "exact" in allowed_sources:
            source = "exact"
            sentences = self.get_sentences_with_lemma(lookup, pos)

        if not sentences and pos != "phrase" and (not allowed_sources or "phrase" in allowed_sources):
            source = "phrase"
            phrase_pos = "phrase-" + pos
            sentences = self.get_sentences_with_lemma(lookup, phrase_pos)

        if not sentences and (not allowed_sources or "literal" in allowed_sources):
            source = "literal"

            if pos == "phrase":
                sentences = self.get_sentences_with_phrase(lookup)

            else:
                sentences = self.get_sentences_with_form(lookup)

        if not sentences:
            return [], None

        sentences.sort(key=lambda x: (x.english.count(" "), locale.strxfrm(x.english), locale.strxfrm(x.spanish)))
        return sentences, source

    def get_sentence(self, spa_id):
        query = """
        SELECT
            spa.id as spa_id,
            spa.sentence as spanish,
            spa.score as spa_score,
            spa.user as spa_user,
            eng.id as eng_id,
            eng.sentence as english,
            eng.score as eng_score,
            eng.user as eng_user,
            x.*
        FROM spanish_english AS se
            JOIN sentences AS spa ON se.spa_id = spa.id
            JOIN sentences AS eng ON se.eng_id = eng.id
            JOIN spanish_extra AS x ON se.spa_id = x.spa_id
        WHERE se.spa_id = ?;
        """
        row = next(self.dbcon.execute(query, (spa_id,)), None)
        if row:
            return Sentence(row)

    def all_sentences(self):
        query = """
        SELECT
            spa.id as spa_id,
            spa.sentence as spanish,
            spa.score as spa_score,
            spa.user as spa_user,
            eng.id as eng_id,
            eng.sentence as english,
            eng.score as eng_score,
            eng.user as eng_user,
            x.*
        FROM spanish_english AS se
            JOIN sentences AS spa ON se.spa_id = spa.id
            JOIN sentences AS eng ON se.eng_id = eng.id
            JOIN spanish_extra AS x ON se.spa_id = x.spa_id
        """
        for row in self.dbcon.execute(query):
            yield Sentence(row)

    def get_lemmas(self, spa_id):
        yield from self.dbcon.execute("SELECT lemma, pos FROM lemmas WHERE spa_id = ?", (spa_id,))

    def get_forms(self, spa_id):
        yield from self.dbcon.execute("SELECT form, pos FROM forms WHERE spa_id = ?", (spa_id,))

    @property
    def all_spanish(self):
        if not self._all_spanish:
            self._all_spanish = set(row[0] for row in self.dbcon.execute("SELECT spa_id FROM spanish_english"))
        return self._all_spanish

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
