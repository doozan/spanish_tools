#!/usr/bin/python3
# -*- python-mode -*-

import argparse
import csv
import genanki
import json
import math
import os
import psutil
import re
import sqlite3
import subprocess
import sys
import time
import urllib.request

import spanish_sentences
import spanish_speech
from spanish_words import SpanishWords

# For the sentence arrays
IDX_SPANISH=0
IDX_ENGLISH=1
IDX_SCORE=2
IDX_SPAID=3
IDX_ENGID=4
IDX_SPAUSER=5
IDX_ENGUSER=6

_words = None
_sentences = None

db_notes = {}
db_timestamps = {}

allwords = []
allwords_set = set()
allwords_positions = {}
shortdefs = {}

media = []

args = None


def init_data(dictionary, sentences, data_dir, custom_dir):
    global _words
    global _sentences

    _words = SpanishWords(dictionary=dictionary, data_dir=data_dir, custom_dir=custom_dir)
    _sentences = spanish_sentences.sentences(sentences=sentences, data_dir=data_dir, custom_dir=custom_dir)

def load_db_notes(filename, deck_name):
    db = sqlite3.connect(filename)
    c = db.cursor()

    decks = json.loads(c.execute("SELECT decks FROM col").fetchone()[0])

    col_deck_guid=0
    for item,val in decks.items():
        if val['name'] == deck_name:
            col_deck_guid = val['id']
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
    for cid,nid,guid,mod,flds,tags in c.execute(query, (col_deck_guid,)).fetchall():

        fields = flds.split(chr(31))

        if guid in db_notes:
            db_notes[guid]['cards'].append(cid)
        else:
            db_notes[guid] = {'word': f"{fields[2]} {fields[1]}", 'cards': [ cid ], 'flds': flds, 'tags': tags, 'mod': mod, 'nid': nid}

    return db_notes


def make_card_model(data):
    return genanki.Model(data['id'],
        data['name'],
        fields=data['flds'],
        templates=data['tmpls'],
        css=data['css']
    )

def get_note_hash(guid,flds,tags):
    tags = " ".join(sorted(tags.strip().split(" ")))
    return hash(json.dumps([guid,flds,tags]))

def get_mod_timestamp(note):
    guid = note.guid
    flds = note._format_fields()
    tags = note._format_tags()

    hashval = get_note_hash(guid,flds,tags)
    return db_timestamps.get(hashval)

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def fail(*args, **kwargs):
    eprint(*args, **kwargs)
    exit(1)

def format_sentences(sentences):
    return "<br>\n".join( f'<span class="spa">{item[0]}</span><br>\n<span class="eng">{item[1]}</span>' for item in sentences )


def get_sentences(items, count):

    results = _sentences.get_sentences(items, count)
    save_credits(results)

    if len(results['sentences']):
        return format_sentences(results['sentences'])

    return ""

credits = {}
def save_credits(results):
    if not args.dump_credits:
        return

    for sentence in results['sentences']:
        spa_user = sentence[IDX_SPAUSER]
        eng_user = sentence[IDX_ENGUSER]
        spa_id = sentence[IDX_SPAID]
        eng_id = sentence[IDX_ENGID]

        for user in [spa_user, eng_user]:
            if user not in credits:
                credits[user] = []
        credits[spa_user].append(str(spa_id))
        credits[eng_user].append(str(eng_id))

def dump_credits(filename):
    with open(filename, "w") as outfile:
        outfile.write(f"The definitions in this deck come from wiktionary.org and are used in accordance with the with the CC-BY-SA license.\n\n")
        outfile.write(f"The sentences in this deck were contributed to tatoeba.org by the following users and are used in accordance with the CC-BY 2.0 license:\n\n")
        for user, sentences in sorted(credits.items(), key=lambda item: (len(item[1])*-1, item[0])):
            count = len(sentences)
            if count>1:
                if count>5:
                    outfile.write(f"{user} ({len(sentences)}) #{', #'.join(sorted(sentences[:3]))} and {len(sentences)-3} others\n")
                else:
                    outfile.write(f"{user} ({len(sentences)}) #{', #'.join(sorted(sentences))}\n")
            else:
                outfile.write(f"{user} #{', #'.join(sorted(sentences))}\n")



