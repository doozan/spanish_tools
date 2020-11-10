#!/usr/bin/python3
# -*- python-mode -*-

import argparse
import csv
import genanki
import json
import math
import os
import re
import sqlite3
import sys

import spanish_sentences
import spanish_speech
from enwiktionary_wordlist.wordlist import Wordlist, Word

def make_tag(word, pos):
    if not pos:
        return word.lower()

    return pos.lower() + ":" + word.lower()

def split_tag(wordtag):
    pos, junk, word = wordtag.partition(":")
    return [word, pos.lower()]

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def fail(*args, **kwargs):
    eprint(*args, **kwargs)
    exit(1)


class MyNote(genanki.Note):
    def write_card_to_db(self, cursor, now_ts, deck_id, note_id, order, due):
        queue = 0
        cursor.execute(
            "INSERT INTO cards VALUES(null,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);",
            (
                note_id,  # nid
                deck_id,  # did
                order,  # ord
                now_ts,  # mod
                -1,  # usn
                0,  # type (=0 for non-Cloze)
                queue,  # queue
                due,  # due
                0,  # ivl
                0,  # factor
                0,  # reps
                0,  # lapses
                0,  # left
                0,  # odue
                0,  # odid
                0,  # flags
                "",  # data
            ),
        )

    def write_to_db(self, cursor, now_ts, deck_id):

        # Preserve the timestamp if it has been specified
        if self.mod_ts:
            now_ts = self.mod_ts

        cursor.execute(
            "INSERT INTO notes VALUES(null,?,?,?,?,?,?,?,?,?,?);",
            (
                self.guid,  # guid
                self.model.model_id,  # mid
                now_ts,  # mod
                -1,  # usn
                self._format_tags(),  # TODO tags
                self._format_fields(),  # flds
                self.sort_field,  # sfld
                0,  # csum, can be ignored
                0,  # flags
                "",  # data
            ),
        )

        note_id = cursor.lastrowid

        count = 0
        for card in self.cards:
            self.write_card_to_db(cursor, now_ts, deck_id, note_id, count, self._order)
            count += 1

