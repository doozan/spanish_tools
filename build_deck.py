#!/usr/bin/python3
# -*- python-mode -*-

import argparse
import csv
import genanki
import html
import json
import math
import os
import re
import sqlite3
import sys
from Levenshtein import distance as fuzzy_distance

from .spanish_sentences import sentences as spanish_sentences
from .spanish_speech import get_speech
from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms
from enwiktionary_wordlist.word import Word

def make_tag(word, pos):
    if not pos:
        return word

    return pos + ":" + word

def split_tag(wordtag):
    pos, junk, word = wordtag.partition(":")
    return [word, pos]

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def fail(*args, **kwargs):
    eprint(*args, **kwargs)
    exit(1)

class MyNote(genanki.Note):

    def write_to_db(self, cursor, timestamp: float, deck_id, id_gen):

        # Preserve the timestamp if there's an override
        if self.mod_ts:
            timestamp = self.mod_ts

        genanki.Note.write_to_db(self, cursor, timestamp, deck_id, id_gen)


class DeckBuilder():

    _fields = [
        "Rank",
        "Spanish",
        "Part of Speech",
        "Synonyms",
        "Data",
        "Sentences",
        "Display",
        "Audio",
    ]

    MAX_SYNONYMS = 5

    # For the sentence arrays
    IDX_SPANISH = 0
    IDX_ENGLISH = 1
    IDX_SCORE = 2
    IDX_SPAID = 3
    IDX_ENGID = 4
    IDX_SPAUSER = 5
    IDX_ENGUSER = 6

    # _FEMALE1 = "Lupe"
    _FEMALE1 = "Penelope"
    _FEMALE2 = "Penelope"
    _MALE1 = "Miguel"

    el_f_nouns = [ 'abra', 'acta', 'afta', 'ágora', 'agua', 'águila', 'ala', 'alba', 'alca',
            'álgebra', 'alma', 'alta', 'alza', 'ama', 'ancla', 'áncora', 'ánima', 'ansia',
            'app', 'arca', 'área', 'arma', 'arpa', 'asa', 'asma', 'aspa', 'asta', 'aula',
            'ave', 'haba', 'habla', 'hacha', 'hada', 'hambre', 'haya' ]

    def __init__(self, wordlist, sentences, ignore, allforms, shortdefs=None):

        self._words = None
        self._ignore = {}
        self._sentences = None

        self.db_notes = {}
        self.db_timestamps = {}

        self.allwords = {}
        self.allwords_index = []
        self.allwords_meta = {}
        self.shortdefs = {}

        self.media_files = []

        self.rows = []

        self.credits = {}
        self.dumpable_sentences = {}
        self.notes = {}
        self.seen_guids = {}
        self.seen_hints = {}

        self._words = wordlist
        self._ignore = ignore
        self._sentences = sentences
        self._shortdefs = shortdefs
        self.all_forms = allforms

    def filter_gloss(self, wordobj, sense, filter_gloss=None):
        word = wordobj.word
        pos = wordobj.pos if wordobj.pos != "n" else wordobj.genders

        note = sense.qualifier
        gloss = sense.gloss

        ignore = self._ignore

        if word in ignore:
            # If the exact pos doesn't match, check for the wildcard ''
            pos = '' if pos not in ignore[word] else pos
            if pos in ignore[word]:
                note = '' if note not in ignore[word][pos] else note
                if note in ignore[word][pos]:
                    for ignore_gloss in ignore[word][pos][note]:
                        if gloss.startswith(ignore_gloss):
                            return None

        gloss = re.sub(r'[ ;:,.]*\s*(alternative case form|feminine|female equivalent) of "[^\"]+"[ :,.]*', '', gloss)
        gloss = gloss.lstrip(":;., ")
        if gloss.startswith('(“') and gloss.endswith('”)'):
            gloss = gloss[2:-2]

        if not re.match("[^ :,.]", gloss):
            return None

        if gloss == filter_gloss:
            return None

        return gloss


    def load_db_notes(self, filename, deck_name):
        db = sqlite3.connect(filename)
        c = db.cursor()

        decks = json.loads(c.execute("SELECT decks FROM col").fetchone()[0])

        col_deck_guid = 0
        for item, val in decks.items():
            if val["name"] == deck_name:
                col_deck_guid = val["id"]
                break

        query = """
    SELECT
        c.id,n.id,n.guid,n.mod,n.flds,n.tags
    FROM
        cards AS c
    LEFT JOIN
        notes AS n
    ON
        c.nid = n.id
    WHERE
        c.did=?;
    """

        db_notes = {}
        for cid, nid, guid, mod, flds, tags in c.execute(
            query, (col_deck_guid,)
        ).fetchall():

            fields = flds.split(chr(31))

            if guid in db_notes:
                db_notes[guid]["cards"].append(cid)
            else:
                db_notes[guid] = {
                    "word": f"{fields[2]} {fields[1]}",
                    "cards": [cid],
                    "flds": flds,
                    "tags": tags,
                    "mod": mod,
                    "nid": nid,
                }

        return db_notes


    @staticmethod
    def make_card_model(data):
        return genanki.Model(
            data["id"],
            data["name"],
            fields=data["flds"],
            templates=data["tmpls"],
            css=data["css"],
        )


    @staticmethod
    def get_note_hash(guid, flds, tags):
        tags = " ".join(sorted(tags.strip().split(" ")))
        return hash(json.dumps([guid, flds, tags]))

    def get_mod_timestamp(self, note):
        guid = note.guid
        flds = note._format_fields()
        tags = note._format_tags()

        hashval = self.get_note_hash(guid, flds, tags)
        return self.db_timestamps.get(hashval)

    @staticmethod
    def format_sentences(sentences):
        return "\n".join(
            f'<span class="spa">{html.escape(item[0])}</span>\n' \
            f'<span class="eng">{html.escape(item[1])}</span>'
            for item in sentences
        )

    def get_sentences(self, items, count):

        results = self._sentences.get_sentences(items, count)
        self.store_credits(results)

        if len(results["sentences"]):
            return self.format_sentences(results["sentences"])

        return ""


    def store_credits(self, results):
        for sentence in results["sentences"]:
            spa_user = sentence[self.IDX_SPAUSER]
            eng_user = sentence[self.IDX_ENGUSER]
            spa_id = sentence[self.IDX_SPAID]
            eng_id = sentence[self.IDX_ENGID]

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




    def store_sentences(self, lookups):

        for word, pos in lookups:
            tag = make_tag(word, pos)
            if tag in self.dumpable_sentences:
                continue

            results = self._sentences.get_sentences([[word, pos]], 3)
            if not results:
                continue

            if results["matched"] not in ("preferred", "exact") and " " not in word:
                continue

            if len(results["sentences"]) != 3:
                continue

            if all(sentence[self.IDX_SCORE] >= 55 for sentence in results["sentences"]):
                ids = [
                    f"{sentence[self.IDX_SPAID]}:{sentence[self.IDX_ENGID]}"
                    for sentence in results["sentences"]
                ]
                self.dumpable_sentences[tag] = ids


    # (spanish, english, score, spa_id, eng_id)
    def dump_sentences(self, filename):

        try:
            with open(filename, "r") as dumpfile:
                dumpfile.seek(0)
                for line in dumpfile:
                    line = line.strip()
                    word,pos,*forced_itemtags = line.split(",")
                    wordtag = make_tag(word, pos)
                    if wordtag not in self.dumpable_sentences:
                        self.dumpable_sentences[wordtag] = forced_itemtags
        except IOError:
            pass

        print(f"dumping {len(self.dumpable_sentences)} sentences to {filename}")
        with open(filename, "w") as dumpfile:
            dumpfile.seek(0)
            dumpfile.truncate()
            for tag, ids in sorted(self.dumpable_sentences.items()):
                word, pos = split_tag(tag)
                row = [word, pos] + ids

                dumpfile.write(",".join(row))
                dumpfile.write("\n")


    @staticmethod
    def format_sound(filename):
        if not filename:
            return ""
        return f"[sound:{filename}]"

    @classmethod
    def obscure_gloss(cls, gloss, hide_word, hide_first=False, hide_all=False, english=True):

        def is_first_word(data):
            if all(w.strip().lower() in ["", "a", "an", "to", "be", "of", "in"] for w in data):
                return True
            return False

        if hide_all:
            hide_first = True

        hide_words = cls.get_hide_words(hide_word, english)

        m = re.match(r'(?P<pre>.*?)(?P<form>apocopic form|diminutive|ellipsis|clipping|superlative|plural) of "(?P<word>.*?)"(?P<post>.*)', gloss)
        if m:
            if not (hide_all or m.group("pre") or m.group("post")):
                return gloss

            new_gloss = []
            if m.group("pre"):
                new_gloss.append(DeckBuilder.obscure_gloss(m.group("pre"), hide_word, hide_all=True))

            new_gloss.append(m.group("form"))
            new_gloss.append(' of "')
            if m.group("form") in ["ellipsis", "clipping"]:
                new_gloss.append("...")
            else:
                new_gloss.append(DeckBuilder.obscure_gloss(m.group("word"), hide_word, hide_all=True))
            new_gloss.append('"')

            if m.group("post"):
                new_gloss.append(DeckBuilder.obscure_gloss(m.group("post"), hide_word, hide_all=True))

            # This isn't perfect, if a gloss for blah is 'blah; diminutive of "blah"' it will
            # be fully obscured to '...; diminutive of "..."'

        data = []
        splits = iter(re.split(r'(\W+)', gloss))
        all_hidden = True
        for word in splits:
            sep = next(splits, None)
            if not word and sep:
                data.append(sep)
                continue

            if any(h for h in hide_words if cls.should_obscure(word, h)) and (hide_first or not is_first_word(data)):
                data.append("...")
            else:
                data.append(word)
                if all_hidden and word.lower() not in ["a", "an", "to"]:
                    all_hidden = False

            if sep:
                data.append(sep)

        if hide_all or not all_hidden:
            gloss = "".join(data)

        return gloss

    alt_endings = {
        "ancia": ["ance", "ancy"],
        "mente": ["ly"],
        "mento": ["ment"],
        "encia": ["ence", "ency"],
        "adora": ["ing"],
        "ante": ["ant"],
        "ario": ["ary"],
        "ente": ["ent"],
        "ador": ["ing"],
        "ante": ["ant"],
        "cion": ["tion"],
        "ente": ["ent"],
        "ista": ["ist"],
        "ura": ["ure"],
        "ano": ["an"],
        "ana": ["an"],
        "ico": ["ic", "ical"],
        "ica": ["ic", "ical"],
        "ivo": ["ive"],
        "io": ["y"],
        "ía": ["y"],
        "ia": ["y"],
    }
    _unstresstab = str.maketrans("áéíóú", "aeiou")
    @classmethod
    def unstress(cls, text):
        return text.translate(cls._unstresstab)

    @classmethod
    def anglicise(cls, word):
        for k,endings in cls.alt_endings.items():
            if word.endswith(k):
                base = word[:-1*len(k)]
                return [base+new_ending for new_ending in endings]

        return []

    @classmethod
    def get_hide_words(cls, hide_word, english):
        if not english:
            return [hide_word]

        hide_word = cls.unstress(hide_word)
        if hide_word[-2:] in ["ar", "er", "ir", "ír"]:
            hide_word = hide_word[:-1]

        hide_words = [hide_word]
        hide_words += cls.anglicise(hide_word)
        return list(map(cls.unstress, hide_words))

    three_letter_english = ["ago","all","and","any","are","bad","bed","big","bit","boy","but","buy","bye",
            "can","car","cut","dad","day","did","die","eat","far","for","fun","get","got","had","has",
            "her","hey","him","his","hit","hot","how","law","let","lie","lot","man","men","met","new",
            "not","now","off","one","our","out","put","say","see","set","she","sit","six","ten","the",
            "too","try","two","was","way","who","why","yet","you"]

    @classmethod
    def should_obscure(cls, word, hide_word):

        word = word.replace("h", "")
        word = word.replace("ff", "f")
        word = word.replace("dd", "d")
        word = word.replace("ss", "s")
        word = word.replace("aa", "a")
        word = word.replace("ee", "e")
        word = word.replace("oo", "o")
        word = word.replace("ii", "i")

        l = min(len(word), len(hide_word))
        if l<=2:
            return False

        if l==3 and word in cls.three_letter_english:
            return False
        distance = int(l/4) if l >= 4 else 0
        matches = [word[:l]]

        # fix for matching blah to xblah (xbla doesn't match, but xblah does even though it's longer)
        if l < len(word) and l >= len(word) - distance:
            matches.append(word[:l+distance])

        for match in matches:
            if fuzzy_distance(match, hide_word[:l]) <= distance:
                return True

        return False

    @staticmethod
    def obscure_list(items, hide_word):
        for item in items:
            yield DeckBuilder.obscure_gloss(item, hide_word, hide_all=True)

    @staticmethod
    def format_syns_html(deck, extra, css_class=''):

        if css_class and not css_class.endswith(' '):
            css_class += ' '

        deck_str = (
            f"""<span class="{css_class}syn deck">{", ".join(deck)}</span>""" if len(deck) else ""
        )
        separator = ", " if len(deck_str) else ""
        extra_str = (
            f"""<span class="{css_class}syn extra">{separator}{", ".join(extra)}</span>"""
            if len(extra)
            else ""
        )

        return deck_str + extra_str

    @classmethod
    def format_syns(cls, deck, extra, hide_word=None):
        obscured_deck = list(cls.obscure_list(deck, hide_word))
        obscured_extra = list(cls.obscure_list(extra, hide_word))

        has_obscured = obscured_deck != deck or obscured_extra != extra

        if has_obscured:
            return cls.format_syns_html(deck,extra, 'unobscured') \
                    + cls.format_syns_html(obscured_deck, obscured_extra, 'obscured')

        return cls.format_syns_html(deck,extra)

    @classmethod
    def format_usage(cls, usage):

        ety_footnotes = [ e["ety"] for e in usage if e.get("ety") ]
        general_etynote = len(usage) == 1

        usage_footnotes = []
        [ usage_footnotes.append(w["note"]) for e in usage for w in e["words"] if w.get("note") and w["note"] not in usage_footnotes ]
        all_usage_footnotes = [w["note"] for e in usage for w in e["words"] if w.get("note") and w["note"]]

        # set a flag if all senses share the same usenote
        general_usenote = len(usage_footnotes) == 1 and all("note" in w for e in usage for w in e["words"])

        data = []

        primary_pos = usage[0]["words"][0]["pos"]
        for ety_idx, ety in enumerate(usage):
            classes = ["etymology", f"etymology_{ety_idx}"]
            if len(usage) == 1:
                classes.append("solo_etymology")
            data.append(f'<div class="{" ".join(classes)}">\n')
            ety_note = ety.get("ety")
            ety_id = ety_footnotes.index(ety_note) if ety_note else None

            for w in ety["words"]:
                word_note = w.get("note", None)
                usage_id = usage_footnotes.index(word_note) if word_note else None

                for sense in w["senses"]:
                    usage_key = chr(ord("1")+usage_id) if not general_usenote and usage_id is not None else None
                    ety_key = chr(ord("a")+ety_id) if not general_etynote and ety_id is not None else None

                    data += cls.format_sense(sense, w["pos"], w.get("noun_type", None), usage_key, ety_key, primary_pos)
                    if "hint" in sense:
                        data += cls.format_sense(sense, w["pos"], w.get("noun_type", None), usage_key, ety_key, primary_pos, hint=True)

            data.append('</div>\n')

        extra_classes = ["general_footnote"] if general_usenote else []
        data += cls.format_usage_footnotes(usage_footnotes, extra_classes)

        extra_classes = ["general_footnote"] if general_etynote else []
        data += cls.format_ety_footnotes(ety_footnotes, extra_classes)

        res = "".join(data)
        return res

    @classmethod
    def format_usage_footnotes(cls, notes, extra_classes=[]):
        classes = ["usage_footnote"]
        c = " ".join(classes + extra_classes)
        return cls.format_footnotes(notes, c, "1")

    @classmethod
    def format_ety_footnotes(cls, notes, extra_classes=[]):
        classes = ["ety_footnote"]
        c = " ".join(classes + extra_classes)
        return cls.format_footnotes(notes, c, "a")

    @classmethod
    def format_footnotes(cls, notes, note_class, start_char):
        res = []

        for idx,note in enumerate(notes):
            anchor = chr(ord(start_char)+idx)
            res.append(f'<span id="footnote_{anchor}" class="footnote {note_class}"><span class="footnote_id">{anchor}</span><span class="footnote_data">' + re.sub(r"\\n", '<br>', html.escape(note)) + '</span></span>\n')

        return res

    @classmethod
    def format_sense(cls, sense, pos, noun_type, usage_key, ety_key, primary_pos, hint=False):
        res = []

        if noun_type:
            display_pos = noun_type
        elif pos == "v":
            display_pos = "v" + sense.get("type", "")
        else:
            display_pos = pos


        classes = ["pos", pos]
        if hint:
            classes.append("hint")

        if pos == "n" and "type" in sense:
            classes.append(sense["type"])
        elif pos == "n" and noun_type:
            classes.append(re.sub("[^a-zA-Z]", "", noun_type))
        elif pos == "v" and sense.get("type") in ["r","p"]:
            classes.append("reflexive")

        tags = []
        if pos == "n" and "type" in sense and not hint:
            tags.append(sense["type"])
        if "tag" in sense:
            tags.append(sense["tag"])
            classes += sorted(cls.get_location_classes(sense["tag"]))

        res.append(f'<span class="{" ".join(classes)}">')

        c = "pos_tag pos_tag_primary" if pos == primary_pos else "pos_tag"
        res.append(f'<span class="{c}">{display_pos}</span>')

        if tags:
            res.append(f'<span class="qualifier">{", ".join(tags)}</span>')


        if not hint or not sense.get("hint"):
            res.append(f'<span class="gloss">{html.escape(sense["gloss"])}</span>')
        else:
            res.append(f'<span class="gloss">{html.escape(sense["hint"])}</span>')

        if usage_key:
            res.append(f'<span class="footnote_link usage_link">{usage_key}</span>')
        if ety_key:
            res.append(f'<span class="footnote_link ety_link">{ety_key}</span>')

        if sense.get("syns"):
            syns = ", ".join(x[len("Thesaurus:"):] if x.startswith("Thesaurus:") else x for x in sense["syns"][:cls.MAX_SYNONYMS])
            res.append(f'<span class="synonyms">{syns}</span>')

        res.append("</span>\n")
        return res


    def validate_note(self, item):

        if item["guid"] in self.seen_guids:
            eprint(f"Duplicate guid from {item}")
        else:
            self.seen_guids[item["guid"]] = 1

        for key in ["Spanish", "Data", "Part of Speech", "Audio"]:
            if item[key] == "":
                eprint(f"Missing {key} from {item}")
                return False

        return True


    def get_feminine_forms(self, word):
        for word_obj in self._words.get_words(word, "n"):
            # Return inside loop intentional, we only want to process the first word
            return word_obj.forms.get("f")

    def get_noun_gender(self, word_obj):
        if not word_obj.genders:
            return "n"

        noun_type = re.sub("-p", "p", word_obj.genders)
        if noun_type == "mfbysense":
            noun_type = "mf"
        elif noun_type == "m; f":
            noun_type = "mf"
        elif noun_type == "mfbysensep":
            noun_type = "mfp"
        elif noun_type not in ["m", "f", "mf", "mp", "fp", "mfp"]:
            raise ValueError("Unexpected noun type", noun_type)

        return noun_type

    def get_filtered_senses(self, word):
        pos = word.pos if word.pos != "n" else word.genders
        return [s for s in word.senses if self.filter_gloss(word, s)]

    def get_word_objs(self, word, primary_pos, get_all_pos=True):

        all_pos = []

        if get_all_pos:
            poslemmas = self.all_forms.get_lemmas(word)
            for pos, lemma  in [x.split("|") for x in sorted(poslemmas)]:
                if pos not in [ primary_pos, "v" ] and pos not in all_pos:
                    all_pos.append(pos)
        all_pos = [ primary_pos ] + sorted(all_pos)

        items = []
        for pos in all_pos:
            if pos == primary_pos:
                lemmas = [word]
            else:
                lemmas = self.get_lemmas(word, pos)
            for lemma in lemmas:
                # Don't match adjectives to their opposite gender nouns
                if primary_pos == "adj" and pos == "n" and lemma != word:
                    continue

                for wordobj in self._words.get_words(lemma, pos):
                    # Skip noun forms
                    if wordobj.pos == "n" and not wordobj.genders:
                        continue
                    if wordobj not in items:
                        items.append(wordobj)

                # Safety check, fail if the primary_pos isn't found
                if pos == primary_pos and not len(items):
                    return items

        return items

    def group_ety(self, words):
        groups = {}
        for word in words:
            ety = word.etymology
            groups[ety] = groups.get(ety, [])
            groups[ety].append(word)
        return groups.values()

    def group_pos(self, words):
        groups = {}
        for word in words:
            pos = word.pos
            groups[pos] = groups.get(pos, [])
            groups[pos].append(word)
        return groups.values()

    def process_nouns(self, words):

        res = {}
        for w in words:
            if w.pos != "n":
                continue

            # Skip filtered words
            if not any(self.get_filtered_senses(w)):
                continue

            gender = self.get_noun_gender(w)

            # Tag f-el nouns
            if gender == "f" and w.word in self.el_f_nouns:
                res["f-el"] = res.get("f-el", []) + [w]

            # Find opposite gender pair for m/f words (el doctor, la doctora)
            elif gender == "m" and "f" in w.forms:
                mates = []
                for femnoun in w.forms["f"]:
                    if femnoun == w.word:
                        continue

                    # Get all possible words for the given femnoun
                    femwords = list(self._words.get_words(femnoun, "n"))

                    # And then filter out only those that reference back to the masculine noun either in their declared forms
                    # or with an explicit "feminine of" sense
                    for f in femwords:
                        if (w.word in f.forms.get("m",[]) or \
                           any(re.search(fr'(feminine|female equivalent) of "{w.word}"', sense.gloss) for sense in f.senses)) and\
                           f not in mates:
                               mates.append(f)

                res["m/f"] = res.get("m/f", [])
                res["m/f"].append([w] + mates)
                #res["m/f"] = res.get("m/f", []) + [w] + mates

            else:
                res[gender] = res.get(gender, []) + [w]

        # mark m-f if there are both masculine and feminine uses for the same word (el cometa, la cometa)
        # TODO: also check "m/f"
        #mf = [k for k in res.keys() if k in ["m", "f", "m/f"]]
        #if len(mf) > 1:
        if "m" in res and "f" in res:
            primary = next(k for k in res.keys() if k in ["m", "f"])
            secondary = "f" if primary=="m" else "m"
            res[primary] += res[secondary]
            del res[secondary]
            res = {"m-f" if k == primary else k:v for k,v in res.items()}

        return res

    @staticmethod
    def shorten_gloss(gloss, max_length):

        # Split and shorten until short enough
        for separator in [ '(', '[', ';' ]:
            if len(gloss) < max_length:
                break

            # strip () and [] only at the end of gloss
            if separator == "(" and not gloss.endswith(")") or \
               separator == "[" and not gloss.endswith("]"):
                continue

            break_pos = gloss.rfind(separator)
            if break_pos > 1:
                new = gloss[:break_pos]
                if new:
                    gloss = new

        # If it's still too long, strip the last , until less than max length or no more , to strip
        break_pos = len(gloss)
        while break_pos and len(gloss) > max_length:
            break_pos = gloss.rfind(",", 0, break_pos)
            if break_pos <= 0:
                break

            # don't break if there's an open ( to the left of break_pos
            if gloss.rfind("(", 0, break_pos) > gloss.rfind(")", 0, break_pos):
                continue

            if break_pos:
                gloss = gloss[:break_pos]

        return gloss.strip()

    def add_shortdefs(self, usage, hide_word, max_length=60):

        def is_reflexive(sense_data):
            return any(x in sense_data.get("type","") for x in ["r","p"])

        if not usage:
            return

        glosses = {}

        pos_data = usage[0]["words"][0]

        short_senses = [ pos_data["senses"][0] ]

        # If a noun has male/female words, try to take a gloss from each
        if pos_data["pos"] == "n" and pos_data.get("noun_type") in ["m-f","m/f"]:
            for sense in pos_data["senses"][1:]:
                if sense.get("type") != short_senses[0].get("type"):
                    short_senses.append(sense)
                    break

        # If it's a verb and the first sense is not reflexive, search for a sense that is reflexive
        if pos_data["pos"] == "v" and not is_reflexive(short_senses[0]):
            for sense in pos_data["senses"][1:]:
                if is_reflexive(sense):
                    short_senses.append(sense)
                    break

        if len(short_senses) == 1 and len(pos_data["senses"]) > 1:
            short_senses.append(pos_data["senses"][1])

        hide_all=False
        for sense in pos_data["senses"]:
            if sense in short_senses:
                hint = self.shorten_gloss(self.obscure_gloss(sense["gloss"], hide_word, hide_all=hide_all), max_length)
                if hint == sense["gloss"]:
                    hint = ""
                sense["hint"] = hint
                hide_all=True

    @staticmethod
    def get_verb_type_and_tag(qualifier):
        if not qualifier:
            return ["", ""]

        verb_types = {
            "transitive": "t",
            "reflexive": "r",
            "intransitive": "i",
            "pronominal": "p",
            "takes a reflexive pronoun": "p",
            "ambitransitive": "x",
        }

        verb_type = []
        def replace(m):
            verb_type.append(verb_types[m.group("type")])
            return ""

        re_pattern = r"^\s*((also|or|and)\s+)?(?P<type>" + "|".join(verb_types.keys()) + r")\s*$"

        tag_items = []
        splits = iter(re.split("(, | or | and )", qualifier))
        prev_sep = ""
        for tag in splits:
            sep = next(splits,"")
            tag = re.sub(re_pattern, replace, tag)
            if tag:
                if prev_sep:
                    tag_items.append(prev_sep)
                tag_items.append(tag)
                prev_sep = sep

        new_type = "".join(verb_type)
        new_tag = "".join(tag_items)

        return new_type, new_tag

    def get_usage(self, word, primary_pos, get_all_pos=True, max_length=None):
        """ Returns data structure:
        [{
            "ety": "etymology notes", # Optional
            "words": [{
                    "word": "word",
                    "pos": "n",
                    "noun_type": "m-f", # Optional, for nouns, "m-f", "m/f"
                    "note": "usage notes", # Optional
                    "senses": [{
                        "type": "m", # Optional, for nouns, "m", "f", "mf", "f-el", for verbs a combination of [t,r,i,p,x]
                        "tag": "tag data", # Optional, qualifier for gloss
                        "gloss": "gloss"
                        "hint": "" # Optional, signals that this sense should be included when displaying shortdefs
                                   # if a non-empty string is provided, it will be used in place of the original gloss
                        "syns": ["syn1","syn2"] # Optional list of synonyms
                    }]
                    "usage": "usage notes" # Optional
                }],
        },
        {
            "ety": "etymology2",
            "words": ....
        }]
        """

        def get_sense_data(word, pos_type, word_tag, sense_filter=None):

            senses = []
            for sense in word.senses:
                gloss = self.filter_gloss(word, sense, sense_filter)
                if not gloss:
                    continue

                if word.pos == "v":
                    sense_type, sense_tag = self.get_verb_type_and_tag(sense.qualifier)
                elif word.pos == "n":
                    sense_type = word_tag
                    sense_tag = sense.qualifier
                else:
                    sense_type = None
                    sense_tag = sense.qualifier

                s = {}

                if sense_type:
                    s["type"] = sense_type
                if sense_tag:
                    s["tag"] = sense_tag
                s["gloss"] = gloss
                if sense.synonyms:
                    s["syns"] = sense.synonyms
                senses.append(s)

            return senses

        def get_word_data(word, pos_type=None, sense_tag=None, sense_filter=None):
            senses = get_sense_data(word, pos_type, sense_tag, sense_filter)
            if not senses:
                return {}

            word_data = { "pos": word.pos, "senses": senses }

            return word_data

        def get_noun_tag(word, words):
            """
            returns "mf" if word is noun is both masculine or feminine (dentista)
            returns "m/f" if the word is the masculine part of a masculine/feminine pair and the the mate has no useful sense (doctor, doctora)
            otherswise returns the nouns gender tag
            """

            if word.pos != "n":
                raise ValueError("word is not noun")

            noun_type = None

            if word.genders in [ "m", "f" ]:
                mate = "m" if word.genders == "f" else "f"

                # word is part of a m/f pair, check if its mate has usable senses
                if mate in word.forms and word.forms[mate] != word:
                    main_gloss = word.senses[0].gloss
                    mates = [ w for w in words if w.genders == mate ]
                    if not any(w for w in mates for s in w.senses if self.filter_gloss(w, s, main_gloss)):
                        return "m/f"


            noun_type = word.genders if word.genders else "unknown"

            noun_type = re.sub("-p", "p", noun_type)
            if noun_type == "mfbysense":
                noun_type = "mf"
            elif noun_type == "m; f":
                noun_type = "mf"
            elif noun_type == "mfbysensep":
                noun_type = "mfp"
            elif noun_type not in ["m", "f", "mf", "mp", "fp", "mfp"]:
                raise ValueError("Unexpected noun type", noun_type, word.word, word.pos, word.genders)

            return noun_type

        res = []
        words = self.get_word_objs(word, primary_pos, get_all_pos)

        etys = self.group_ety(words)
        for ety_words in etys:
            ety = {}
            if ety_words[0].etymology:
                ety["ety"] = ety_words[0].etymology
            words_data = []
            for group in self.group_pos(ety_words):

                if group[0].pos == "n":
                    m_f_data = None
                    for noun_type,words in self.process_nouns(group).items():
                        for w in words:
                            word_data = {}
                            word_notes = None
                            primary_sense = None

                            if noun_type == "m/f":
                                # Unlike all other nouns, which are lists of words [word1, word2, word3],
                                # m/f items will be a list of lists [[male1, female1], [male2, female2]]
                                # that should be merged into one group of senses
                                group = w
                                group_data = {}
                                for w in group:
                                    noun_tag = get_noun_tag(w, group)
                                    if noun_tag == noun_type:
                                        noun_tag = None

                                    data = get_word_data(w, noun_type, noun_tag, primary_sense)
                                    if not data:
                                        continue

                                    if not word_data:
                                        word_data = data
                                        primary_sense = word_data["senses"][0]["gloss"]
                                    else:
                                        word_data["senses"] += data["senses"]
                                        if w.use_notes:
                                            if word_notes and w.use_notes != word_notes:
                                                raise ValueError("usage conflict", word, word_notes, w.use_notes)
                                            word_notes = w.use_notes

                            else:
                                noun_tag = get_noun_tag(w, words)
                                if noun_tag == noun_type:
                                    noun_tag = None
                                word_data = get_word_data(w, noun_type, noun_tag)

                                if word_notes and w.use_notes != word_notes:
                                    raise ValueError("usage conflict", word)
                                word_notes = w.use_notes

                            if word_data:
                                if noun_type:
                                    word_data["noun_type"] = noun_type

                                if word_notes:
                                    word_data["note"] = word_notes

                                if noun_type == "m-f":
                                    if m_f_data:
                                        m_f_data["senses"] += word_data["senses"]
                                    else:
                                        m_f_data = word_data
                                        words_data.append(m_f_data)
                                else:
                                    words_data.append(word_data)

                else:
                    for w in group:
                        word_data = get_word_data(w)
                        if word_data:
                            if w.use_notes:
                                word_data["note"] = w.use_notes
                            words_data.append(word_data)


            if words_data:
                ety["words"] = words_data
                res.append(ety)

        self.add_shortdefs(res, word)
        return res

    def get_lemmas(self, word, pos):

        lemmas = []
        poslemmas = self.all_forms.get_lemmas(word)
        for form_pos, lemma  in [x.split("|") for x in sorted(poslemmas)]:
            if form_pos != pos:
                continue
            if lemma not in lemmas:
                lemmas.append(lemma)
        if not lemmas:
            return [word]

        # remove verb-se if verb is already in lemmas
        if pos == "v":
            lemmas = [x for x in lemmas if not (x.endswith("se") and x[:-2] in lemmas)]

        # resolve lemmas that are "form of" other lemmas
        good_lemmas = set()
        for lemma in lemmas:
            for word_obj in self._words.get_words(lemma, pos):
                good_lemmas |= set(self._words.get_lemmas(word_obj).keys())

        return sorted(good_lemmas)


    def add_synonyms(self, word, pos, synonyms, reciprocal=True):
        key = (word,pos)
        if key not in self.synonyms:
            self.synonyms[key] = list(synonyms) # Copy the list, since it will be modified
        else:
            for syn in synonyms:
                if syn not in self.synonyms[key]:
                    self.synonyms[key].append(syn)

        if reciprocal:
            for syn in synonyms:
                if syn != word:
                    self.add_synonyms(syn, pos, [word], False)

    def build_synonyms(self):
        self.synonyms = {}

        # Build synonyms
        for k,usage in self.allwords.items():
            word, pos = split_tag(k)
            # Only take synonyms from the primary defs in the first etymology
            for w in usage[0]["words"]:
                for sense in w["senses"]:
                    if "hint" in sense and "syns" in sense:
                        self.add_synonyms(word, pos, sense["syns"])


    def get_synonyms(self, word, pos, limit=5, only_in_deck=True):

        key = (word,pos)
        items = []
        for syn in self.synonyms.get(key, []):
            if syn.startswith("Thesaurus:"):
                syn = syn[len("Thesaurus:"):]
            if syn == word:
                continue
            if syn not in items:
                items.append(syn)

        in_deck = [k for k in items if make_tag(k, pos) in self.allwords]
        if only_in_deck or len(in_deck) > limit:
            return in_deck[:limit]

        return items[:limit]

    def get_noun_type(self, usage):
        return usage[0]["words"][0]["noun_type"] if usage[0]["words"][0]["pos"] == "n" else ""

    def verb_has_reflexive(self, usage):

        for sense in usage[0]["words"][0]["senses"]:
            if "r" in sense.get("type", "") or "p" in sense.get("type", ""):
                return True

        return False

    def get_phrase(self, word, usage):
        voice = ""
        phrase = ""
        display = None

        pos = usage[0]["words"][0]["pos"]
        noun_type = self.get_noun_type(usage)
        femforms = self.get_feminine_forms(word) if pos == "n" else None
        if femforms:
            voice = self._MALE1

            fems = [f"el {f}" if f in self.el_f_nouns else f"la {f}" for f in femforms]
            fem_display = ", ".join(fems)
            fem_phrase = ". ".join(fems)

            phrase = f"{fem_phrase}. el {word}"
            display = f"{fem_display}/el {word}"
        elif noun_type == "f-el":
            voice = self._FEMALE2
            phrase = f"el {word}"
        elif noun_type == "f":
            voice = self._FEMALE2
            phrase = f"la {word}"
        elif noun_type == "fp":
            voice = self._FEMALE2
            phrase = f"las {word}"
        elif noun_type == "m-f":
            voice = self._FEMALE1
            phrase = f"la {word}. el {word}"
            display = f"la/el {word}"
        elif noun_type == "m":
            voice = self._MALE1
            phrase = f"el {word}"
        elif noun_type == "mf":
            voice = self._MALE1
            phrase = f"el {word}. la {word}"
            display = f"el/la {word}"
        elif noun_type == "mp":
            voice = self._MALE1
            phrase = f"los {word}"
        elif pos == "n":
            raise ValueError(f"Word {word} has unknown noun type {noun_type}")
        elif pos == "v" \
                and " " not in word \
                and word[-2:] in ["ar", "er", "ir", "ír"] \
                and self.verb_has_reflexive(usage):
                    voice = self._FEMALE1
                    phrase = f"{word}. {word}se"
                    display = f"{word}/{word}se"
        else:
            voice = self._FEMALE1
            phrase = word

        if not display:
            display = phrase

        return {"voice": voice, "phrase": phrase, "display": display}


    _REGIONS = {
        "canary islands": set(),
        "caribbean": {
            "cuba",
            "dominican republic",
            "puerto rico",
            "panama",
            "venezuela",
            "colombia",
        },
        "central america": {
            "costa rica",
            "el salvador",
            "guatemala",
            "honduras",
            "nicaragua",
            "panama",
        },
        "latin america": set(),
        "mexico": set(),
        "south america": {
            "argentina",
            "bolivia",
            "chile",
            "colombia",
            "ecuador",
            "paraguay",
            "peru",
            "uruguay",
            "venezuela",
        },
        "spain": set(),
        "philippines": set(),
        "united states": {"california", "louisiana", "new mexico", "texas"},
    }

    _PLACE_TO_REGION = {
        item: region for region, items in _REGIONS.items() for item in items
    }


    @classmethod
    def get_location_classes(cls, tag_string):
        items = {t.strip() for t in tag_string.lower().split(",")}

        places = items & cls._PLACE_TO_REGION.keys()
        regions = items & cls._REGIONS.keys()

        meta_classes = set()

        if len(places) == 1 and len(regions) == 0:
            meta_classes.add("only-" + next(iter(places)))

        place_regions = set()
        for place in places:
            place_regions.add(cls._PLACE_TO_REGION[place])

        if len(regions | place_regions) == 1:
            meta_classes.add("only-" + next(iter(regions | place_regions)))

        #    all_places = places
        #    for region in regions:
        #        all_places |= _PLACES[region]

        # Special case handling for "latin america"
        if (len(places) or len(regions)) and not len(
            (regions | place_regions)
            - {
                "caribbean",
                "central america",
                "mexico",
                "south america",
                "united states",
                "latin america",
            }
        ):
            meta_classes.add("only-latin-america")

        return [item.replace(" ", "-") for item in regions | places | meta_classes]




    def build_item(self, word, pos, mediadir):
        spanish = word.strip()
        pos = pos.lower()
        item_tag = make_tag(spanish, pos)

        usage = self.allwords[item_tag]
        meta = self.allwords_meta.get(item_tag)

        if not usage:
            raise ValueError("No usage data", spanish, pos)

        deck_syns = self.get_synonyms(spanish, pos, self.MAX_SYNONYMS, only_in_deck=True)
        extra_syns = [
                k
                for k in self.get_synonyms(spanish, pos, self.MAX_SYNONYMS, only_in_deck=False)
                if k not in deck_syns
            ] if len(deck_syns) < self.MAX_SYNONYMS else []

        defs = []
        for w in usage[0]["words"]:
            for s in w["senses"]:
                if "hint" in s:
                    gloss = s["hint"] if s["hint"] else s["gloss"]
                    defs += [z.strip() for x in gloss.split(";") for z in x.split(",")]

        seen_tag = "|".join(sorted([d for d in deck_syns if d != "..."]) + sorted([d for d in defs if d != "..."]))
        if seen_tag in self.seen_hints:
            eprint(f"Warning: {seen_tag} is used by {item_tag} and {self.seen_hints[seen_tag]}, adding syn")
            deck_syns.insert(0, self.seen_hints[seen_tag].split(":")[1])
        else:
            self.seen_hints[seen_tag] = item_tag

        tts_data = self.get_phrase(spanish, usage)

        sound = get_speech(tts_data["voice"], tts_data["phrase"], mediadir)

        all_usage_pos = []
        [all_usage_pos.append(w["pos"]) for ety in usage for w in ety["words"] if w["pos"] not in all_usage_pos]

        lookups = [[spanish, pos] for pos in all_usage_pos]
        sentences = self.get_sentences(lookups, 3)

        self.store_sentences(lookups)

        display_pos = self.get_noun_type(usage) if pos == "n" else pos

        item = {
            "Spanish": spanish,
            "Part of Speech": display_pos,
            "Synonyms": self.format_syns(deck_syns, extra_syns, hide_word=spanish),
            "Data": self.format_usage(usage),
            "Sentences": sentences,
            "Display": tts_data["display"],
            "Audio": self.format_sound(sound),
            "guid": genanki.guid_for(item_tag, "Jeff's Spanish Deck"),
        }

        item["tags"] = []
        if meta:
            item["tags"] += meta.get("tags", [])

        FILE = os.path.join(mediadir, sound)
        if os.path.isfile(FILE):
            self.media_files.append(FILE)
        else:
            item["Audio"] = ""

        if not self.validate_note(item):
            exit(1)

        return item


    def wordlist_indexof(self, target):
        if ":" in target:
            return self.allwords_index.index(target)

        target = ":" + target
        for i,item in enumerate(self.allwords_index):
            if item.endswith(target):
                return i

    def wordlist_insert_after(self, target, wordtag, usage):

        index = self.wordlist_indexof(target)
        if not index:
            #eprint(f"ERROR: {target} not found in wordlist, unable to insert {wordtag} after it")
            return

        # Do nothing if it's already in the wordlist
        if wordtag in self.allwords:
            return

        self.allwords[wordtag] = usage
        self.allwords_index.insert(index + 1, wordtag)

    def wordlist_replace(self, target, wordtag, usage):

        index = self.wordlist_indexof(target)
        if not index:
            #eprint(f"ERROR: {old_tag} not found in wordlist, unable to replace with {wordtag}")
            return

        # If the replacement is already in the wordlist, just delete the replacee
        if wordtag in self.allwords:
            self.wordlist_remove(target)
            return

        old_tag = self.allwords_index[index]
        del self.allwords[old_tag]

        # Preserve metadata
        if old_tag in self.allwords_meta:
            self.allwords_meta[wordtag] = self.allwords_meta.pop(old_tag)

        self.allwords[wordtag] = usage
        self.allwords_index[index] = wordtag

    def wordlist_remove(self, target):
        index = self.wordlist_indexof(target)
        if index is None:
