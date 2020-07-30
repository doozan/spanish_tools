#!/usr/bin/python3
# -*- python-mode -*-

import genanki
import csv
import os
import sys
import math
import json
import re
import spanish_words
import spanish_sentences
import spanish_speech
import argparse

parser = argparse.ArgumentParser(description='Compile anki deck')
parser.add_argument('deckname', help="Name of deck to build")
parser.add_argument('-m', '--mediadir', help="Directory containing deck media resources (default: DECKNAME.media)")
parser.add_argument('-w', '--wordlist', action='append', help="List of words to include/exclude from the deck (default: DECKNAME.json")
parser.add_argument('-j', '--json',  help="JSON file with deck info (default: DECKNAME.json)")
parser.add_argument('-d', '--dump-sentence-ids',  help="Dump high scoring sentence ids to file")
parser.add_argument('-n', '--dump-notes',  help="Dump notes to file")
parser.add_argument('-l', '--limit', type=int, help="Limit deck to N entries")

args = parser.parse_args()

if not args.mediadir:
    args.mediadir = args.deckname + ".media"

if not args.wordlist:
    args.wordlist = [ args.deckname + ".csv" ]

if not args.json:
    args.json = args.deckname + ".json"

if not os.path.isdir(args.mediadir):
    print(f"Deck directory does not exist: {args.mediadir}")
    exit(1)

for wordlist in args.wordlist:
    if not os.path.isfile(wordlist):
        print(f"Wordlist file does not exist: {wordlist}")
        exit(1)

if not os.path.isfile(args.json):
    print(f"Deck JSON does not exist: {args.json}")
    exit(1)


allwords = []
allwords_set = set()
allwords_positions = {}

words = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt")
spanish_sentences = spanish_sentences.sentences("spanish_data/sentences.json")

media = []

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def fail(*args, **kwargs):
    eprint(*args, **kwargs)
    exit(1)

def format_sentences(sentences):
    return "<br>\n".join( f'<span class="spa">{item[0]}</span><br>\n<span class="eng">{item[1]}</span>' for item in sentences )

def get_sentences(items, count):

    results = spanish_sentences.get_sentences(items, count)

    if len(results['sentences']):
        return format_sentences(results['sentences'])

    return ""


dumpable_sentences = {}
def save_dump_sentences(lookups):
    if not args.dump_sentence_ids:
        return

    for word,pos in lookups:
        tag = make_tag(word, pos)
        if tag in dumpable_sentences:
            continue

        results = spanish_sentences.get_sentences( [ [word,pos] ], 3)
        if not results:
            continue

        if results['matched'] not in ('preferred', 'exact'):
            continue

        if len(results['sentences']) != 3:
            continue

        all_good=True
        for sentence in results['sentences']:
            if sentence[2] not in [ 55, 56 ]:
                all_good = False

        if all_good:
            ids = [ f"{sentence[3]}:{sentence[4]}" for sentence in results['sentences' ] ]
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

def format_def(item):

    results = []
    multi_pos = (len(item) > 1)

    prev_display_pos = None
    for pos in item:
        common_pos = words.common_pos(pos)
        safe_pos = pos.replace("/", "_")

        # Don't prefix the def with the part of speech if there's only one pos
        # for this entry (unless it's a verb with type of usage specified)
        if not prev_display_pos and len(item)==1:
            prev_display_pos = "{v}" if common_pos == "verb" else f"{{{pos}}}"

        for tag in item[pos]:
            if len(results):
                results.append("<br>\n")

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

            elif common_pos == "verb" and pos in [ "vir","vitr","vr","vri","vrp","vrt","vtir","vtr" ]:
                classes.append("reflexive")

            if prev_display_pos == display_pos:
                display_pos = ""
            else:
                prev_display_pos = display_pos

            results.append(f'<span class="{" ".join(classes)}">{display_pos} ')

            usage = item[pos][tag]

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

    for key in [ "Spanish", "English", "Part of Speech", "Audio" ]:
        if item[key] == "":
            eprint(f"Missing {key} from {item}")
            return False

    return True

def get_synonyms(word, pos, limit=5):
    items = words.get_synonyms(word,pos)
    return [ k for k in items if make_tag(k,pos) in allwords_set ][:limit]

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
            if femnoun in words.wordlist.el_f_nouns:
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



