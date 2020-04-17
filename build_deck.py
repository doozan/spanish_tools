import genanki
import csv
import os
import sys
import math
import json
import re
import spanish_dictionary
import spanish_sentences
import spanish_speech
import argparse



def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def fail(*args, **kwargs):
    eprint(*args, **kwargs)
    exit(1)

parser = argparse.ArgumentParser(description='Compile anki deck')
parser.add_argument('deckname', help="Name of deck to build")
parser.add_argument('--mediadir', help="Directory containing deck media resources (default: DECKNAME.media)")
parser.add_argument('--wordlist', help="Wordlist to use (default: DECKNAME.csv)")
parser.add_argument('--json',  help="JSON file with deck info (default: DECKNAME.json)")
args = parser.parse_args()

if not args.mediadir:
    args.mediadir = args.deckname + ".media"

if not args.wordlist:
    args.wordlist = args.deckname + ".csv"

if not args.json:
    args.json = args.deckname + ".json"

if not os.path.isdir(args.mediadir):
    fail("Deck directory does not exist: %s"%args.mediadir)

if not os.path.isfile(args.wordlist):
    fail("Wordlist file does not exist: %s"%args.wordlist)

if not os.path.isfile(args.json):
    fail("Deck JSON does not exist: %s"%args.json)


# check that we don't have any unknown pos types
# squash nouns into generic "noun" lookup
# squash verbs into generic "verb" lookup
pos_types = {
    'adj': 'adj',
    'adv': 'adv',
    'art': 'art',
    'conj': 'conj',
    'interj': 'interj',

    "m": "noun",
    "f": "noun",
    "mf": "noun",
    "f-el": "noun",
    "m-f": "noun",
    "m/f": "noun",

    'num': 'num',
    'prep': 'prep',
    'pron': 'pron',
    'v': 'verb',

    'phrase': 'phrase'
}

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
pos_nouns = list(noun_articles.keys())



def format_sentences(sentences):
    return "<br>\n".join( '<span class="spa">%s</span><br><span class="eng">%s</span>' % pair[:2] for pair in sentences )

def get_sentences(word, pos, count):

    results = spanish_sentences.get_sentences(word, pos, count)

    if len(results['sentences']):
        return format_sentences(results['sentences'])

    return ""



#class MyNote(genanki.Note):
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



with open(args.json) as jsonfile:
    data = json.load(jsonfile)

model_guid = list(data['model'].keys())[0]
model_name = data['model'][model_guid]['name']
#deck_guid = [ item for item in data['deck'] if item != '1' ][0]
deck_guid = 1587078062419

# Create a template for anki card
card_model = genanki.Model(model_guid,
  model_name,
  fields=data['model'][model_guid]['flds'],
  templates=data['model'][model_guid]['tmpls'],
  css=data['model'][model_guid]['css']
)


def format_sound(filename):
    if not filename:
        return ""
    return "[sound:%s]"%filename

def format_image(filename):
    if not filename:
        return ""
    return '<img src="%s" />'%filename

def is_noun(pos):
    return pos in pos_nouns

def get_article(pos):
    return noun_articles[pos]


#def format_spanish(item):
#    return "%s (%s)" % (item['spanish'], item['pos'])

def format_def(item):

    result = ""
    for pos in item:
        pos_tag = ""
        if len(item.keys()) > 1:
            pos_tag = '<span class="pos pos-%s">{%s} </span>'%(pos,pos)

        for tag in item[pos]:
            if result != "":
                result += "<br>\n"

            result += pos_tag

            defs = spanish_dictionary.get_best_defs(item[pos][tag],4)
            usage = spanish_dictionary.defs_to_string(defs, pos)

            if tag != "x":
                result += '<span class="usage-type usage-tag">[%s]: </span>'%tag

            result += '<span class="usage">%s</span>'%usage

    return result


seen = {}
def validate_note(item):

    if item['guid'] in seen:
       eprint("Duplicate %s from %s" % (key, item))
    else:
        seen[item['guid']] = 1

    for key in [ "Spanish", "English", "Part of Speech", "Audio" ]:
        if item[key] == "":
            eprint("Missing %s from %s" % (key, item))
            return False

    return True

allwords = {}
def get_synonyms(word, pos):
    items = spanish_dictionary.get_synonyms(word)
    return [ k for k in items if pos+":"+k in allwords ]


my_deck = genanki.Deck(int(deck_guid),'Spanish top 5000-revised', "5000 common Spanish words")

media = []
notes = []

# read through the file once to build a list of words for the repeat/synonym checking
with open(args.wordlist, newline='') as csvfile: #, open('notes_rebuild.csv', 'w', newline='') as outfile:
    csvreader = csv.DictReader(csvfile)
    allwords = set( row['pos'].lower()+":"+row['spanish'] for row in csvreader )

with open(args.wordlist, newline='') as csvfile: #, open('notes_rebuild.csv', 'w', newline='') as outfile:
    csvreader = csv.DictReader(csvfile)
#    csvwriter = csv.DictWriter(outfile, fieldnames=fieldnames)
#   csvwriter.writeheader()

    for row in csvreader:
#        print(row)
#        image = row['oldrank'] + ".jpg"
        #sound = row['sound'] if row['sound'] != "" else row['rank'] + ".mp3"

        spanish = row['spanish']
        english = ""
        noun_type = ""
        pos = row['pos'].lower()
        usage = spanish_dictionary.lookup(spanish, pos)
        syns = get_synonyms(spanish, pos)
        if usage and len(usage):
            english = format_def(usage)
            if pos == "noun":
                noun_type = list(usage.keys())[0]
        else:
            print("No english", spanish, pos)
            print(row)
            exit()



        speech_res = spanish_speech.get_speech(spanish,pos,noun_type,args.mediadir)
        sound = speech_res['filename']


        item = {
#            'Picture': format_image(image),
            'Rank': row['rank'],
            'Spanish': spanish,
            'Part of Speech': noun_type if pos == "noun" else pos,
            'Synonyms': ", ".join(syns),
            'English': english,
            'Sentences': get_sentences(spanish, pos, 3),
            'Article': get_article(noun_type) if pos == "noun" else spanish,
            'Audio':   format_sound(sound),
        }

        item['guid'] = row['guid'] if row['guid'] != "" else genanki.guid_for(item['Spanish'], item['Part of Speech'])

#        tags = [ row['pos'],str(math.ceil(int(row['rank']) / 500)*500) ]
        tags = [ noun_type if pos == "noun" else pos ]
        tags.append("NEW")
        if "tags" in row and row['tags'] != "":
            for tag in row['tags'].split(" "):
                tags.append(tag)

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

        row = []
        _fields = [ "Rank", "Spanish", "Part of Speech", "Synonyms", "English", "Sentences", "Article", "Audio" ]
        for field in _fields:
            row.append(item[field])

        my_deck.add_note( genanki.Note( model = card_model, sort_field=row[4], fields = row, guid = item['guid'], tags = tags ) )
        #csvwriter.writerow(item)

my_package = genanki.Package(my_deck)
my_package.media_files = media
my_package.write_to_file(args.deckname + '.apkg')
