import genanki
import csv
import os.path
import math
import json
import re
import spanish_sentences


pos_types = {
    'phrase': 'phrase',
    'adj': 'adj',
    'adj, adv': 'adj',
    'adj, pron': 'adj',
    'adv': 'adv',
    'art': 'det',
    'conj': 'conj',
    'interj': 'intj',
    'nc': 'noun',
    'nf': 'noun',
    'nf-el': 'noun',
    'nm': 'noun',
    'nmf': 'noun',
    'nm/f': 'noun',
    'num': 'num',
    'prep': 'adp',
    'pron': 'pron',
    'v': 'verb',
}


def format_sentences(sentences):
    return "\n".join( '<br><span class="spa">%s</span><br><span class="eng">%s</span>' % pair[:2] for pair in sentences )

def get_sentences(lookup, pos, count):
    results = spanish_sentences.get_sentences(lookup, pos, count)

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

with open('spanish_5000.json') as jsonfile:
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
    return pos in [ "nf", "nm", "nc", "nm/f", "nmf", "nf-el" ]

def get_article(pos):
    if pos in [ "nf" ]:
        return "la"
    elif pos in [ "nm", "nc", "nm/f", "nmf", "nf-el" ]:
        return "el"
    return ""


def format_spanish(item):
    return "%s (%s)" % (item['spanish'], item['pos'])

def format_english(item):
    if item['related'] != "":
        return "%s [also %s]" % (item['english'], item['related'])
    return item['english']


my_deck = genanki.Deck(int(deck_guid),'Spanish top 5000-revised', "5000 common Spanish words")

media = []
notes = []

fieldnames = [ "Spanish", "Picture", "English", "Audio", "Ranking", "tag", "Part of speech", "Spanish word with article", "Simple example sentences" ]

with open('spanish_5000.csv', newline='') as csvfile, open('spanish_5000_rebuild.csv', 'w', newline='') as outfile:
    csvreader = csv.DictReader(csvfile)
    csvwriter = csv.DictWriter(outfile, fieldnames=fieldnames)
    csvwriter.writeheader()

    for row in csvreader:
        image = row['image'] if row['image'] != "" else row['rank'] + ".jpg"
        sound = row['sound'] if row['sound'] != "" else row['rank'] + ".mp3"

        item = {
            'Spanish': format_spanish(row),
            'Picture': format_image(image),
            'English': format_english(row),
            'Audio':   format_sound(sound),
            'Ranking': row['rank'],
            'tag':     '',
            'Part of speech': row['pos'],
            'Spanish word with article': row['spanish'] if not is_noun(row['pos']) else get_article(row['pos']) + " " + row['spanish'],
            'Simple example sentences': get_sentences(row['spanish'], row['pos'], 3)
        }

        # manually fix this id since libreoffice overwrites the value with #NAME because it hates things that start with =
        guid = row['guid'] if row['guid'] != '#NAME?' else '=mm:yng9n'

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

        row = []
        for field in fieldnames:
            row.append(item[field])

        my_deck.add_note( genanki.Note( model = card_model, sort_field=row[4], fields = row, guid = guid, tags = tags ) )
        csvwriter.writerow(item)

my_package = genanki.Package(my_deck)
my_package.media_files = media
my_package.write_to_file('spanish_top_5000_revised.apkg')