dumpable_sentences = {}
def save_dump_sentences(lookups):
    if not args.dump_sentence_ids:
        return

    for word,pos in lookups:
        tag = make_tag(word, pos)
        if tag in dumpable_sentences:
            continue

        results = _sentences.get_sentences( [ [word,pos] ], 3)
        if not results:
            continue

        if results['matched'] not in ('preferred', 'exact') and ' ' not in word:
            continue

        if len(results['sentences']) != 3:
            continue


        if all( sentence[IDX_SCORE] >= 55 for sentence in results['sentences'] ):
            ids = [ f"{sentence[IDX_SPAID]}:{sentence[IDX_ENGID]}" for sentence in results['sentences' ] ]
            dumpable_sentences[tag] = ids


# (spanish, english, score, spa_id, eng_id)
def dump_sentences(filename):
    with open(filename, "w") as outfile:
        print(f"dumping {filename}")
        for tag,ids in sorted(dumpable_sentences.items()):
            word, pos = split_tag(tag)
            row = [word,pos] + ids

            outfile.write(",".join(row))
            outfile.write("\n")



class MyNote(genanki.Note):

    def write_card_to_db(self, cursor, now_ts, deck_id, note_id, order, due):
      queue = 0
      cursor.execute('INSERT INTO cards VALUES(null,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);', (
        note_id,    # nid
        deck_id,    # did
        order,      # ord
        now_ts,     # mod
        -1,         # usn
        0,          # type (=0 for non-Cloze)
        queue,      # queue
        due,          # due
        0,          # ivl
        0,          # factor
        0,          # reps
        0,          # lapses
        0,          # left
        0,          # odue
        0,          # odid
        0,          # flags
        "",         # data
      ))

    def write_to_db(self, cursor, now_ts, deck_id):

        # Preserve the timestamp if it has been specified
        if self.mod_ts:
            now_ts = self.mod_ts

        cursor.execute('INSERT INTO notes VALUES(null,?,?,?,?,?,?,?,?,?,?);', (
            self.guid,                    # guid
            self.model.model_id,          # mid
            now_ts,                       # mod
            -1,                           # usn
            self._format_tags(),          # TODO tags
            self._format_fields(),        # flds
            self.sort_field,              # sfld
            0,                            # csum, can be ignored
            0,                            # flags
            '',                           # data
        ))

        note_id = cursor.lastrowid

        count=0
        for card in self.cards:
            self.write_card_to_db(cursor, now_ts, deck_id, note_id, count, self._order)
            count+=1



def format_sound(filename):
    if not filename:
        return ""
    return f"[sound:{filename}]"

def format_image(filename):
    if not filename:
        return ""
    return f'<img src="{filename}" />'

def format_syns(deck, extra):
    deck_str = f"""<span class="syn deck">{", ".join(deck)}</span>""" if len(deck) else ""
    separator = ", " if len(deck_str) else ""
    extra_str = f"""<span class="syn extra">{separator}{", ".join(extra)}</span>""" if len(extra) else ""
    return deck_str+extra_str

def format_def(item,hide_word=None):

    results = []
    multi_pos = (len(item) > 1)

    prev_display_pos = None
    for pos in item:
        common_pos = _words.common_pos(pos)
        safe_pos = pos.replace("/", "_")

        # Don't prefix the def with the part of speech if there's only one pos
        # for this entry (unless it's a verb with type of usage specified)
        if not prev_display_pos and len(item)==1:
            prev_display_pos = "{v}" if common_pos == "verb" else f"{{{pos}}}"

        for tag in item[pos]:
            if len(results):
                results.append("\n")

            classes = ["pos", common_pos]
            if common_pos != safe_pos:
                classes.append(safe_pos)

            display_pos = f"{{{pos}}}"
            display_tag = tag

            # Only m/f and m-f nouns will have special pos in the tags
            if common_pos == "noun" and pos in [ "m-f", "m/f" ]:
                tag_pos, sep, other_tags = tag.partition(" ")
                tag_pos = tag_pos.replace(",", "")
                if tag_pos in [ "m", "f", "mf" ]:
                    display_tag = other_tags
                else:
                    tag_pos = "mf"

                classes.append(tag_pos)
                display_pos = f"{{{tag_pos}}}"

            elif common_pos == "verb" and pos in [ "vir","vitr","vr","vri","vrp","vrt","vtir","vtr", "vp", "vip", "vtp" ]:
                classes.append("reflexive")

            if prev_display_pos == display_pos:
                display_pos = ""
            else:
                prev_display_pos = display_pos

            classes += sorted(get_location_classes(tag))
            results.append(f'<span class="{" ".join(classes)}">{display_pos} ')

            usage = item[pos][tag]

            if hide_word:
                new_usage = re.sub(r"(apocopic form|diminutive|ellipsis|clipping|superlative) of [^,:;(]*", r"\1 of ... ", usage).strip()

                if new_usage != usage and len(item.keys()) == 1 and len(item[pos].keys()) == 1 \
                        and "," not in usage and ";" not in usage and "(" not in usage and ":" not in usage:
                    eprint(f"Warning: obscured definition: ({usage}) may be completely obscured")

                usage = new_usage

            if display_tag != "":
                results.append(f'<span class="tag">[{display_tag}]:</span>')

            results.append(f'<span class="usage">{usage}</span>')

            results.append('</span>')

    return "".join(results)


