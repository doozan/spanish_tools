import argparse
import zipfile
import json
import sqlite3
import tempfile
import csv
import re
import os

def get_photo_filename(val):
    res = re.search('src=[\'"](.*)[\'"]', val)
    if res:
        return res.group(1)

def get_sound_filename(val):
    res = re.match('\[sound:(.*)\]', val)
    if res:
        return res.group(1)


pos_types = {
    'adj': 'adj',
    'adv': 'adv',
    'art': 'art',
    'conj': 'conj',
    'interj': 'interj',

    "nc": "mf",         # noun takes both m/f without changing meaning (el turista/la turista)
    "nf": "f",          # feminine noun
    "nf el": "f-el",   # feminine noun but uses el (el agua)
    "nm": "m",          # masculine noun
    "nmf": "m-f",       # noun takes both m/f and changes meaning (el cura [priest], la cura [cure])
    'nm/f': 'm/f',     # noun has different m/f forms with same meaning(el doctor, la doctora)

    'num': 'num',
    'prep': 'prep',
    'pron': 'pron',
    'v': 'v',

    'phrase': 'phrase',

    "adj, adv": "adv",
    "adj pron": "pron",
    "adj, pron": "pron",
    "se": "v", #preocupar(se) (v)
    "n": "m",
}

def get_pos(spanish):
    pos = re.search("\((.*?)\)", spanish).group(1)
    if pos in pos_types:
        return pos_types[pos]
    else:
        print("Unknown pos %s in %s" % (pos, spanish))

    return pos

def get_related(spanish,english):
    if "[also " in spanish:
        return re.search("\[also (.*?)\]", spanish).group(1)
    if "[also " in english:
        if "]" not in english:
            return re.search(r"\[also (.*)\b", english).group(1)
        else:
            return re.search("\[also (.*?)\]", english).group(1)
    return ""

def clean_english(text):
    clean = re.sub('&nbsp;', ' ', text)
    clean = re.sub('\[also .*?\]', '', clean)
    clean = re.sub('\<.*?>', '', clean)

    clean = re.sub('\s\s+', ' ', clean)
    clean = re.sub(r'^\s+', '', clean)
    clean = re.sub(r'\s+$', '', clean)
    return clean

def clean_spanish(text):
    clean = re.sub('&nbsp;', ' ', text)
    clean = re.sub(' \+ ', ' ', clean)
    clean = re.sub('\<div>', '', clean)
    clean = re.sub('\</div>', '', clean)
    clean = re.sub('\[.*\]', '', clean)

    clean = re.sub('.*\):', '', clean)  # manifiesto (nm): poner de manifiesto >> "poner de manifiesto"
    clean = re.sub('.*\);', '', clean)  # acuerdo (nm); de acuerdo >> "de acuerdo"

    clean = re.sub('\<br.*$', '', clean)
    clean = re.sub('\(.*$', '', clean)
    clean = re.sub(';.*$', '', clean)
    clean = re.sub(':.*$', '', clean)
    clean = re.sub(',.*$', '', clean)

    clean = re.sub('\s\s+', ' ', clean)
    clean = re.sub(r'^\s+', '', clean)
    clean = re.sub(r'\s+$', '', clean)
    return clean


parser = argparse.ArgumentParser(description='Decompile anki deck')
parser.add_argument('infile', help="Anki package to decompile")
parser.add_argument('outdir', help="Destination folder")
args = parser.parse_args()

if not os.path.isfile(args.infile):
    print("Cannot open orig file %s"%args.infile, file=sys.stderr)
    exit(1)

if not os.path.isdir(args.outdir):
    os.mkdir(args.outdir)

myzip = zipfile.ZipFile(args.infile)

tmpdir = tempfile.mkdtemp()
myzip.extract('collection.anki2', tmpdir)
myzip.extract('media', tmpdir)

fieldnames = ["guid", "rank", "spanish", "pos", "english", "related", "tags", "image", "sound", "sentences"]

with open(args.outdir+'/notes.csv','w') as outfile:
    csvwriter = csv.DictWriter(outfile, fieldnames=fieldnames, lineterminator="\n")
    csvwriter.writeheader()

    filenames = {}

    conn = sqlite3.connect(tmpdir+'/collection.anki2')
    c = conn.cursor()

    c.execute("select decks, models from col where id=1")
    row = next(c)
    deck_data = json.loads(row[0])
    model_data = json.loads(row[1])
    data = { 'deck': deck_data, 'model': model_data }

    # Write csv header from field names
#    fields = [ 'guid' ]
#    model_guid = list(data['model'].keys())[0]
#    for field in data['model'][model_guid]['flds']:
#        fields.append(field['name'])
#    csvwriter.writerow(fields)

    c.execute("select guid, flds from notes")
    for row in c:
        fld = row[1].split(chr(31))

        spanish = clean_spanish(fld[0])

        pos = get_pos(fld[0]) if " " not in spanish else "phrase"

        item = {
            'guid': row[0],
            'rank': fld[4],
            'spanish': spanish,
            'pos': pos,
            'english': clean_english(fld[2]),
            'related': get_related(fld[0], fld[2]),
            'tags': '',
            'image' : '',
            'sound' : '',
        }


        old_filename = get_photo_filename(fld[1])

        # Manual fix for bad entry
        if item['rank'] == "1078":
            old_filename = "paste-81720342740993.jpg"

        if old_filename in filenames:
            item['image'] = filenames[old_filename]
            #print("File referenced mutiple times", fld[1], old_filename, item['spanish'])
        else:
            filenames[old_filename] = item['rank']+".jpg"

        old_filename = get_sound_filename(fld[3])
        if old_filename in filenames:
            item['sound'] = filenames[old_filename]
            #print("File referenced mutiple times", old_filename, item['spanish'])
        else:
            filenames[old_filename] = item['rank']+".mp3"

        csvwriter.writerow(item)


    destnames = {}
    with open(tmpdir+'/media') as jsonfile:
        media = json.load(jsonfile)
        for filename in media.keys():
            destnames[filename] = media[filename]
            if media[filename] in filenames:
                destnames[filename] = filenames[media[filename]]
            else:
                destnames[filename] = media[filename]
                print("Unreferenced file:", filename, media[filename])

    zipinfos = myzip.infolist()
    for item in zipinfos:
        if item.filename in destnames:
            item.filename = destnames[item.filename]
            myzip.extract(item, args.outdir)

    with open(args.outdir+'/deck.json','w') as outfile:
        json.dump(data, outfile, indent=4, ensure_ascii=False )

    conn.close()
    os.remove(tmpdir+'/media')
    os.remove(tmpdir+'/collection.anki2')
    os.rmdir(tmpdir)

