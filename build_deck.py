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

words = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt", synonyms="spanish_data/synonyms.txt")
spanish_sentences = spanish_sentences.sentences("spanish_data/sentences.json")

allwords = {}

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def fail(*args, **kwargs):
    eprint(*args, **kwargs)
    exit(1)

parser = argparse.ArgumentParser(description='Compile anki deck')
parser.add_argument('deckname', help="Name of deck to build")
parser.add_argument('-m', '--mediadir', help="Directory containing deck media resources (default: DECKNAME.media)")
parser.add_argument('-w', '--wordlist', action='append', help="List of words to include/exclude from the deck (default: DECKNAME.json")
parser.add_argument('-j', '--json',  help="JSON file with deck info (default: DECKNAME.json)")
parser.add_argument('-g', '--guids',  help="Read guids from file")
args = parser.parse_args()

if not args.mediadir:
    args.mediadir = args.deckname + ".media"

if not args.wordlist:
    args.wordlist = [ args.deckname + ".csv" ]

if not args.json:
    args.json = args.deckname + ".json"

if not os.path.isdir(args.mediadir):
    fail(f"Deck directory does not exist: {args.mediadir}")

for wordlist in args.wordlist:
    if not os.path.isfile(wordlist):
        fail(f"Wordlist file does not exist: {wordlist}")

if not os.path.isfile(args.json):
    fail(f"Deck JSON does not exist: {args.json}")


noun_articles = {
    "m": "el",
    "mp": "los",
    "f": "la",
    "fp": "las",
    "mf": "el/la",
    "f-el": "el",
    "m-f": "el",
    "m/f": "el"
}

def format_sentences(sentences):
    return "<br>\n".join( f'<span class="spa">{pair[0]}</span><br><span class="eng">{pair[1]}</span>' for pair in sentences )

def get_sentences(word, pos, count):

    results = spanish_sentences.get_sentences(word, pos, count)

    if len(results['sentences']):
        return format_sentences(results['sentences'])

    return ""



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

#    def __init__(self, model=None, fields=None, sort_field=None, tags=None, guid=None):
#        super(MyNote, self).__init__(model, fields, sort_field, tags, guid)
#        try:
#            self.guid = guid
#        except AttributeError:
#            # guid was defined as a property
#            pass
#
#    @property
#    def guid(self):
#        if self._guid is None:
#            return genanki.guid_for(self.fields[1], self.fields[2])
#        return self._guid
#
#    @guid.setter
#    def guid(self, val):
#        self._guid = val

#    @property
#    def guid(self):
#        if super(MyNote, self)._guid is None:
#            return genanki.guid_for(self.fields[0], self.fields[6])


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
    for pos in item:
        pos_tag = ""
        if len(item.keys()) > 1:
            pos_tag = f'<span class="pos pos-{pos}">{{{pos}}} </span>'

        for tag in item[pos]:
            if len(results):
                results.append("<br>\n")

            results.append(pos_tag)

            usage = item[pos][tag]

            if tag != "":
                results.append(f'<span class="usage-type usage-tag">[{tag}]: </span>')

            results.append(f'<span class="usage">{usage}</span>')

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

def get_synonyms(word, pos):
    items = words.synonyms.get_synonyms(word)
    return [ k for k in items if pos+":"+k in allwords ]

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
            phrase = f"la {femnoun}. el {word}"
            display = f"la {femnoun}/el {word}"
        else:
            raise ValueError("Unknown noun type", noun_type)
    else:
        voice = _FEMALE1
        phrase = word

    if not display:
        display = phrase

    return { "voice": voice, "phrase": phrase, "display": display }



def build_item(row):
    spanish = row['spanish'].strip()
    english = ""
    noun_type = ""
    pos = row['pos'].lower()
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

    if pos == "part":
        pos = "past participle"

    item = {
#            'Picture': format_image(image),
#        'Rank': row['count'],
        'Spanish': spanish,
        'Part of Speech': noun_type if pos == "noun" else pos,
        'Synonyms': ", ".join(syns),
        'English': english,
        'Sentences': get_sentences(spanish, pos, 3),
        'Display': tts_data['display'],
        'Audio':   format_sound(sound),
    }

    wordtag = make_tag(spanish, pos)
    if 'guid' in row and row['guid']:
        item['guid'] = row['guid']
    elif wordtag in guids:
        item['guid'] = guids[wordtag]
    else:
#        print("generating guid for ", wordtag)
        item['guid'] = genanki.guid_for(wordtag)

#        tags = [ row['pos'],str(math.ceil(int(row['rank']) / 500)*500) ]
    tags = [ noun_type if pos == "noun" else pos ]
    tags.append("NEW")
    if "tags" in row and row['tags'] != "":
        for tag in row['tags'].split(" "):
            tags.append(tag)
    item['tags'] = tags