guidseen = {}
def validate_note(item):

    if item['guid'] in guidseen:
       eprint(f"Duplicate {key} from {item}")
    else:
        guidseen[item['guid']] = 1

    for key in [ "Spanish", "Definition", "Part of Speech", "Audio" ]:
        if item[key] == "":
            eprint(f"Missing {key} from {item}")
            return False

    return True

def get_synonyms(word, pos, limit=5, only_in_deck=True):
    items = _words.get_synonyms(word,pos)
    if only_in_deck:
        return [ k for k in items if make_tag(k,pos) in allwords_set ][:limit]
    return list(items)[:limit]

#_FEMALE1 = "Lupe"
_FEMALE1 = "Penelope"
_FEMALE2 = "Penelope"
_MALE1   = "Miguel"

def get_phrase(word, pos, noun_type, femnoun):
    voice = ""
    phrase = ""
    display = None

    if noun_type:
        if noun_type == "f":
            voice = _FEMALE2
            phrase = f"la {word}"
        elif noun_type == "fp":
            voice = _FEMALE2
            phrase = f"las {word}"
        elif noun_type == "f-el":
            voice = _FEMALE2
            phrase = f"el {word}"
        elif noun_type == "m-f":
            voice = _FEMALE1
            phrase = f"la {word}. el {word}"
            display = f"la/el {word}"
        elif noun_type == "m":
            voice = _MALE1
            phrase = f"el {word}"
        elif noun_type == "mf":
            voice = _MALE1
            phrase = f"el {word}. la {word}"
            display = f"el/la {word}"
        elif noun_type == "mp":
            voice = _MALE1
            phrase = f"los {word}"
        elif noun_type == "m/f":
            voice = _MALE1
            if femnoun in _words.wordlist.el_f_nouns:
                phrase = f"el {femnoun}. el {word}"
                display = f"el {femnoun}/el {word}"
            else:
                phrase = f"la {femnoun}. el {word}"
                display = f"la {femnoun}/el {word}"
        else:
            raise ValueError(f"Word {word} has unknown noun type {noun_type}")
    else:
        voice = _FEMALE1
        phrase = word

    if not display:
        display = phrase

    return { "voice": voice, "phrase": phrase, "display": display }


