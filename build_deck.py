import genanki
import csv
import os.path
import math
import json
import re
import spanish_dictionary
import spanish_sentences


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
    "f": "la",
    "mf": "el/la",
    "f-el": "el",
    "m-f": "el",
    "m/f": "el"
}
pos_nouns = list(noun_articles.keys())



def format_sentences(sentences):
    return "<br>\n".join( '<span class="spa">%s</span><br><span class="eng">%s</span>' % pair[:2] for pair in sentences )

def get_sentences(item, count):

    # if there's already a value, use that
    if item['sentences'] != '':
        return item['sentences']

    results = spanish_sentences.get_sentences(row['spanish'], pos_types[row['pos']], count)

    if len(results['sentences']):
        return format_sentences(results['sentences'])

    return ""


# genanki 0.8.0
# override the genanki function so we can set sortf
#
def new_to_json(self, now_ts, deck_id):
    for ord_, tmpl in enumerate(self.templates):
      tmpl['ord'] = ord_
      tmpl.setdefault('bafmt', '')
      tmpl.setdefault('bqfmt', '')
      tmpl.setdefault('did', None)  # TODO None works just fine here, but should it be deck_id?

    for ord_, field in enumerate(self.fields):
      field['ord'] = ord_
      field.setdefault('font', 'Liberation Sans')
      field.setdefault('media', [])
      field.setdefault('rtl', False)
      field.setdefault('size', 20)
      field.setdefault('sticky', False)

    return {
      "css": self.css,
      "did": deck_id,
      "flds": self.fields,
      "id": str(self.model_id),
      "latexPost": "\\end{document}",
      "latexPre": "\\documentclass[12pt]{article}\n\\special{papersize=3in,5in}\n\\usepackage{amssymb,amsmath}\n"
                  "\\pagestyle{empty}\n\\setlength{\\parindent}{0in}\n\\begin{document}\n",
      "mod": now_ts,
      "name": self.name,
      "req": self._req,
      #"sortf": 0,
      "sortf": 4,
      "tags": [],
      "tmpls": self.templates,
      "type": self.model_type,
      "usn": -1,
      "vers": []
    }

# override the json generator so we can explicitly set the sortf field
old_to_json = genanki.Model.to_json
genanki.Model.to_json = new_to_json

with open('deck.json') as jsonfile:
    data = json.load(jsonfile)

model_guid = list(data['model'].keys())[0]
model_name = data['model'][model_guid]['name']
deck_guid = [ item for item in data['deck'] if item != '1' ][0]

custom_css = """
.spa { font-weight: bold; }
.eng { font-style: italic; font-size: .8em }"""

# Create a template for anki card
card_model = genanki.Model(model_guid,
  model_name,
  fields=data['model'][model_guid]['flds'],
  templates=data['model'][model_guid]['tmpls'],
  css=data['model'][model_guid]['css'] + custom_css
)


def format_sound(filename):
    return "[sound:%s]"%filename

def format_image(filename):
    return '<img src="%s" />'%filename

def is_noun(pos):
    return pos in pos_nouns

def get_article(pos):
    return noun_articles[pos]


def format_spanish(item):
    return "%s (%s)" % (item['spanish'], item['pos'])

def get_definition(word, pos):
    item = spanish_dictionary.lookup(word, pos)

    result = ""
    for pos in item:
        pos_tag = ""
        if len(item.keys()) > 1:
            pos_tag = '<span class="pos-%s">{%s} </span>'%(pos,pos)

        for tag in item[pos]:
            if result != "":
                result += "<br>\n"

            result += pos_tag

            defs = spanish_dictionary.get_best_defs(item[pos][tag],4)
            usage = spanish_dictionary.defs_to_string(defs, pos)

            if tag != "x":
                result += '<span class="usage-tag">[%s]: </span>'%tag

            result += '<span class="usage">%s</span>'%usage
    return result


def get_english(item):
    #english = item['english']

    #if english == "":
    #    english = get_definition(item['spanish'], pos_types[item['pos']])

    english = get_definition(item['spanish'], pos_types[item['pos']])
    if english == "":
        english = item['english']

    if item['related'] != "":
        english += " [also %s]" % item['related']

    return english


my_deck = genanki.Deck(int(deck_guid),'Spanish top 5000-revised', "5000 common Spanish words")

media = []
notes = []

fieldnames = [ "Spanish", "Picture", "English", "Audio", "Ranking", "tag", "Part of speech", "Spanish word with article", "Simple example sentences" ]

with open('notes.csv', newline='') as csvfile, open('notes_rebuild.csv', 'w', newline='') as outfile:
    csvreader = csv.DictReader(csvfile)
    csvwriter = csv.DictWriter(outfile, fieldnames=fieldnames)
    csvwriter.writeheader()

    for row in csvreader:
        image = row['image'] if row['image'] != "" else row['rank'] + ".jpg"
        sound = row['sound'] if row['sound'] != "" else row['rank'] + ".mp3"

        item = {
            'Spanish': format_spanish(row),
            'Picture': format_image(image),
            'English': get_english(row),
            'Audio':   format_sound(sound),
            'Ranking': row['rank'],
            'tag':     '',
            'Part of speech': row['pos'],
            'Spanish word with article': row['spanish'] if not is_noun(row['pos']) else get_article(row['pos']) + " " + row['spanish'],
            'Simple example sentences': get_sentences(row, 3)
        }

        # guid should be None if empty so generator will create one
        guid = row['guid'] if row['guid'] != "" else None
        # manually fix this id since libreoffice overwrites the value with #NAME because it hates things that start with =
        if guid == '#NAME?':
            guid = '=mm:yng9n'

        tags = [ row['pos'],str(math.ceil(int(row['rank']) / 500)*500) ]
        if row['tags'] != "":
            for tag in row['tags'].split(" "):
                tags.append(tag)

        if os.path.isfile(image):
            media.append(image)
        else:
            item['Picture'] = ""
            print("Skipping missing pic",image,row['rank'],row['spanish'])

        if os.path.isfile(sound):
            media.append(sound)
        else:
            item['Picture'] = ""
            print("Skipping missing pic",sound)

        for key in [ "Spanish", "English", "Part of speech" ]:
            if item[key] == "":
                print("Missing %s from %s %s" % (key, row['rank'], row['spanish']))

        row = []
        for field in fieldnames:
            row.append(item[field])

        my_deck.add_note( genanki.Note( model = card_model, sort_field=row[4], fields = row, guid = guid, tags = tags ) )
        csvwriter.writerow(item)

my_package = genanki.Package(my_deck)
my_package.media_files = media
my_package.write_to_file('deck.apkg')