def build_item(word, pos):
    spanish = word.strip()
    pos = pos.lower()

    english = ""
    noun_type = ""
    usage = words.lookup(spanish, pos)
    syns = get_synonyms(spanish, pos)
    if usage and len(usage):
        english = format_def(usage)
        if pos == "noun":
            noun_type = list(usage.keys())[0]
    else:
        print(row)
        raise ValueError("No english", spanish, pos)

    femnoun = words.wordlist.get_feminine_noun(spanish) if pos == "noun" else None
    tts_data = get_phrase(spanish,pos,noun_type,femnoun)
    sound = spanish_speech.get_speech(tts_data['voice'], tts_data['phrase'], args.mediadir)

    all_usage_pos = { words.common_pos(k):1 for k in usage.keys() }.keys()
    lookups = [ [ spanish, pos ] for pos in all_usage_pos ]
    sentences = get_sentences(lookups, 3)
    save_dump_sentences(lookups)

    if pos == "part":
        pos = "past participle"

    item = {
        'Spanish': spanish,
        'Part of Speech': noun_type if pos == "noun" else pos,
        'Synonyms': ", ".join(syns),
        'English': english,
        'Sentences': sentences,
        'Display': tts_data['display'],
        'Audio':   format_sound(sound),
        'guid': genanki.guid_for(make_tag(spanish, pos), "Jeff's Spanish Deck")
    }


    tags = [ noun_type if pos == "noun" else pos ]
    tags.append("NEW")
    if "tags" in row and row['tags'] != "":
        for tag in row['tags'].split(" "):
            tags.append(tag)
    item['tags'] = tags

    FILE=os.path.join(args.mediadir, sound)
    if os.path.isfile(FILE):
        media.append(FILE)
    else:
        item['Sound'] = ""


    if not validate_note(item):
        exit()

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

def wordlist_replace(old_tag, new_tag):

    index = wordlist_indexof(old_tag)
    if not index:
        raise ValueError(f"{old_tag} not found in wordlist, unable to replace with {new_tag}")

    old_tag = allwords[index]
    allwords_set.remove(old_tag)
    allwords_set.add(new_tag)

    allwords[index] = new_tag

def wordlist_remove(wordtag):

    index = wordlist_indexof(wordtag)
    if not index:
        raise ValueError(f"{old_tag} not found in wordlist, unable to remove")

    old_tag = allwords[index]
    allwords_set.remove(old_tag)
    del allwords[index]

def wordlist_insert(wordtag, position):
    if wordtag in allwords_set:
        raise ValueError(f"{wordtag} already exists in wordlist, cannot insert at position {position}")

    # Note, don't actually insert the word at the specified position, because later wordlists
    # may delete items and rearrange the order.  Instead, add it to the bottom of the list and
    # save the desired position in allwords_positions, which will be used after the wordlist
    # is finished to position it absolutely

    allwords_set.add(wordtag)
    allwords.append(wordtag)
    allwords_positions[wordtag] = position

def wordlist_append(wordtag):
    if wordtag in allwords_set:
        raise ValueError(f"{wordtag} already exists in wordlist, cannot be added again")

    allwords.append(wordtag)
    allwords_set.add(wordtag)



with open(args.json) as jsonfile:
    data = json.load(jsonfile)

model_guid = list(data['model'].keys())[0]
model_name = data['model'][model_guid]['name']
deck_guid = 1587078062419

my_deck = genanki.Deck(int(deck_guid),'Spanish top 5000-revised', "5000 common Spanish words")

# Create a template for anki card
card_model = genanki.Model(model_guid,
  model_name,
  fields=data['model'][model_guid]['flds'],
  templates=data['model'][model_guid]['tmpls'],
  css=data['model'][model_guid]['css']
)



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

            # Position that is another word instead of a numeric value will replace pos:word specified
            # or the first occurance of the word if the pos: is not specified
            if 'position' in row and not row['position'][0].isdigit() and not row['position'][0] == "-":
                wordlist_replace(row['position'], item_tag)

            # Negative position indicates that all previous instances of this word should be removed
            elif 'position' in row and int(row['position']) < 0:
                wordlist_remove(item_tag)

            # a digit in the position column indicates that it should be inserted at that position
            elif 'position' in row and int(row['position']) >0 and int(row['position']) < len(allwords):
                wordlist_insert(item_tag, int(row['position']))

            # otherwise put it at the end of the list
            else:
                wordlist_append(item_tag)

# Arrange any items with absolute positions
for wordtag,position in sorted(allwords_positions.items(), key=lambda item: item[1]):
    index = wordlist_indexof(wordtag)
    if index != position:
        allwords.pop(index)
        allwords.insert(position-1, wordtag)


if args.limit and args.limit < len(allwords):
    allwords = allwords[:args.limit]
    allwords_set = set(allwords)

rows = []

# Build the deck
_fields = [ "Rank", "Spanish", "Part of Speech", "Synonyms", "English", "Sentences", "Display", "Audio" ]

position=0
for wordtag in allwords:
    word, pos = split_tag(wordtag)

    position+=1
    item = build_item(word, pos)
    item['Rank'] = str(position)
    item['tags'].append( str(math.ceil(position / 500)*500) )

    row = []
    for field in _fields:
        row.append(item[field])

    note = MyNote( model = card_model, sort_field=1, fields = row, guid = item['guid'], tags = item['tags'] )
    note._order = position
    my_deck.add_note( note )
    rows.append(row)

my_package = genanki.Package(my_deck)
my_package.media_files = media
my_package.write_to_file(args.deckname + '.apkg')

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