_REGIONS = {
    "canary islands": set(),
    "caribbean": {
        "cuba",
        "dominican republic",
        "puerto rico",
        "panama",
        "venezuela",
        "colombia"
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
    "united states": {
        "california",
        "louisiana",
        "new mexico",
        "texas"
    },
}

_PLACE_TO_REGION = { item:region for region,items in _REGIONS.items() for item in items }

def get_location_classes(tag_string):
    items = { t.strip() for t in tag_string.lower().split(',') }

    places = items & _PLACE_TO_REGION.keys()
    regions = items & _REGIONS.keys()

    meta_classes = set()

    if len(places)==1 and len(regions) == 0:
        meta_classes.add("only-"+next(iter(places)))

    place_regions = set()
    for place in places:
        place_regions.add(_PLACE_TO_REGION[place])

    if len(regions | place_regions) == 1:
        meta_classes.add("only-"+next(iter(regions|place_regions)))

#    all_places = places
#    for region in regions:
#        all_places |= _PLACES[region]


    # Special case handling for "latin america"
    if (len(places) or len(regions)) and not len( (regions|place_regions) - { "caribbean","central america","mexico","south america","united states","latin america" }):
        meta_classes.add("only-latin-america")

    return [ item.replace(" ", "-") for item in regions | places | meta_classes ]


seen_clues = {}

def build_item(word, pos, mediadir):
    spanish = word.strip()
    pos = pos.lower()
    item_tag = make_tag(spanish, pos)

    english = ""
    noun_type = ""
    usage = _words.lookup(spanish, pos, get_all_pos=True)
    deck_syns = get_synonyms(spanish, pos, 5, only_in_deck=True)
    extra_syns = [k for k in get_synonyms(spanish, pos, 5, only_in_deck=False) if k not in deck_syns] if len(deck_syns)<5 else []

    if usage and len(usage):
        english = format_def(usage)
        if pos == "noun":
            noun_type = next(iter(usage))
    else:
        raise ValueError("No english", spanish, pos)

    shortdef = shortdefs.get(item_tag)
    if not shortdef:
        shortdef = _words.lookup(word, pos, max_length=60)
    short_english = format_def(shortdef, hide_word=word) if shortdef else ""

    defs = [ value.strip() for pos,tags in shortdef.items() for tag,def_str in tags.items() for def1 in def_str.split(";") for value in def1.split(",") ]
    seen_tag = "|".join(deck_syns + sorted(defs))
    if seen_tag in seen_clues:
        eprint(f"Warning: {seen_tag} is used by {item_tag} and {seen_clues[seen_tag]}")
#        exit()
    else:
        seen_clues[seen_tag] = item_tag

    if short_english == english:
        short_english = ""

    femnoun = _words.wordlist.get_feminine_noun(spanish) if pos == "noun" else None
    tts_data = get_phrase(spanish,pos,noun_type,femnoun)
    sound = spanish_speech.get_speech(tts_data['voice'], tts_data['phrase'], mediadir)

    all_usage_pos = { _words.common_pos(k):1 for k in usage.keys() }.keys()
    lookups = [ [ spanish, pos ] for pos in all_usage_pos ]
    sentences = get_sentences(lookups, 3)
    save_dump_sentences(lookups)

    if pos == "part":
        pos = "past participle"

    item = {
        'Spanish': spanish,
        'Part of Speech': noun_type if pos == "noun" else pos,
        'Synonyms': format_syns(deck_syns, extra_syns),
        'ShortDef': short_english,
        'Definition': english,
        'Sentences': sentences,
        'Display': tts_data['display'],
        'Audio':   format_sound(sound),
        'guid': genanki.guid_for(item_tag, "Jeff's Spanish Deck")
    }


    tags = [ noun_type if pos == "noun" else pos ]
#    if "tags" in row and row['tags'] != "":
#        for tag in row['tags'].split(" "):
#            tags.append(tag)
    item['tags'] = tags

    FILE=os.path.join(mediadir, sound)
    if os.path.isfile(FILE):
        media.append(FILE)
    else:
        item['Sound'] = ""


    if not validate_note(item):
        exit(1)

    return item


def make_tag(word, pos):
    if not pos:
        return word.lower()

    return pos.lower() + ":" + word.lower()

def split_tag(wordtag):
    pos,junk,word = wordtag.partition(":")
    return [word,pos.lower()]

def wordlist_indexof(target):
    if ":" in target:
        return allwords.index(target)

    for index in range(len(allwords)):
        word, pos = split_tag(allwords[index])

        if word == target:
            return index

def wordlist_insert_after(target, wordtag):
    index = wordlist_indexof(target)
    if not index:
        eprint(f"ERROR: {target} not found in wordlist, unable to insert {wordtag} after it")
        return

    allwords.insert(index+1,wordtag)
    allwords_set.add(wordtag)

def wordlist_replace(old_tag, new_tag):

    index = wordlist_indexof(old_tag)
    if not index:
        eprint(f"ERROR: {old_tag} not found in wordlist, unable to replace with {new_tag}")
        return

    old_tag = allwords[index]
    allwords_set.remove(old_tag)
    allwords_set.add(new_tag)

    allwords[index] = new_tag

def wordlist_remove(wordtag):

    index = wordlist_indexof(wordtag)
    if not index:
        eprint(f"ERROR: {wordtag} not found in wordlist, unable to remove")
        return

    old_tag = allwords[index]
    allwords_set.remove(old_tag)
    del allwords[index]

def wordlist_insert(wordtag, position):
    if wordtag in allwords_set:
        eprint(f"ERROR: {wordtag} already exists in wordlist, cannot insert at position {position}")
        return

    # Note, don't actually insert the word at the specified position, because later wordlists
    # may delete items and rearrange the order.  Instead, add it to the bottom of the list and
    # save the desired position in allwords_positions, which will be used after the wordlist
    # is finished to position it absolutely

    allwords_set.add(wordtag)
    allwords.append(wordtag)
    allwords_positions[wordtag] = position

def wordlist_append(wordtag):
    if wordtag in allwords_set:
        eprint(f"ERROR: {wordtag} already exists in wordlist, cannot be added again")
        return

    allwords.append(wordtag)
    allwords_set.add(wordtag)

def load_shortdefs(filename):
    with open(filename, newline='') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for reqfield in ["spanish", "pos", "shortdef"]:
            if reqfield not in csvreader.fieldnames:
                raise ValueError(f"No '{reqfield}' field specified in file {filename}")
        for row in csvreader:
            if not row or row.get('shortdef',"") == "":
                continue

            common_pos = _words.common_pos(row['pos'])
            item_tag = make_tag(row['spanish'],common_pos)
            shortdefs[item_tag] = { row['pos']: { '': row['shortdef'] } }

def main():

    global allwords
    global allwords_set
    global args

    parser = argparse.ArgumentParser(description='Compile anki deck')
    parser.add_argument('deckname', help="Name of deck to build")
    parser.add_argument('-m', '--mediadir', help="Directory containing deck media resources (default: DECKNAME.media)")
    parser.add_argument('-w', '--wordlist', action='append', help="List of words to include/exclude from the deck (default: DECKNAME.json")
    parser.add_argument('--short-defs',  help="CSV file with short definitions (default DECKNAME.shortdefs)")
    parser.add_argument('-l', '--limit', type=int, help="Limit deck to N entries")
    parser.add_argument('--dump-sentence-ids',  help="Dump high scoring sentence ids to file")
    parser.add_argument('--dump-credits',  help="Dump high scoring sentence ids to file")
    parser.add_argument('--dump-notes',  help="Dump notes to file")
    parser.add_argument('--dump-removed',  help="Dump list of removed note ids to file (requires --anki)")
    parser.add_argument('--deckinfo',  help="Read model/deck info from JSON file (default: DECKNAME.json)")
    parser.add_argument('--anki', help="Read/write data from specified anki profile")
    parser.add_argument('--dictionary', help="Dictionary file name (DEFAULT: es-en.txt)")
    parser.add_argument('--sentences', help="Sentences file name (DEFAULT: sentences.tsv)")
    parser.add_argument('--data-dir', help="Directory contaning the dictionary (DEFAULT: SPANISH_DATA_DIR environment variable or 'spanish_data')")
    parser.add_argument('--custom-dir', help="Directory containing dictionary customizations (DEFAULT: SPANISH_CUSTOM_DIR environment variable or 'spanish_custom')")
    args = parser.parse_args()

    if not args.dictionary:
        args.dictionary="es-en.txt"

    if not args.sentences:
        args.sentences="sentences.tsv"

    if not args.data_dir:
        args.data_dir = os.environ.get("SPANISH_DATA_DIR", "spanish_data")

    if not args.custom_dir:
        args.custom_dir = os.environ.get("SPANISH_CUSTOM_DIR", "spanish_custom")

    if not args.mediadir:
        args.mediadir = args.deckname + ".media"

    if not args.wordlist:
        args.wordlist = [ args.deckname + ".csv" ]

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

    with open(args.deckinfo) as jsonfile:
        deck_info = json.load(jsonfile)

    card_model = make_card_model(deck_info['model'])
    deck_guid = deck_info['deck']['id']
    my_deck = genanki.Deck(int(deck_guid),deck_info['deck']['name'],deck_info['deck']['desc'])

    if args.anki:
        ankidb = os.path.join( os.path.expanduser("~"), ".local/share/Anki2", args.anki, "collection.anki2" )
        if not os.path.isfile(ankidb):
            print("Cannot find anki database:", ankidb)
            exit(1)

        db_notes = load_db_notes(ankidb, deck_info['deck']['name'])
        for guid, item in db_notes.items():
            hashval = get_note_hash(guid,item['flds'],item['tags'])
            db_timestamps[hashval] = item['mod']


    init_data(args.dictionary, args.sentences, args.data_dir, args.custom_dir)

    load_shortdefs(args.short_defs)



    # read through all the files to populate the synonyms and excludes lists
    for wordlist in args.wordlist:
        with open(wordlist, newline='') as csvfile:
            csvreader = csv.DictReader(csvfile)
            for reqfield in ["pos", "spanish"]:
                if reqfield not in csvreader.fieldnames:
                    raise ValueError(f"No '{reqfield}' field specified in file {wordlist}")

            for row in csvreader:
                if not row:
                    continue

                if 'flags' in row and 'CLEAR' not in row['flags']:
                    continue

                item_tag = make_tag(row['spanish'],row['pos'])


                position = row.get("position",None)
                if not position:
                    wordlist_append(item_tag)

                # +pos:word indicates that the entry should be positioned immedialy after the specified pos:word
                # or after the first occurance of word if pos: is not specified
                elif position.startswith("+"):
                    wordlist_insert_after(position[1:], item_tag)

                # pos:word will replace the specific pos:word or the first occurance of the word if pos: is not specified
                elif not position[0].isdigit() and position[0] != "-":
                    wordlist_replace(position, item_tag)

                # Negative position indicates that all previous instances of this word should be removed
                elif int(position) < 0:
                    wordlist_remove(item_tag)

                # a digit in the position column indicates that it should be inserted at that position
                elif int(position) >0 and int(position) < len(allwords):
                    wordlist_insert(item_tag, int(position))

                # otherwise put it at the end of the list
                else:
                    raise ValueError("Position {position} does not exist, ignoring")

    # Arrange any items with absolute positions
    for wordtag,position in sorted(allwords_positions.items(), key=lambda item: item[1]):
        index = wordlist_indexof(wordtag)
        if index != position:
            allwords.pop(index)
            allwords.insert(position-1, wordtag)

        word, pos = split_tag(wordtag)
        print(f"Absolute position for {wordtag}, consider using relative: ~{allwords[position-2]},{word},{pos}", file=sys.stderr)


    if args.limit and args.limit < len(allwords):
        allwords = allwords[:args.limit]
        allwords_set = set(allwords)

    rows = []

    # Build the deck
    _fields = [ "Rank", "Spanish", "Part of Speech", "Synonyms", "ShortDef", "Definition", "Sentences", "Display", "Audio" ]

    position=0
    deck_guids = set()
    for wordtag in allwords:
        word, pos = split_tag(wordtag)

        position+=1
        item = build_item(word, pos, args.mediadir)
        item['Rank'] = str(position)
        item['tags'].append( str(math.ceil(position / 500)*500) )

        row = []
        for field in _fields:
            row.append(item[field])

        note = MyNote( model = card_model, sort_field=1, fields = row, guid = item['guid'], tags = item['tags'] )
        # preserve the mod timestamp if the note matches with the database
        note.mod_ts = get_mod_timestamp(note)
        if not note.mod_ts:
            if item['guid'] not in db_notes:
                print(f"added: {wordtag}")
            else:
                old_data = db_notes[item['guid']]
                if old_data['flds'] != note._format_fields():
                    old_fields = old_data['flds'].split(chr(31))
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

        deck_guids.add(item['guid'])

        note._order = position
        my_deck.add_note( note )
        rows.append(row)

    package_filename = os.path.join(os.getcwd(), args.deckname + ".apkg")
    my_package = genanki.Package(my_deck)
    my_package.media_files = media
    my_package.write_to_file(package_filename)

    if args.dump_sentence_ids:
        dump_sentences(args.dump_sentence_ids)

    if args.dump_notes:
        with open(args.dump_notes, 'w', newline='') as outfile:
            csvwriter = csv.writer(outfile)

            del _fields[7] # audio
            del _fields[0] # rank

            csvwriter.writerow(_fields)
            for row in rows:
                del row[7]
                del row[0]
                csvwriter.writerow(row)

    if args.dump_removed:
        with open(args.dump_removed, "w") as outfile:
            for guid in db_notes.keys()-deck_guids:
                outfile.write(str(db_notes[guid]['nid']))

    if args.dump_credits:
        dump_credits(args.dump_credits)

if __name__ == "__main__":
    main()
