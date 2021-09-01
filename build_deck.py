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

    def filter_gloss(self, wordobj, sense):
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
        if not re.match("[^ :,.]", gloss):
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
            f'<div class="sentence"><span class="spa">{item[0]}</span><br>\n<span class="eng">{html.escape(item[1])}</span></div>'
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

    @staticmethod
    def obscure_gloss(gloss, hide_word, distance=None, hide_first=False, hide_all=False):

        def is_first_word(data):
            if not len(data):
                return True
            if len(data) == 2 and data[0].lower() in ["a", "an", "to"]:
                return True
            return False

        if distance is None:
            distance = int(len(hide_word)/4)

        if hide_all:
            hide_first = True

        data = []
        splits = iter(re.split(r'(\W+)', gloss))
        all_hidden = True
        for word in splits:
            sep = next(splits, None)
            if not word and sep:
                data.append(sep)
                continue

            if fuzzy_distance(word, hide_word)<=distance and (hide_first or not is_first_word(data)):
                data.append("...")
            else:
                data.append(word)
                if all_hidden and word.lower() not in ["a", "an", "to"]:
                    all_hidden = False

            if sep:
                data.append(sep)

        if hide_all or not all_hidden:
            gloss = "".join(data)

        # TODO: Ensure this doesn't obscure everything?
        m = re.match(r'(?P<pre>.*?)(apocopic form|diminutive|ellipsis|clipping|superlative|plural) of ".*?"(?P<post>.*)', gloss)
        if m and (hide_all or m.group("pre") or m.group("post")):
            gloss = re.sub(r'(apocopic form|diminutive|ellipsis|clipping|superlative|plural) of ".*?"', r"...", gloss)

        return gloss


    @staticmethod
    def obscure_list(items, hide_word, distance=None):

        if distance is None:
            distance = int(len(hide_word)/4)

        for item in items:
            yield DeckBuilder.obscure_gloss(item, hide_word, distance, True, True)

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
        multi_etynotes = len(usage) > 1

        usage_footnotes = [ w["note"] for e in usage for w in e["words"] if w.get("note") ]
        multi_usenotes = len(usage_footnotes) > 0
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
                    ety_key = chr(ord("a")+ety_id) if multi_etynotes and ety_id is not None else None
                    usage_key = chr(ord("1")+usage_id) if multi_usenotes and usage_id is not None else None

                    data += cls.format_sense(sense, w["pos"], w.get("noun_type", None), ety_key, usage_key, primary_pos)
                    if "hint" in sense:
                        data += cls.format_sense(sense, w["pos"], w.get("noun_type", None), ety_key, usage_key, primary_pos, hint=True)

            data.append('</div>\n')

        data += cls.format_usage_footnotes(usage_footnotes)
        data += cls.format_ety_footnotes(ety_footnotes)

        res = "".join(data)
        return res

    @classmethod
    def format_usage_footnotes(cls, notes, extra_classes=[]):
        classes = ["usage_footnote"]
        if len(notes) == 1:
            classes.append("solo_footnote")
        c = " ".join(classes + extra_classes)
        return cls.format_footnotes(notes, c, "1")

    @classmethod
    def format_ety_footnotes(cls, notes, extra_classes=[]):
        classes = ["ety_footnote"]
        if len(notes) == 1:
            classes.append("solo_footnote")
        c = " ".join(classes + extra_classes)
        return cls.format_footnotes(notes, c, "a")

    @classmethod
    def format_footnotes(cls, notes, note_class, start_char):
        res = []

        for idx,note in enumerate(notes):
            anchor = chr(ord(start_char)+idx)
            res.append(f'<span id="footnote_{anchor}" class="footnote {note_class}"><span class="footnote_id">{anchor}</span><span class="footnote_data">' + re.sub(r"\\n", "<br>", note) + '</span></span>\n')

        return res

    @classmethod
    def format_sense(cls, sense, pos, noun_type, ety_key, usage_key, primary_pos, hint=False):
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
            res.append(f'<span class="synonyms">{", ".join(sense["syns"])}</span>')

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


    def get_feminine_noun(self, word):
        for word_obj in self._words.get_words(word, "n"):
            if "f" in word_obj.forms:
                return word_obj.forms["f"][0]

            # Only look at the first word
            return None

        return None

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
            new = gloss[:break_pos].strip()
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

        for sense in pos_data["senses"]:
            if sense in short_senses:
                hint = self.shorten_gloss(self.obscure_gloss(sense["gloss"], hide_word), max_length)
                if hint == sense["gloss"]:
                    hint = ""
                sense["hint"] = hint

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

        def get_verb_type_and_tag(sense):
            verb_types = {
                "transitive": "t",
                "reflexive": "r",
                "intransitive": "i",
                "pronominal": "p",
                "takes a reflexive pronoun": "p",
                "ambitransitive": "x",
            }

            if not sense.qualifier:
                return ["", ""]

            tag_items = []
            verb_type = []
            for tag in sense.qualifier.split(", "):
                if tag in verb_types:
                    verb_type.append(verb_types[tag])
                else:
                    tag_items.append(tag)
            pos = "".join(verb_type)
            tag = ", ".join(tag_items)

            return (pos, tag)

        def get_sense_data(word, pos_type, word_tag):

            senses = []
            for sense in word.senses:
                gloss = self.filter_gloss(word, sense)
                if not gloss:
                    continue

                if word.pos == "v":
                    sense_type, sense_tag = get_verb_type_and_tag(sense)
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

        def get_word_data(word, pos_type=None, sense_tag=None):
            senses = get_sense_data(word, pos_type, sense_tag)
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
                    mates = [ w for w in words if w.genders == mate ]
                    if not any(w for w in mates for s in w.senses if self.filter_gloss(w, s)):
                    #if not any(w for w in mates if any(self.get_filtered_senses(w))):
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

                                    data = get_word_data(w, noun_type, noun_tag)
                                    if not data:
                                        continue

                                    if not word_data:
                                        word_data = data
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
            self.synonyms[key] = synonyms
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

    def get_phrase(self, word, pos, noun_type, femnoun):
        voice = ""
        phrase = ""
        display = None

        if noun_type:
            if femnoun:
                voice = self._MALE1
                if femnoun in self.el_f_nouns:
                    phrase = f"el {femnoun}. el {word}"
                    display = f"el {femnoun}/el {word}"
                else:
                    phrase = f"la {femnoun}. el {word}"
                    display = f"la {femnoun}/el {word}"
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
            else:
                raise ValueError(f"Word {word} has unknown noun type {noun_type}")
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

        if not usage:
            raise ValueError("No usage data", spanish, pos)
        noun_type = usage[0]["words"][0]["noun_type"] if pos == "n" else ""

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

        seen_tag = "|".join(sorted(deck_syns) + sorted(defs))
        if seen_tag in self.seen_hints:
            eprint(f"Warning: {seen_tag} is used by {item_tag} and {self.seen_hints[seen_tag]}, adding syn")
            deck_syns.insert(0, self.seen_hints[seen_tag].split(":")[1])
        else:
            self.seen_hints[seen_tag] = item_tag

        femnoun = self.get_feminine_noun(spanish) if pos == "n" else None
        tts_data = self.get_phrase(spanish, pos, noun_type, femnoun)

        sound = get_speech(tts_data["voice"], tts_data["phrase"], mediadir)

        all_usage_pos = {w["pos"] for ety in usage for w in ety["words"]}
        lookups = [[spanish, pos] for pos in all_usage_pos]
        sentences = self.get_sentences(lookups, 3)

        self.store_sentences(lookups)

        item = {
            "Spanish": spanish,
            "Part of Speech": noun_type if pos == "n" else pos,
            "Synonyms": self.format_syns(deck_syns, extra_syns, hide_word=spanish),
            "Data": self.format_usage(usage).replace("\n+", "\n<br>"),
            "Sentences": sentences,
            "Display": tts_data["display"],
            "Audio": self.format_sound(sound),
            "guid": genanki.guid_for(item_tag, "Jeff's Spanish Deck"),
        }

        tags = [noun_type if pos == "n" else pos]
        #    if "tags" in row and row['tags'] != "":
        #        for tag in row['tags'].split(" "):
        #            tags.append(tag)
        item["tags"] = tags

        FILE = os.path.join(mediadir, sound)
        if os.path.isfile(FILE):
            self.media_files.append(FILE)
        else:
            item["Sound"] = ""

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

        # read through all the files to populate the synonyms and excludes lists
        for wordlist in wordlists:
            with open(wordlist, newline="") as csvfile:
                csvreader = csv.DictReader(csvfile)
                for reqfield in ["pos", "spanish"]:
                    if reqfield not in csvreader.fieldnames:
                        raise ValueError(
                            f"No '{reqfield}' field specified in file {wordlist}"
                        )

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

                    # a digit in the position column indicates that it should be inserted at that position
                    elif int(position) > 0 and int(position) < len(self.allwords_index):
                        self.wordlist_insert(item_tag, int(position), usage)

                    else:
                        raise ValueError(f"Position {position} does not exist, ignoring")

            if len(self.allwords_index) != len(self.allwords):
                raise ValueError("Mismatch", len(self.allwords_index), len(self.allwords), wordlist)

    def compile(self, infofile, deckname, mediadir, limit, ankideck=None, tags=[]):

        with open(infofile) as jsonfile:
            self.deck_info = json.load(jsonfile)

        self.ankideck = ankideck
        if ankideck:
            ankidb = os.path.join(
                os.path.expanduser("~"), ".local/share/Anki2", ankideck, "collection.anki2"
            )
            if not os.path.isfile(ankidb):
                print("Cannot find anki database:", ankidb)
                exit(1)

            self.db_notes = self.load_db_notes(ankidb, self.deck_info["deck"]["name"])
            for guid, item in self.db_notes.items():
                hashval = self.get_note_hash(guid, item["flds"], item["tags"])
                self.db_timestamps[hashval] = item["mod"]

        card_model = self.make_card_model(self.deck_info["model"])
        deck_guid = self.deck_info["deck"]["id"]
        my_deck = genanki.Deck(
            int(deck_guid), self.deck_info["deck"]["name"], self.deck_info["deck"]["desc"]
        )

        if limit and limit < len(self.allwords_index):
            for tag in self.allwords_index[limit:]:
                del self.allwords[tag]
            self.allwords_index = self.allwords_index[:limit]


        self.build_synonyms()

        self.rows = []

        position = 0
        for wordtag in self.allwords_index:
            word, pos = split_tag(wordtag)

            position += 1

            item = self.build_item(word, pos, mediadir)
            self.notes[item["guid"]] = item
            item["Rank"] = str(position)
            item["tags"] += tags
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
            self.rows.append(row)

        package_filename = os.path.join(os.getcwd(), deckname + ".apkg")
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
    parser.add_argument("deckname", help="Name of deck to build")
    parser.add_argument(
        "-m",
        "--mediadir",
        help="Directory containing deck media resources (default: DECKNAME.media)",
    )
    parser.add_argument(
        "-w",
        "--wordlist",
        action="append",
        help="List of words to include/exclude from the deck (default: DECKNAME.csv)",
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
        help="CSV file with short definitions (default DECKNAME.shortdefs)",
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
    parser.add_argument(
        "--deckinfo",
        help="Read model/deck info from JSON file (default: DECKNAME.json)",
    )
    parser.add_argument("--anki", help="Read/write data from specified anki profile")
    parser.add_argument( "--allforms", help="Load word forms from file")
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
        args.mediadir = args.deckname + ".media"

    if not args.wordlist:
        args.wordlist = [args.deckname + ".csv"]

    if not args.short_defs and os.path.isfile(args.deckname + ".shortdefs"):
        args.short_defs = args.deckname + ".shortdefs"

    if not args.allow_flag:
        args.allow_flag = set()

    if not os.path.isdir(args.mediadir):
        print(f"Deck directory does not exist: {args.mediadir}")
        exit(1)

    for wordlist in args.wordlist:
        if not os.path.isfile(wordlist):
            print(f"Wordlist file does not exist: {wordlist}")
            exit(1)

    if args.dump_changes and not args.anki:
        print("Use of --dump-changes requires --anki profile to be specified")
        exit(1)

    if not args.deckinfo:
        args.deckinfo = args.deckname + ".json"

    if not os.path.isfile(args.deckinfo):
        print(f"Model JSON does not exist: {args.deckinfo}")
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
    deck.compile(args.deckinfo, args.deckname, args.mediadir, args.limit, args.anki, args.tag)

    if args.dump_sentence_ids:
        deck.dump_sentences(args.dump_sentence_ids)

    if args.dump_notes:
        with open(args.dump_notes, "w", newline="") as outfile:
            csvwriter = csv.writer(outfile)

            fields = deck._fields
            del fields[7]  # audio
            del fields[0]  # rank
            csvwriter.writerow(fields)

            for row in deck.rows:
                del row[7]
                del row[0]
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
