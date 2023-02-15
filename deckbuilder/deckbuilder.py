#!/usr/bin/python3
# -*- python-mode -*-

import csv
import genanki
import html
import json
import math
import os
import re
import sqlite3
import sys

from .hider import Hider
from .tts import get_speech
from .sentences import SentenceSelector
from spanish_tools.sentences import SpanishSentences

from collections import defaultdict

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

    # _FEMALE1 = "Lupe"
    _FEMALE1 = "Penelope"
    _FEMALE2 = "Penelope"
    _MALE1 = "Miguel"

    el_f_nouns = [ 'abra', 'acta', 'afta', 'ágora', 'agua', 'águila', 'ala', 'alba', 'alca',
            'álgebra', 'alma', 'alta', 'alza', 'ama', 'ancla', 'áncora', 'ánima', 'ansia',
            'app', 'arca', 'área', 'arma', 'arpa', 'asa', 'asma', 'aspa', 'asta', 'aula',
            'aura', 'ave', 'haba', 'habla', 'hacha', 'hada', 'hambre', 'haya' ]

    def __init__(self, wordlist, sentences, ignore, allforms, shortdefs, ngprobs, allow=None):

        self.db_notes = {}
        self.db_timestamps = {}

        self.allwords = {}
        self.allwords_index = []
        self.allwords_meta = {}
        self.shortdefs = {}

        self.media_files = []

        self.rows = []

        self.notes = {}
        self.seen_guids = {}
        self.seen_hints = defaultdict(list)

        self._words = wordlist
        self._ignore = ignore
        self._sentences = sentences
        self._shortdefs = shortdefs
        self.all_forms = allforms
        self.ngprobs = ngprobs
        self.allow = allow

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
    def format_sound(filename):
        if not filename:
            return ""
        return f"[sound:{filename}]"

    @classmethod
    def format_syns_html(cls, deck, extra, css_class=''):

        valid_deck_syns = cls.get_valid_syns(deck, [])
        valid_extra_syns = cls.get_valid_syns(extra, deck)

        if css_class and not css_class.endswith(' '):
            css_class += ' '

        deck_str = (
            f"""<span class="{css_class}syn deck">{", ".join(valid_deck_syns)}</span>""" if valid_deck_syns else ""
        )
        if not valid_extra_syns:
            return deck_str

        separator = ", " if len(deck_str) else ""
        extra_str = f"""<span class="{css_class}syn extra">{separator}{", ".join(valid_extra_syns)}</span>"""

        return deck_str + extra_str

    @classmethod
    def format_syns(cls, deck, extra, hide_words=[]):
        obscured_deck = [Hider.obscure(syn, hide_words) for syn in deck]
        obscured_extra = [Hider.obscure(syn, hide_words) for syn in extra]

        has_obscured = False

        if obscured_deck != deck:
            has_obscured = True
            obscured_deck = [x for x in obscured_deck if "..." not in x] + ["..."]

        if obscured_extra != extra:
            has_obscured = True
            obscured_extra = [x for x in obscured_extra if "..." not in x] + ["..."]

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

        if tags and sense.get("hint") != "...":
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


    def get_noun_gender(self, word_obj):
        if not word_obj.genders:
            return "n"

        noun_type = word_obj.genders.replace("-p", "p").replace("-f", "f")
        if noun_type == "mfbysense":
            noun_type = "mf"
        elif noun_type == "m; f":
            noun_type = "mf"
        elif noun_type in ["mfbysensep", "mp; fp"]:
            noun_type = "mfp"
        elif noun_type not in ["m", "f", "mf", "mp", "fp", "mfp"]:
            raise ValueError("Unexpected noun type", word_obj.word, noun_type)

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

        def sense_is_reflexive(sense_data):
            return any(x in sense_data.get("type","") for x in ["r","p"])

        def sense_is_plural(sense_data):
            return "plural" in sense_data.get("tag","")

        def sense_is_obsolete(sense_data):
            return any(x in sense_data.get("tag","") for x in ["obsolete", "archaic"])

        if not usage:
            return

        glosses = {}

        pos_data = usage[0]["words"][0]

        # Skip obsolete or archaic senses
        for first_sense, sense in enumerate(pos_data["senses"]):
            if not sense_is_obsolete(sense):
                break

        # If all senses were obsolete, revert to the first sense
        if sense_is_obsolete(pos_data["senses"][first_sense]):
            first_sense = 0

        sense = pos_data["senses"][first_sense]
        sense["can_hide_all"] = False
        short_senses = [ sense ]

        # If a noun has male/female words, try to take a gloss from each
        if pos_data["pos"] == "n" and pos_data.get("noun_type") in ["m-f","m/f"]:
            for sense in pos_data["senses"][first_sense+1:]:
                if sense.get("type") != short_senses[0].get("type") and not sense_is_obsolete(sense):
                    sense["can_hide_all"] = True
                    short_senses.append(sense)
                    break

        elif pos_data["pos"] == "n" and not sense_is_plural(short_senses[0]):
            for sense in pos_data["senses"][first_sense+1:]:
                if sense_is_plural(sense) and not sense_is_obsolete(sense):
                    sense["can_hide_all"] = False
                    short_senses.append(sense)
                    break

        # If it's a verb and the first sense is not reflexive, search for a sense that is reflexive
        elif pos_data["pos"] == "v" and not sense_is_reflexive(short_senses[0]):
            for sense in pos_data["senses"][first_sense+1:]:
                if sense_is_reflexive(sense) and not sense_is_obsolete(sense):
                    sense["can_hide_all"] = False
                    short_senses.append(sense)
                    break

        if len(short_senses) == 1 and len(pos_data["senses"]) > first_sense+1:
            for sense in pos_data["senses"][first_sense+1:]:
                if not sense_is_obsolete(sense):
                    sense["can_hide_all"] = True
                    short_senses.append(sense)
                    break

        # TODO: Include all POS for multi-word lemmas

        # use feminine forms for hiding for m/f nouns
        if pos_data["pos"] == "n" and pos_data.get("noun_type") == "m/f":
            hide_words = [hide_word] + self.get_feminine_forms(hide_word)
        else:
            hide_words = [hide_word]

        self.add_sense_hints(short_senses, hide_words, max_length)

    @classmethod
    def add_sense_hints(cls, senses, hide_words, max_length):
        skip_hiding = False
        for sense in senses:
            can_hide_all = sense["can_hide_all"]

            if skip_hiding:
                hint = sense["gloss"]
            else:
                hint = Hider.obscure(sense["gloss"], hide_words)

            hint = cls.shorten_gloss(hint, max_length)
            if Hider.is_fully_hidden(hint):
                if not can_hide_all:
                    hint = cls.shorten_gloss(sense["gloss"], max_length)
                    skip_hiding = True

            sense["hint"] = hint if hint != sense["gloss"] else ""

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

            return self.get_noun_gender(word)

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

        poslemmas = self.all_forms.get_lemmas(word, pos)
        lemmas = [x.split("|")[1] for x in sorted(poslemmas)] if poslemmas else [word]

        # remove verb-se if verb is already in lemmas
        if pos == "v":
            lemmas = [x for x in lemmas if not (x.endswith("se") and x[:-2] in lemmas)]

        return lemmas

        # resolve lemmas that are "form of" other lemmas