#            eprint(f"ERROR: {wordtag} not found in wordlist, unable to remove")
            return

        old_tag = self.allwords_index[index]
        del self.allwords[old_tag]
        del self.allwords_index[index]


    def wordlist_append(self, wordtag, usage):
        # Do nothing if it's already in the wordlist
        if wordtag in self.allwords:
            return

        self.allwords[wordtag] = usage
        self.allwords_index.append(wordtag)

    def load_wordlists(self, wordlists, allowed_flags):
        # Wordlist is a list of strings
        # Each wordlist string must be a filename, optionally trailed ; separated key=value pairs
        # wordlist.txt
        # wordlist2.txt;limit=1000
        # wordlist3.txt;limit=1000;allow=NOSENT
        #
        # allow options are applied only to the specified deck and are cumulative with the global
        # --allow-flag options
        #
        # Specifying a limit will limit processing to the first N allowed words in the wordlist

        # read through all the files to populate the synonyms and excludes lists
        for wordlist in wordlists:

            all_allowed_flags = allowed_flags
            limit = 0
            metadata = {}

            filename, *options = wordlist.split(";")
            for option in options:
                k,v = option.split("=")
                k = k.lower().strip()
                if k == "allow":
                    all_allowed_flags.append(v)
                elif k == "limit":
                    limit = int(v)
                elif k == "tag":
                    if "tags" not in metadata:
                        metadata["tags"] = [v]
                    else:
                        metadata["tags"].append(v)
                else:
                    raise ValueError(f'Unknown option "{option}" specified in wordlist {wordlist}')

            with open(filename, newline="") as csvfile:
                self.load_wordlist(csvfile, all_allowed_flags, limit, metadata)

    def load_wordlist(self, data, allowed_flags, limit=0, metadata=None):
        # data is an iterator that provides csv formatted data

        csvreader = csv.DictReader(data)
        for reqfield in ["pos", "spanish"]:
            if reqfield not in csvreader.fieldnames:
                raise ValueError(
                    f"No '{reqfield}' field specified in file {wordlist}"
                )

        count = 0
        for row in csvreader:
            if not row:
                continue

            item_tag = make_tag(row["spanish"], row["pos"])

            position = row.get("position", None)
            # Negative position indicates that all previous instances of this word should be removed
            if position and position.startswith("-"):
                self.wordlist_remove(item_tag)
                continue

            if "flags" in row and row["flags"]:
                flags = set(row["flags"].split("; "))
                if flags.difference(allowed_flags):
                    continue

            usage = self.get_usage(row["spanish"], row["pos"])
            if not usage:
                continue

            if metadata and item_tag not in self.allwords_meta:
                self.allwords_meta[item_tag] = metadata

            # Skip words that have don't have usage for the given word/pos
            if usage[0]["words"][0]["pos"] != row["pos"]:
                continue

            if not position:
                self.wordlist_append(item_tag, usage)

            # +pos:word indicates that the entry should be positioned immedialy after the specified pos:word
            # or after the first occurance of word if pos: is not specified
            elif position.startswith("+"):
                self.wordlist_insert_after(position[1:], item_tag, usage)

            # pos:word will replace the specific pos:word or the first occurance of the word if pos: is not specified
            elif not position[0].isdigit() and position[0] != "-":
                self.wordlist_replace(position, item_tag, usage)

            else:
                raise ValueError(f"Position {position} does not exist, ignoring")

            count += 1
            if limit and count>limit:
                break


    def compile(self, modelfile, filename, deck_name, deck_guid, deck_desc, mediadir, limit, ankideck=None, tags=[]):

        self.ankideck = ankideck
        if ankideck:
            ankidb = os.path.join(
                os.path.expanduser("~"), ".local/share/Anki2", ankideck, "collection.anki2"
            )
            if not os.path.isfile(ankidb):
                print("Cannot find anki database:", ankidb)
                exit(1)

            self.db_notes = self.load_db_notes(ankidb, deck_name)
            for guid, item in self.db_notes.items():
                hashval = self.get_note_hash(guid, item["flds"], item["tags"])
                self.db_timestamps[hashval] = item["mod"]

        with open(modelfile) as infile:
            model_info = json.load(infile)
        card_model = self.make_card_model(model_info)
        my_deck = genanki.Deck(deck_guid, deck_name, deck_desc)

        if limit and limit < len(self.allwords_index):
            for tag in self.allwords_index[limit:]:
                del self.allwords[tag]
            self.allwords_index = self.allwords_index[:limit]

        self.build_synonyms()
        self.rows = []

        counter = {}
        for wordtag in self.allwords_index:
            word, pos = split_tag(wordtag)

            item = self.build_item(word, pos, mediadir)
            self.notes[item["guid"]] = item

            tags = item.get("tags",[])
            if tags and len(tags) > 1:
                print(item)
                raise ValueError("Multiple tags", tags)
            idx = tags[0] if tags else -1
            if not idx in counter:
                counter[idx] = 0
            counter[idx] += 1
            position = counter[idx]

            item["Rank"] = str(position)

            item["tags"] += tags
            item["tags"].append(item["Part of Speech"])
            item["tags"].append(str(math.ceil(position / 500) * 500))

            row = []
            for field in self._fields:
                row.append(item[field])

            note = MyNote(
                model=card_model,
                sort_field=1,
                fields=row,
                guid=item["guid"],
                tags=item["tags"],
                due=position
            )
            # preserve the mod timestamp if the note matches with the database
            note.mod_ts = self.get_mod_timestamp(note)
            if not note.mod_ts and self.ankideck:
                if item["guid"] not in self.db_notes:
                    print(f"added: {wordtag}")
                elif False:
                    old_data = self.db_notes[item["guid"]]
                    if old_data["flds"] != note._format_fields():
                        old_fields = old_data["flds"].split(chr(31))
                        new_fields = note._format_fields().split(chr(31))
                        for idx in range(len(old_fields)):
                            old = old_fields[idx]
                            new = new_fields[idx]
                            if old != new:
                                if idx == 6:
                                    print(f"{wordtag} sentences changed")
                                elif idx != 0:
                                    print(f"{wordtag}  field {idx}: {old} => {new}")
                    else:
                        print(f"  old tags: {old_data['tags']}")
                        print(f"  new tags: {note._format_tags()}")

            my_deck.add_note(note)
            self.rows.append(row+[",".join(item["tags"])])

        package_filename = os.path.join(os.getcwd(), filename + ".apkg")
        my_package = genanki.Package(my_deck)
        my_package.media_files = self.media_files
        my_package.write_to_file(package_filename)


    @staticmethod
    def load_shortdefs(filename):
        shortdefs = {}
        if not filename:
            return shortdefs

        with open(filename, newline="") as csvfile:
            csvreader = csv.DictReader(csvfile)
            for reqfield in ["spanish", "pos", "shortdef"]:
                if reqfield not in csvreader.fieldnames:
                    raise ValueError(f"No '{reqfield}' field specified in file {filename}")
            for row in csvreader:
                if not row or row.get("shortdef", "") == "":
                    continue

                common_pos = Word.get_common_pos(row["pos"])
                item_tag = make_tag(row["spanish"], common_pos)
                shortdefs[item_tag] = {row["pos"]: {"": row["shortdef"]}}

        return shortdefs

    @classmethod
    def load_ignore(cls, filename):
        if not filename:
            return {}

        with open(filename) as infile:
            return cls.load_ignore_data(infile)

    @staticmethod
    def load_ignore_data(data):
        ignore = {}
        for line in data:
            if line.strip().startswith("#") or line.strip() == "":
                continue

            if line.startswith("- "):
                (word, pos, note, syn, gloss) = Wordlist.parse_line(line[2:])
                if word not in ignore:
                    ignore[word] = {}
                if pos not in ignore[word]:
                    ignore[word][pos] = {}
                if note not in ignore[word][pos]:
                    ignore[word][pos][note] = []
                if gloss not in ignore[word][pos][note]:
                    ignore[word][pos][note].append(gloss)

        return ignore