#        item['Picture'] = ""
#        FILE=os.path.join(args.mediadir, image)
#        if os.path.isfile(FILE):
#            media.append(FILE)
#        else:
#            item['Picture'] = ""
#            print("Skipping missing pic",image,row['rank'],row['spanish'], file=sys.stderr)

    FILE=os.path.join(args.mediadir, sound)
    if os.path.isfile(FILE):
        media.append(FILE)
    else:
        item['Sound'] = ""


    if not validate_note(item):
        exit()

    return item


def make_tag(word, pos):
    return pos.lower() + ":" + word.lower()



media = []
notes = []
all_items = []

guids = {}
if args.guids:
    with open(args.guids) as infile:
        csvreader = csv.DictReader(infile)
        for row in csvreader:
            wordtag = make_tag(row['spanish'], row['pos'])
            guids[wordtag] = row['guid']

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

            # Rank that is another word will replace pos:word specified
            # or the first occurance of the word if the pos: is not specified
            if 'rank' in row and not row['rank'][0].isdigit() and not row['rank'][0] == "-":
                old_word = row['rank']
                old_pos = ""
                if ":" in row['rank']:
                    old_word, old_pos = row['rank'].lower().split(":")
                new_word = row['spanish'].lower()
                new_pos = row['pos'].lower()
                new_tag = make_tag(new_word, new_pos)

                if old_pos:
                    old_tag = make_tag(old_word, old_pos)
                    item = allwords.pop(old_tag)
                    item['spanish'] = new_word
                    item['pos'] = new_pos
                    allwords[newtag] = item
                    #print(f"replaced {old_tag} with {new_word} ({new_pos})")
                else:
                    replaced=False
                    for wordtag in list(allwords.keys()):
                        item = allwords[wordtag]
                        if item['spanish'].lower() == old_word:
                            item = allwords.pop(wordtag)
                            item['spanish'] = new_word
                            item['pos'] = new_pos
                            allwords[new_tag] = item
                            #print(f"replaced {old_word} with {new_word} ({new_pos})")
                            replaced=True
                            break
                    if not replaced:
                        raise ValueError(f"{old_word} not found, unable to replace with {new_word} ({new_pos}) from {wordlist}")
#                        allwords[newtag] = { 'spanish': new_word, 'pos': new_pos }


            # Negative rank indicates that all previous instances of this word should be removed
            elif 'rank' in row and int(row['rank']) < 0:
                exclude_word = row['spanish'].lower()
                exclude_pos = row['pos'].lower() if 'pos' in row and row['pos'] != "" else None
                if exclude_pos:
                    exclude_tag = make_tag(row['spanish'],row['pos'])
                    if exclude_tag in allwords:
                        allwords.pop(exclude_tag)
                    else:
                        print(f"{exclude_tag} was not removed because it is not in the wordlist")
                else:
                    found=False
                    for wordtag in list(allwords.keys()):
                        item = allwords[wordtag]
                        if item['spanish'].lower() == exclude_word:
                            found=True
                            allwords.pop(wordtag)
                    if not found:
                        print(f"{exclude_word} was not removed because it is not in the wordlist")

            else:
                wordtag = make_tag(row['spanish'],row['pos'])
                # exclude duplicates
                if wordtag not in allwords:
                    allwords[wordtag] = row

# Build the items
for wordtag, row in allwords.items():
    item = build_item(row)

    rank = int(row['rank']) if row['rank'] else 0
    if rank and rank < len(all_items):
        all_items.insert(rank-1, item)
    else:
        all_items.append(item)

# Number the items
count = 1
for item in all_items:
    item['Rank'] = str(count)
    count += 1

with open(args.json) as jsonfile:
    data = json.load(jsonfile)

model_guid = list(data['model'].keys())[0]
model_name = data['model'][model_guid]['name']
#deck_guid = [ item for item in data['deck'] if item != '1' ][0]
deck_guid = 1587078062419

my_deck = genanki.Deck(int(deck_guid),'Spanish top 5000-revised', "5000 common Spanish words")

# Create a template for anki card
card_model = genanki.Model(model_guid,
  model_name,
  fields=data['model'][model_guid]['flds'],
  templates=data['model'][model_guid]['tmpls'],
  css=data['model'][model_guid]['css']
)

_fields = [ "Rank", "Spanish", "Part of Speech", "Synonyms", "English", "Sentences", "Display", "Audio" ]

with open('notes_rebuild.csv', 'w', newline='') as outfile:
    csvwriter = csv.writer(outfile)
    csvwriter.writerow(_fields)

    for item in all_items:
        row = []
        for field in _fields:
            row.append(item[field])

        note = MyNote( model = card_model, sort_field=row[4], fields = row, guid = item['guid'], tags = item['tags'] )
        note._order = int(item['Rank'])
        my_deck.add_note( note )
        csvwriter.writerow(row)

my_package = genanki.Package(my_deck)
my_package.media_files = media
my_package.write_to_file(args.deckname + '.apkg')