#        good_lemmas = set()
#        for lemma in lemmas:
#            for word_obj in self._words.get_words(lemma, pos):
#                for maybe_lemma in self._words.get_words(word_obj.word, word_obj.pos)
#                good_lemmas |= { 
#
#                good_lemmas |= set(self._words.get_lemmas(word_obj).keys())
#
#        return sorted(good_lemmas)


    def add_synonyms(self, word, pos, synonyms):
        key = (word,pos)

        for syn in synonyms:
            if syn == word:
                continue

            if syn not in self.synonyms[key]:
                self.synonyms[key].append(syn)

            # add reciprocal synonym
            r_key = (syn,pos)
            if word not in self.synonyms[r_key]:
                self.synonyms[r_key].append(word)


    def build_synonyms(self):
        self.synonyms = defaultdict(list)
        defs_to_syns = defaultdict(list)

        # Build synonyms
        for item_tag,usage in self.allwords.items():
            word, pos = split_tag(item_tag)

            # Only the first word in the first entymology has senses with hints/synonyms
            word_data = usage[0]["words"][0]
            defs = set()
            for sense in word_data["senses"]:
                if "hint" in sense:
                    print("scanning", sense)

                    # Create list of words that list other words as a synonyms to create
                    # the reciprocal synonym
                    if "syns" in sense:
                        self.add_synonyms(word, pos, sense["syns"])


                    # Build list of displayed glosses to generate auto synonyms for
                    # words with identical glosses
                    gloss = sense["hint"] if sense["hint"] else sense["gloss"]

                    # Strip leading [lables]
                    gloss = re.sub(r"^\[.+?\][:,; ]*", "", gloss)
                    for item in re.split("[;,]", gloss):
                        item = item.strip()
                        if item != "...":
                            defs.add(item)

            if not defs:
                raise ValueError("no defs", item_tag, usage)
            defs_to_syns[tuple([pos] + sorted(defs))].append(item_tag)

        self.auto_syns = {}
        for pos_defs, items in defs_to_syns.items():
            if len(items) < 2:
                continue

            for item_tag in items:
                if item_tag in self.auto_syns:
                    raise ValueError("dup item in auto syns", item_tag, defs, items)

                self.auto_syns[item_tag] = [x for x in items if x != item_tag]


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

        pos = usage[0]["words"][0]["pos"]

        if pos == "n":
            return self.get_noun_phrase(word, usage)