def build_deck(params=None):

    parser = argparse.ArgumentParser(description="Compile anki deck")
    parser.add_argument("deckfile", help="Name of deck to build")
    parser.add_argument(
        "-m",
        "--mediadir",
        help="Directory containing deck media resources (default: DECKFILE.media)",
    )
    parser.add_argument(
        "-w",
        "--wordlist",
        action="append",
        help="List of words to include/exclude from the deck (default: DECKFILE.csv)",
    )
    parser.add_argument(
        "-t",
        "--tag",
        action="append",
        help="Add specified to to all notes (can be declared multiple times)",
    )
    parser.add_argument(
        "--allow-flag",
        action="append",
        help="Include wordlist items even if they have specificed flag (can be declared multiple times)"
    )
    parser.add_argument(
        "--short-defs",
        help="CSV file with short definitions (default DECKFILE.shortdefs)",
    )
    parser.add_argument("-l", "--limit", type=int, help="Limit deck to N entries")
    parser.add_argument(
        "--dump-sentence-ids", help="Dump high scoring sentence ids to file"
    )
    parser.add_argument("--dump-credits", help="Dump high scoring sentence ids to file")
    parser.add_argument("--dump-notes", help="Dump notes to file")
    parser.add_argument(
        "--dump-changes", help="Dump list of removed/added note ids to file (requires --anki)"
    )
    parser.add_argument( "--model", help="Read model info from JSON file", required=True)
    parser.add_argument("--deck-name", help="Deck Name", default="Deck")
    parser.add_argument("--deck-guid", help="Deck GUID", required=True, type=int)
    parser.add_argument("--deck-desc", help="Deck Description", default="")
    parser.add_argument("--anki", help="Read/write data from specified anki profile")
    parser.add_argument("--allforms", help="Load word forms from file")
    parser.add_argument(
        "--dictionary", help="Dictionary file name (DEFAULT: es-en.txt)",
        default="es-en.txt"
    )
    parser.add_argument(
        "--dictionary-custom", help="File containing dictionary customizations"
    )
    parser.add_argument(
        "--sentences", help="Sentences file name (DEFAULT: sentences.tsv)",
        default="sentences.tsv"
    )
    parser.add_argument(
        "--data-dir",
        help="Directory contaning the dictionary (DEFAULT: SPANISH_DATA_DIR environment variable or 'spanish_data')",
    )
    parser.add_argument(
        "--custom-dir",
        help="Directory containing dictionary customizations (DEFAULT: SPANISH_CUSTOM_DIR environment variable or 'spanish_custom')",
    )
    parser.add_argument("--low-mem", help="Use less memory", action='store_true', default=False)
    args = parser.parse_args(params)

    if args.tag:
        for tag in args.tag:
            if not re.match("^[0-9a-zA-Z_]+$", tag):
                print(f"Invalid tag: '{tag}'. May only contain alphanumerics + _")
                exit(1)
    else:
        args.tag = []

    if not args.data_dir:
        args.data_dir = os.environ.get("SPANISH_DATA_DIR", "spanish_data")

    if not args.custom_dir:
        args.custom_dir = os.environ.get("SPANISH_CUSTOM_DIR", "spanish_custom")

    if not args.mediadir:
        args.mediadir = args.deckfile + ".media"

    if not args.wordlist:
        args.wordlist = [args.deckfile + ".csv"]

    if not args.short_defs and os.path.isfile(args.deckfile + ".shortdefs"):
        args.short_defs = args.deckfile + ".shortdefs"

    if not args.allow_flag:
        args.allow_flag = set()

    if not os.path.isdir(args.mediadir):
        print(f"Deck directory does not exist: {args.mediadir}")
        exit(1)

    for wordlist in args.wordlist:
        wordlist = wordlist.split(";")[0]
        if not os.path.isfile(wordlist):
            print(f"Wordlist file does not exist: {wordlist}")
            exit(1)

    if args.dump_changes and not args.anki:
        print("Use of --dump-changes requires --anki profile to be specified")
        exit(1)

    if not os.path.isfile(args.model):
        print(f"Model JSON does not exist: {args.model}")
        exit(1)

    with open(args.dictionary) as wordlist_data:
        cache_words = not args.low_mem
        dictionary = Wordlist(wordlist_data, cache_words=cache_words)

    if args.allforms:
        allforms = AllForms.from_file(args.allforms)
    else:
        allforms = AllForms.from_wordlist(wordlist)

    ignore = DeckBuilder.load_ignore(args.dictionary_custom)

    sentences = spanish_sentences(
        sentences=args.sentences, data_dir=args.data_dir, custom_dir=args.custom_dir
    )
    shortdefs = DeckBuilder.load_shortdefs(args.short_defs)

    deck = DeckBuilder(dictionary, sentences, ignore, allforms, shortdefs)
    deck.load_wordlists(args.wordlist, args.allow_flag)
    deck.compile(args.model, args.deckfile, args.deck_name, args.deck_guid, args.deck_desc, args.mediadir, args.limit, args.anki, args.tag)

    if args.dump_sentence_ids:
        deck.dump_sentences(args.dump_sentence_ids)

    if args.dump_notes:
        with open(args.dump_notes, "w", newline="") as outfile:
            csvwriter = csv.writer(outfile)

            fields = deck._fields+["tags"]
            #del fields[7]  # audio
            #del fields[0]  # rank
            csvwriter.writerow(fields)

            for row in deck.rows:
                #del row[7]
                #del row[0]
                csvwriter.writerow(row)

    if args.dump_changes:
        with open(args.dump_changes, "w") as outfile:
            changes = []
            for guid in deck.db_notes.keys() - deck.notes.keys():
                changes.append((int(deck.db_notes[guid]["nid"]), deck.db_notes[guid]["word"], guid, "-"))
            for guid in deck.notes.keys() - deck.db_notes.keys():
                changes.append((int(deck.notes[guid]["Rank"]), f'{deck.notes[guid]["Part of Speech"]} {deck.notes[guid]["Spanish"]}', guid, "+"))

            for rank, word, guid, change in sorted(changes):
                outfile.write(f'{change}{rank} {word} {guid}\n')

            if len(changes):
                print(f'{len(changes)} words added/subtracted, {len(deck.db_notes)} items in db, {len(deck.notes)} items in deck')


    if args.dump_credits:
        deck.dump_credits(args.dump_credits)

if __name__ == "__main__":
    build_deck(sys.argv[1:])