class DeckBuilder():

    _fields = [
        "Rank",
        "Spanish",
        "Part of Speech",
        "Synonyms",
        "ShortDef",
        "Definition",
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

    _words = None
    _ignore = {}
    _sentences = None

    db_notes = {}
    db_timestamps = {}

    allwords = []
    allwords_set = set()
    allwords_positions = {}
    shortdefs = {}

    media_files = []

    rows = []

    el_f_nouns = [ 'abra', 'acta', 'agua', 'ala', 'alba', 'alma', 'ama', 'ancla', 'ansia',
        'area', 'arma', 'arpa', 'asma', 'aula', 'ave', 'habla', 'hada', 'hacha', 'hambre',
        'águila']

    credits = {}
    dumpable_sentences = {}
    deck_guids = set()
    seen_guids = {}
    seen_clues = {}

    def __init__(self, dictionary, ignore, sentences, shortdefs):

        self._words = dictionary
        if ignore:
            self._ignore = ignore
        self._sentences = sentences
        self._shortdefs = shortdefs


    def filter_gloss(self, word, pos, note, gloss):
        """ Returns True if the item matches an entry in the ignore list """

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

        gloss = re.sub(r'[;:,.]?\s*(feminine|female equivalent) of "[^\"]+"[ :,.]*', '', gloss)
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
        return "<br>\n".join(
            f'<span class="spa">{item[0]}</span><br>\n<span class="eng">{item[1]}</span>'
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
        with open(filename, "w") as outfile:
            print(f"dumping {filename}")
            for tag, ids in sorted(self.dumpable_sentences.items()):
                word, pos = split_tag(tag)
                row = [word, pos] + ids

                outfile.write(",".join(row))
                outfile.write("\n")


    @staticmethod
    def format_sound(filename):
        if not filename:
            return ""
        return f"[sound:{filename}]"


    @staticmethod
    def format_image(filename):
        if not filename:
            return ""
        return f'<img src="{filename}" />'


    @staticmethod
    def format_syns(deck, extra):
        deck_str = (
            f"""<span class="syn deck">{", ".join(deck)}</span>""" if len(deck) else ""
        )
        separator = ", " if len(deck_str) else ""
        extra_str = (
            f"""<span class="syn extra">{separator}{", ".join(extra)}</span>"""
            if len(extra)
            else ""
        )
        return deck_str + extra_str


    @classmethod
    def format_def(cls, item, hide_word=None):

        results = []
        multi_pos = len(item) > 1

        prev_display_pos = None
        for pos, tags in item.items():
            if not pos:
                print(item)
                raise ValueError("xx")

            common_pos = Word.get_common_pos(pos)
            safe_pos = pos.replace("/", "_")

            # Don't prefix the def with the part of speech if there's only one pos
            # for this entry (unless it's a verb with type of usage specified)
            if not prev_display_pos and len(item) == 1:
                prev_display_pos = "{v}" if common_pos == "verb" else f"{{{pos}}}"

            for tag, usage in tags.items():
                if len(results):
                    results.append("\n")

                classes = ["pos", common_pos]
                if common_pos != safe_pos:
                    classes.append(safe_pos)

                display_pos = f"{{{pos}}}"
                display_tag = tag

                # Only m/f and m-f nouns will have special pos in the tags
                if common_pos == "noun" and pos in ["m-f", "m/f"]:
                    tag_pos, sep, other_tags = tag.partition(" ")
                    tag_pos = tag_pos.replace(",", "")
                    if tag_pos in ["m", "f", "mf"]:
                        display_tag = other_tags
                    else:
                        tag_pos = "mf"

                    classes.append(tag_pos)
                    display_pos = f"{{{tag_pos}}}"

                elif common_pos == "verb" and ("r" in pos or "p" in pos):
                    classes.append("reflexive")

                if prev_display_pos == display_pos:
                    display_pos = ""
                else:
                    prev_display_pos = display_pos

                classes += sorted(cls.get_location_classes(tag))
                results.append(f'<span class="{" ".join(classes)}">{display_pos} ')

                usage = "; ".join(item[pos][tag])

                if hide_word:
                    new_usage = re.sub(
                        r'(apocopic form|diminutive|ellipsis|clipping|superlative) of ".*?"',
                        r"\1 of ...",
                        usage,
                    ).strip()

                    if (
                        new_usage != usage
                        and len(item.keys()) == 1
                        and len(item[pos].keys()) == 1
                        and "," not in usage
                        and ";" not in usage
                        and "(" not in usage
                        and ":" not in usage
                    ):
                        eprint(
                            f"Warning: obscured definition: ({usage}) may be completely obscured"
                        )

                    usage = new_usage

                if display_tag != "":
                    results.append(f'<span class="tag">[{display_tag}]:</span>')

                results.append(f'<span class="usage">{usage}</span>')

                results.append("</span>")

        return "".join(results)




    def validate_note(self, item):

        if item["guid"] in self.seen_guids:
            eprint(f"Duplicate guid from {item}")
        else:
            self.seen_guids[item["guid"]] = 1

        for key in ["Spanish", "Definition", "Part of Speech", "Audio"]:
            if item[key] == "":
                eprint(f"Missing {key} from {item}")
                return False

        return True


    def get_feminine_noun(self, word):
        for word_obj in self._words.all_words.get(word,{}).get("noun", []):
            if "f" in word_obj.forms:
                return word_obj.forms["f"][0]

            # Only look at the first word
            return None

        return None

    def get_pos_usage(self, word, common_pos):
        defs = {}

        for word_obj in self._words.all_words.get(word,{}).get(common_pos, []):
            pos = word_obj.pos

            if not pos:
                continue
            if pos not in defs:
                defs[pos] = {}

            for sense in word_obj.senses:
                tag = sense.qualifier

                gloss = self.filter_gloss(word, pos, tag, sense.gloss)
                if not gloss:
                    continue

                if tag not in defs[pos]:
                    defs[pos][tag] = [gloss]
                else:
                    defs[pos][tag].append(gloss)

            # If all defs were ignored, drop the pos
            if defs[pos] == {}:
                del defs[pos]

        return defs

    @staticmethod
    def def_len(defs):
        return sum(
            len(pos) + len(tag) + len("; ".join(values))
            for pos,tags in defs.items()
            for tag,values in tags.items()
            )


    @classmethod
    def shorten_defs(cls, defs, max_len=60, only_first_def=False):
        """
        Get a shorter definition having less than max_len characters

        Definitions separated by commas are assumed to be synonyms, while semicolons
        separate distinct usage.  Synonyms may be dropped to save space

        Return up to two distinct usages from the given definitions

        For nouns with male/female parts, try to include a definition for each gender

        For verbs with reflexive/non-reflexive, try to include a definition for each use

        If there are tagged/untagged uses, try to include the untagged and the first tagged usage

        Otherwise, try to include the first two distinct uses
        """

        first_pos = next(iter(defs))

        shortdefs = {}

        if first_pos in ["m-f", "mf", "m/f"]:
            pos = first_pos
            shortdefs[pos] = {}
            for tag,values in defs[pos].items():
                for gender in ['m', 'f']:
                    if tag.startswith(gender) and not any( x.startswith(gender) for x in shortdefs[pos] ):
                        shortdefs[pos][tag] = values

            if not len(shortdefs[pos]):
                tag = next(iter(defs[pos]))
                shortdefs[pos][tag] = defs[pos][tag]

        elif first_pos.startswith("v"):
            for pos,tags in defs.items():
                if not pos.startswith("v"):
                    continue

                if len(shortdefs) and only_first_def:
                    break

                # Always take the first verb def, then check each pronomial or reflexive def
                if len(shortdefs) and "p" not in pos and "r" not in pos:
                    continue

                # Limit to two defs (first + pronom or reflexive)
                if len(shortdefs)>=2:
                    break

                # Use the first definition
                for tag,values in tags.items():
                    shortdefs[pos] = { tag: values }
                    break

                ## Take the untagged value, no matter the order
                #for tag,value in tags.items():
                #    if shortdefs[pos] == {} or tag == "":
                #        shortdefs[pos] = { tag: value }

        else:
            pos = first_pos
            tags = defs[pos]
            shortdefs[pos] = {}

            # Use the first definition
            for tag,values in tags.items():
                shortdefs[pos] = { tag: values }
                break

        # If there's only one usage, try to take two definitions from it
        pos = next(iter(shortdefs))
        if not only_first_def and len(shortdefs) == 1 and len(shortdefs[pos]) == 1:
            tag = next(iter(shortdefs[pos]))
            shortdefs[pos][tag] = [shortdefs[pos][tag][0]]
            if len(shortdefs[pos][tag])>1:
                shortdefs[pos][";"] = shortdefs[pos][tag][1:]

        # If there's one usage, and it doesn't contain mulitple defs
        # take the second tag of the first pos
        # or the first tag of the second pos
        if not only_first_def and len(shortdefs) == 1 and len(shortdefs[pos]) == 1:
            if len(defs[pos]) > 1:
                next_tag = list(defs[pos].keys())[1]
                shortdefs[pos][next_tag] = defs[pos][next_tag]
            elif len(defs) > 1:
                next_pos = list(defs.keys())[1]
                tag = next(iter(defs[next_pos]))
                shortdefs[next_pos] = { tag: defs[next_pos][tag] }

        # Always include interjection definitions
        if "interj" in defs and pos != "interj":
            pos = "interj"
            tags = defs[pos]
            shortdefs[pos] = {}

            # Use the first definition
            for tag,values in tags.items():
                shortdefs[pos] = { tag: values }
                break

        # Split and shorten until short enough
        for separator in [ ';', '(', '[' ]:
            for pos,tags in shortdefs.items():
                for tag,values in tags.items():
                    value = "; ".join(values)
                    value = value.partition(separator)[0].strip()
                    shortdefs[pos][tag] = [value]

            if cls.def_len(shortdefs) <= max_len:
                break

        # If it's still too long, strip the last , until less than max length or no more , to strip
        can_strip=True
        while can_strip and cls.def_len(shortdefs) > max_len:
            can_strip=False
            for pos,tags in shortdefs.items():
                for tag,values in tags.items():
                    value = "; ".join(values)
                    strip_pos = value.rfind(",")
                    if strip_pos > 0:
                        can_strip=True
                        shortdefs[pos][tag] = [value[:strip_pos].strip()]
                        if cls.def_len(shortdefs) <= max_len:
                            break

        if only_first_def:
            return shortdefs

        # Rejoin any defs that we split out, unless it's a dup or too long
        pos = next(iter(shortdefs))
        if ";" in shortdefs[pos]:
            tag = next(iter(shortdefs[pos]))

            # If the second def is the same as the first def, retry without splitting the def
            if shortdefs[pos][tag] == shortdefs[pos][';']:
                shortdefs = cls.shorten_defs(defs, max_len=max_len, only_first_def=True)
            else:
                otherdefs = shortdefs[pos].pop(';')
                shortdefs[pos][tag] += otherdefs

        # If it's too long, try with just one definition
        if cls.def_len(shortdefs) > max_len:
            shortdefs = cls.shorten_defs(defs, max_len=max_len, only_first_def=True)

        if cls.def_len(shortdefs) > max_len:
            print(f"Alert: Trouble shortening def: {shortdefs}", file=sys.stderr)

        return shortdefs


    def get_shortdef(self, word, primary_pos, max_length=None):
        item_tag = make_tag(word, primary_pos)
        if item_tag in self.shortdefs:
            return self.shortdefs[item_tag]
        return self.get_usage(word, primary_pos, False, max_length)


    def process_defs(self, word, alldefs):

        # If there are independent defs for masculine and feminine use,
        # tag it as m-f
        if len( {"m","f","mf"} & alldefs.keys() ) > 1:
            alldefs['m-f'] = {}
            for oldpos in ['f', 'mf', 'm']:
                if oldpos in alldefs:
                    for oldnote,use in alldefs[oldpos].items():
                        newnote = oldpos + ", " + oldnote if oldnote != "" else oldpos
                        alldefs['m-f'][newnote] = use
                    del alldefs[oldpos]

        # Tag f-el nouns
        elif "f" in alldefs and word in self.el_f_nouns:
            alldefs["f-el"] = alldefs.pop("f")

        # Check for feminine equivalent nouns and tag as m/f
        elif "m" in alldefs:

            # If this has a "-a" feminine counterpart, reclassify the "m" defs as "m/f"
            # and add any feminine definitions (ignoring the "feminine noun of xxx" def)
            femnoun = self.get_feminine_noun(word)
            if femnoun:
                femdefs = []
                if femnoun in self._words.all_words:
                    femdefs = self.get_pos_usage(femnoun, "noun")

                if len(femdefs) and 'f' in femdefs:
                    alldefs['f'] = femdefs['f']
                    alldefs['m/f'] = {}

                    for oldpos in ['f', 'm']:
                        for oldnote,defs in alldefs[oldpos].items():
                            newnote = oldpos + ", " + oldnote if oldnote != "" else oldpos
                            alldefs['m/f'][newnote] = defs
                        del alldefs[oldpos]

                else:
                    alldefs['m/f'] = alldefs.pop('m')

        return alldefs


    def get_usage(self, word, primary_pos, get_all_pos=True, max_length=None):

        defs = self.get_pos_usage(word, primary_pos)
        defs = self.process_defs(word, defs)

        if get_all_pos:

            all_pos = []
            forms = self._words.all_forms.get(word, [])
            for pos,lemma,formtype in [x.split(":") for x in sorted(forms)]:
                if pos not in all_pos:
                    all_pos.append(pos)

            for common_pos in all_pos:
                if common_pos not in [primary_pos, "verb"]:
                    lemmas = self.get_lemmas(word, common_pos)
                    defs.update(self.get_pos_usage(lemmas[0], common_pos))

        if max_length:
            defs = self.shorten_defs(defs, max_length)

        return defs

    def get_lemmas(self, word, pos):

        lemmas = []
        forms = self._words.all_forms.get(word, [])
        for form_pos,lemma,formtype in [x.split(":") for x in sorted(forms)]:
            if form_pos != pos:
                continue
            if lemma not in lemmas:
                lemmas.append(lemma)
        if not lemmas:
            return [word]

        # remove verb-se if verb is already in lemmas
        if pos == "verb":
            lemmas = [x for x in lemmas if not (x.endswith("se") and x[:-2] in lemmas)]

        # resolve lemmas that are "form of" other lemmas
        good_lemmas = set()
        for lemma in lemmas:
            for word_obj in self._words.get_words(lemma, pos):
                good_lemmas |= set(self._words.get_lemmas(word_obj).keys())

        return sorted(good_lemmas)

    def get_synonyms(self, word, pos, limit=5, only_in_deck=True):

        # TODO: Get reverse synonyms?

        items = []
        for word_obj in self._words.all_words[word][pos]:
            for sense in word_obj.senses:
                items += sense.synonyms

        if only_in_deck:
            return [k for k in items if make_tag(k, pos) in self.allwords_set][:limit]
        return list(items)[:limit]



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

        english = ""
        noun_type = ""

    #    if word.startswith("protector"):
    #        import pdb; pdb.set_trace()

        usage = self.get_usage(spanish, pos)
        if not usage:
            raise ValueError("No english", spanish, pos)
        if pos == "noun":
            noun_type = next(iter(usage))

        deck_syns = self.get_synonyms(spanish, pos, self.MAX_SYNONYMS, only_in_deck=True)
        extra_syns = (
            [
                k
                for k in self.get_synonyms(spanish, pos, self.MAX_SYNONYMS, only_in_deck=False)
                if k not in deck_syns
            ]
            if len(deck_syns) < self.MAX_SYNONYMS
            else []
        )

        english = self.format_def(usage)

        shortdef = self.get_shortdef(word, pos, max_length=60)
        short_english = self.format_def(shortdef, hide_word=word) if shortdef else ""

        defs = [
            value.strip()
            for tags in shortdef.values()
            for defs in tags.values()
            for d in defs
            for split_def in d.split(";")
            for value in split_def.split(",")
        ]
        seen_tag = "|".join(deck_syns + sorted(defs))
        if seen_tag in self.seen_clues:
            eprint(f"Warning: {seen_tag} is used by {item_tag} and {self.seen_clues[seen_tag]}, adding syn")
            deck_syns.insert(0, self.seen_clues[seen_tag])
        #        exit()
        else:
            self.seen_clues[seen_tag] = item_tag

        if short_english == english:
            short_english = ""

        femnoun = self.get_feminine_noun(spanish) if pos == "noun" else None
        tts_data = self.get_phrase(spanish, pos, noun_type, femnoun)

        sound = spanish_speech.get_speech(tts_data["voice"], tts_data["phrase"], mediadir)

        all_usage_pos = {Word.get_common_pos(k): 1 for k in usage.keys()}.keys()
        lookups = [[spanish, pos] for pos in all_usage_pos]
        sentences = self.get_sentences(lookups, 3)
        self.store_sentences(lookups)

        if pos == "part":
            pos = "past participle"

        item = {
            "Spanish": spanish,
            "Part of Speech": noun_type if pos == "noun" else pos,
            "Synonyms": self.format_syns(deck_syns, extra_syns),
            "ShortDef": short_english,
            "Definition": english,
            "Sentences": sentences,
            "Display": tts_data["display"],
            "Audio": self.format_sound(sound),
            "guid": genanki.guid_for(item_tag, "Jeff's Spanish Deck"),
        }

        tags = [noun_type if pos == "noun" else pos]
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
            return self.allwords.index(target)

        for index in range(len(self.allwords)):
            word, pos = split_tag(self.allwords[index])

            if word == target:
                return index


    def wordlist_insert_after(self, target, wordtag):
        index = self.wordlist_indexof(target)
        if not index:
            eprint(
                f"ERROR: {target} not found in wordlist, unable to insert {wordtag} after it"
            )
            return

        self.allwords.insert(index + 1, wordtag)
        self.allwords_set.add(wordtag)


    def wordlist_replace(self, old_tag, new_tag):

        index = self.wordlist_indexof(old_tag)
        if not index:
            eprint(
                f"ERROR: {old_tag} not found in wordlist, unable to replace with {new_tag}"
            )
            return

        old_tag = self.allwords[index]
        self.allwords_set.remove(old_tag)
        self.allwords_set.add(new_tag)

        self.allwords[index] = new_tag


    def wordlist_remove(self, wordtag):

        index = self.wordlist_indexof(wordtag)
        if not index:
            eprint(f"ERROR: {wordtag} not found in wordlist, unable to remove")
            return

        old_tag = self.allwords[index]
        self.allwords_set.remove(old_tag)
        del self.allwords[index]


    def wordlist_insert(self, wordtag, position):
        if wordtag in self.allwords_set:
            eprint(
                f"ERROR: {wordtag} already exists in wordlist, cannot insert at position {position}"
            )
            return

        # Note, don't actually insert the word at the specified position, because later wordlists
        # may delete items and rearrange the order.  Instead, add it to the bottom of the list and
        # save the desired position in allwords_positions, which will be used after the wordlist
        # is finished to position it absolutely

        self.allwords_set.add(wordtag)
        self.allwords.append(wordtag)
        self.allwords_positions[wordtag] = position


    def wordlist_append(self, wordtag):
        if wordtag in self.allwords_set:
            eprint(f"ERROR: {wordtag} already exists in wordlist, cannot be added again")
            return

        self.allwords.append(wordtag)
        self.allwords_set.add(wordtag)


    def load_wordlists(self, wordlists):

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

                    if "flags" in row and "CLEAR" not in row["flags"]:
                        continue

                    if not self.get_usage(row["spanish"], row["pos"]):
                        continue

                    item_tag = make_tag(row["spanish"], row["pos"])

                    position = row.get("position", None)
                    if not position:
                        self.wordlist_append(item_tag)

                    # +pos:word indicates that the entry should be positioned immedialy after the specified pos:word
                    # or after the first occurance of word if pos: is not specified
                    elif position.startswith("+"):
                        self.wordlist_insert_after(position[1:], item_tag)

                    # pos:word will replace the specific pos:word or the first occurance of the word if pos: is not specified
                    elif not position[0].isdigit() and position[0] != "-":
                        self.wordlist_replace(position, item_tag)

                    # Negative position indicates that all previous instances of this word should be removed
                    elif int(position) < 0:
                        self.wordlist_remove(item_tag)

                    # a digit in the position column indicates that it should be inserted at that position
                    elif int(position) > 0 and int(position) < len(self.allwords):
                        self.wordlist_insert(item_tag, int(position))

                    # otherwise put it at the end of the list
                    else:
                        raise ValueError("Position {position} does not exist, ignoring")

        # Arrange any items with absolute positions
        for wordtag, position in sorted(
            self.allwords_positions.items(), key=lambda item: item[1]
        ):
            index = self.wordlist_indexof(wordtag)
            if index != position:
                self.allwords.pop(index)
                self.allwords.insert(position - 1, wordtag)

            word, pos = split_tag(wordtag)
            print(
                f"Absolute position for {wordtag}, consider using relative: ~{self.allwords[position-2]},{word},{pos}",
                file=sys.stderr,
            )

    def compile(self, infofile, deckname, mediadir, limit, ankideck=None):

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

        if limit and limit < len(self.allwords):
            self.allwords = self.allwords[:limit]
            self.allwords_set = set(self.allwords)

        self.rows = []

        position = 0
        for wordtag in self.allwords:
            word, pos = split_tag(wordtag)

            position += 1
            item = self.build_item(word, pos, mediadir)
            item["Rank"] = str(position)
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
            )
            # preserve the mod timestamp if the note matches with the database
            note.mod_ts = self.get_mod_timestamp(note)
            if not note.mod_ts and self.ankideck and False:
                if item["guid"] not in self.db_notes:
                    print(f"added: {wordtag}")
                else:
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
                                else:
                                    print(f"{wordtag}  field {idx}: {old} => {new}")
                    else:
                        print(f"  old tags: {old_data['tags']}")
                        print(f"  new tags: {note._format_tags()}")

            self.deck_guids.add(item["guid"])

            note._order = position
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
    def load_dictionary(cls, filename):
        with open(filename) as infile:
            return cls.load_dictionary_data(infile)

    @staticmethod
    def load_dictionary_data(data):
        return Wordlist(data)

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


def main():

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
        help="List of words to include/exclude from the deck (default: DECKNAME.json",
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
        "--dump-removed", help="Dump list of removed note ids to file (requires --anki)"
    )
    parser.add_argument(
        "--deckinfo",
        help="Read model/deck info from JSON file (default: DECKNAME.json)",
    )
    parser.add_argument("--anki", help="Read/write data from specified anki profile")
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
    args = parser.parse_args()

    if not args.data_dir:
        args.data_dir = os.environ.get("SPANISH_DATA_DIR", "spanish_data")

    if not args.custom_dir:
        args.custom_dir = os.environ.get("SPANISH_CUSTOM_DIR", "spanish_custom")

    if not args.mediadir:
        args.mediadir = args.deckname + ".media"

    if not args.wordlist:
        args.wordlist = [args.deckname + ".csv"]

    if not args.short_defs:
        args.short_defs = args.deckname + ".shortdefs"

    if not os.path.isdir(args.mediadir):
        print(f"Deck directory does not exist: {args.mediadir}")
        exit(1)

    for wordlist in args.wordlist:
        if not os.path.isfile(wordlist):
            print(f"Wordlist file does not exist: {wordlist}")
            exit(1)

    if not os.path.isfile(args.short_defs):
        print(f"Shortdefs file does not exist: {args.short_defs}")
        exit(1)

    if args.dump_removed and not args.anki:
        print("Use of --dump-removed requires --anki profile to be specified")
        exit(1)

    if not args.deckinfo:
        args.deckinfo = args.deckname + ".json"

    if not os.path.isfile(args.deckinfo):
        print(f"Model JSON does not exist: {args.deckinfo}")
        exit(1)

    dictionary = DeckBuilder.load_dictionary(args.dictionary)
    ignore = DeckBuilder.load_ignore(args.dictionary_custom)

    sentences = spanish_sentences.sentences(
        sentences=args.sentences, data_dir=args.data_dir, custom_dir=args.custom_dir
    )
    shortdefs = DeckBuilder.load_shortdefs(args.short_defs)

    deck = DeckBuilder(dictionary, ignore, sentences, shortdefs)
    deck.load_wordlists(args.wordlist)
    deck.compile(args.deckinfo, args.deckname, args.mediadir, args.limit, args.anki)

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

    if args.dump_removed:
        with open(args.dump_removed, "w") as outfile:
            for guid in deck.db_notes.keys() - deck.deck_guids:
                outfile.write(f'{deck.db_notes[guid]["nid"]} {deck.db_notes[guid]["word"]}\n')

    if args.dump_credits:
        deck.dump_credits(args.dump_credits)




if __name__ == "__main__":
    main()