#            old = self.get_noun_phrase_old(word, usage)
#            if old != new:
#                print("XXXX", old, "->", new)

        elif pos == "v":
            return self.get_verb_phrase(word, usage)

        else:
            return { "voice": self._FEMALE1, "phrase": word, "display": word }


    def get_verb_phrase(self, word, usage):
        phrase = word
        display = word

        if " " not in word \
            and word[-2:] in ["ar", "er", "ir", "ír"] \
            and self.verb_has_reflexive(usage):
                phrase = f"{word}. {word}se"
                display = f"{word}/{word}se"

        return { "voice": self._FEMALE1, "phrase": phrase, "display": display }

    def get_feminine_forms(self, word):
        for word_obj in self._words.get_words(word, "n"):
            # Return inside loop intentional, we only want to process the first word
            return word_obj.forms.get("f")

    def get_plurals(self, word):
        plurals = []
        for word in self._words.get_words(word, "n"):
            for pl in word.forms.get("pl", []):
                if pl not in plurals:
                    plurals.append(pl)
        return plurals

    def get_usually_plural(self, word):
        for plural in self.get_plurals(word):
            if self.ngprobs.get_usage_count(plural, "n") > self.ngprobs.get_usage_count(word, "n"):
                return plural

    def has_any_plural_gloss(self, usage):
        for word in usage[0]["words"]:
            if word["pos"] != "n":
                continue
            return any("plural" in sense.get("tag", "") for sense in word["senses"])

    def has_all_plural_gloss(self, usage):
        for word in usage[0]["words"]:
            if word["pos"] != "n":
                continue
            return all("plural" in sense.get("tag", "") for sense in word["senses"])

    def include_plural_form(self, word, gender, usage):
        # formats a noun with an article, includes the plural form if usually plural

        if gender == "f":
            art = "el" if word.split()[0] in self.el_f_nouns else "la"
            pl_art = "las"
        else:
            art = "el"
            pl_art = "los"

        # If it's usually plural, put the plural first
        pl_word = self.get_usually_plural(word)
        if pl_word:
            if self.has_all_plural_gloss(usage):
                return [f"{pl_art} {pl_word}"]
            else:
                return [f"{pl_art} {pl_word}", f"{art} {word}"]

        # If it has a plural-only sense, include the plural
        if self.has_any_plural_gloss(usage):
            plurals = self.get_plurals(word)
            if plurals:
                pl_word = plurals[0]
                return [f"{art} {word}", f"{pl_art} {pl_word}"]

        return [f"{art} {word}"]

    def get_noun_phrase(self, word, usage):
        voice = ""
        phrase = ""
        display = None

        items = []

        noun_type = self.get_noun_type(usage)

        femforms = self.get_feminine_forms(word)
        if femforms:
            voice = self._MALE1

            items = [f"el {f}" if f.split()[0] in self.el_f_nouns else f"la {f}" for f in femforms]
            items.append(f"el {word}")
            phrase = ". ".join(items)
            display = "/".join(items)

        elif noun_type == "f-el":
            voice = self._FEMALE2
            items = self.include_plural_form(word, "f", usage)
            phrase = ". ".join(items)
            display = "/".join(items)
        elif noun_type == "f":
            voice = self._FEMALE2
            items = self.include_plural_form(word, "f", usage)
            phrase = ". ".join(items)
            display = "/".join(items)
        elif noun_type == "fp":
            voice = self._FEMALE2
            phrase = f"las {word}"
            display = phrase
        elif noun_type == "m-f":
            voice = self._FEMALE1
            phrase = f"la {word}. el {word}"
            display = f"la/el {word}"
        elif noun_type == "m":
            voice = self._MALE1
            items = self.include_plural_form(word, "m", usage)
            phrase = ". ".join(items)
            display = "/".join(items)
        elif noun_type == "mf":
            voice = self._MALE1
            phrase = f"el {word}. la {word}"
            display = f"el/la {word}"
        elif noun_type == "mfp":
            voice = self._MALE1
            phrase = f"los {word}. las {word}"
            display = f"los/las {word}"
        elif noun_type == "mp":
            voice = self._MALE1
            phrase = f"los {word}"
            display = phrase
        else:
            raise ValueError(f"Word {word} has unknown noun type {noun_type}")

        return { "voice": voice, "phrase": phrase, "display": display }


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

    @staticmethod
    def get_valid_syns(syns, existing_syns):
        valid_syns = []
        seen_syns = set()

        for syn in existing_syns:
            clean_syn = re.sub(r"\s*\(.*\)\s*", "", syn)
            seen_syns.add(clean_syn)

        for syn in syns:
            clean_syn = re.sub(r"\s*\(.*\)\s*", "", syn)

            if clean_syn not in seen_syns:
                valid_syns.append(syn)
                seen_syns.add(clean_syn)

        return valid_syns

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


        auto_syns = self.get_valid_syns([x.partition(":")[2] for x in self.auto_syns.get(item_tag,[])], deck_syns + extra_syns)
        if auto_syns:
            eprint(f"Auto-syn: {item_tag} display defs match other items, adding auto synonyms: {auto_syns}")
            deck_syns = auto_syns + deck_syns

        tts_data = self.get_phrase(spanish, usage)

        sound = get_speech(tts_data["voice"], tts_data["phrase"], mediadir)

        sentences = self._sentences.get_sentences(spanish, pos, 3)

        display_pos = self.get_noun_type(usage) if pos == "n" else pos

        item = {
            "Spanish": spanish,
            "Part of Speech": display_pos,
            "Synonyms": self.format_syns(deck_syns, extra_syns, hide_words=[spanish]),
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

            all_allowed_flags = allowed_flags.copy()
            limit = 0
            minuse = 0
            metadata = {}

            filename, *options = wordlist.split(";")
            for option in options:
                k,v = option.split("=")
                k = k.lower().strip()
                if k == "allow":
                    all_allowed_flags.append(v)
                elif k == "limit":
                    limit = int(v)
                elif k == "minuse":
                    minuse = int(v)
                elif k == "tag":
                    if "tags" not in metadata:
                        metadata["tags"] = [v]
                    else:
                        metadata["tags"].append(v)
                else:
                    raise ValueError(f'Unknown option "{option}" specified in wordlist {wordlist}')

            with open(filename, newline="") as csvfile:
                print("loading", filename, all_allowed_flags, limit, metadata, minuse)
                self.load_wordlist(csvfile, all_allowed_flags, limit, metadata, minuse)




    allowed_proper_nouns = { "Fulano", "Sudáfrica", "Sudamérica", "Centroamérica", "Renacimiento", "URSS",
            "América Latina", "Mediterráneo", "Atlántico", "Caribe", "OTAN", "Pacífico", "Oriente",
            "Estados Unidos", "Biblia", "Latinoamérica", "Norteamérica", "Navidad", "ONU", "fulana",
            "Nochebuena", "Dios", "Mesoamérica", "Pereira"}

    def is_allowed(self, word, pos):
        if pos != "prop":
            return True

        return word in self.allowed_proper_nouns

    @staticmethod
    def load_allow(filename):
        with open(filename) as data:
            allowed = set()
            csvreader = csv.DictReader(data)
            for reqfield in ["pos", "spanish"]:
                if reqfield not in csvreader.fieldnames:
                    raise ValueError(f"No '{reqfield}' field specified in wordlist")

            for row in csvreader:
                if not row:
                    continue

                pos = row["pos"]
                if pos == "none":
                    continue

                lemma = row["spanish"]

                allowed.add((lemma,pos))

        return allowed


    def load_wordlist(self, data, allowed_flags, limit=0, metadata=None, minuse=0):
        # data is an iterator that provides csv formatted data

        csvreader = csv.DictReader(data)
        for reqfield in ["pos", "spanish"]:
            if reqfield not in csvreader.fieldnames:
                raise ValueError(f"No '{reqfield}' field specified in wordlist")

        count = 0
        for row in csvreader:
            if not row:
                continue

            pos = row["pos"]
            if pos == "none":
                continue

            if minuse and minuse > int(row.get("count", 0)):
                continue

            lemma = row["spanish"]

            item_tag = make_tag(lemma, pos)

            position = row.get("position", None)

            # Negative position indicates that all previous instances of this word should be removed
            if position and position.startswith("-"):
                self.wordlist_remove(item_tag)
                continue

            if not self.is_allowed(lemma, pos):
                continue

            if "USELIST" in allowed_flags and (lemma, pos) not in self.allow:
                continue

            # Unless items without sentences are explicitly allowed, make sure word has sentences
            if "NOSENT" not in allowed_flags:
                sentences, source = self._sentences.sentences.get_sentences(lemma, pos)
                if not sentences:
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
        print(f"  loaded {count} items")


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

#        print("##"*30)
#        print("loaded", len(self.allwords_index), filename)
#        print("##"*30)
#        exit(1)

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
#            item["tags"].append(str(math.ceil(position / 500) * 500))

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

    @staticmethod
    def load_sentence_selector(sentences, preferred, forced, ignored, tagfixes):
        sentences = SpanishSentences(
            sentences=sentences,
            ignored=ignored,
            tagfixes=tagfixes,
        )

        return SentenceSelector(sentences, preferred, forced)

    def dump_sentences(self, filename):
        self._sentences.dump_sentences(filename)

