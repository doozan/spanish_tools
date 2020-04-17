import argparse
import zipfile
import json
import sqlite3
import tempfile
import csv
import re
import os


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

FILE=os.path.join(tmpdir, 'collection.anki2')
conn = sqlite3.connect(FILE)
c = conn.cursor()

c.execute("select decks, models from col where id=1")
row = next(c)
deck_data = json.loads(row[0])
model_data = json.loads(row[1])
json_data = { 'deck': deck_data, 'model': model_data }

FILE=os.path.join(args.outdir, 'deck.json')
with open(FILE,'w') as outfile:
    json.dump(json_data, outfile, indent=4, ensure_ascii=False )

exit()


# TODO: get name of notes from json
# TODO: get fieldnames from notes

fieldnames = ["guid", "rank", "spanish", "pos", "english", "related", "tags", "image", "sound", "sentences"]

FILE=os.path.join(args.outdir, 'notes.csv')
with open(FILE,'w') as outfile:
    csvwriter = csv.DictWriter(outfile, fieldnames=fieldnames, lineterminator="\n")
    csvwriter.writeheader()

    filenames = {}


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
    FILE=os.path.join(tmpdir, 'media')
    with open(FILE) as jsonfile:
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

    conn.close()
    os.remove(os.path.join(tmpdir, '/media'))
    os.remove(os.path.join(tmpdir, '/collection.anki2'))
    os.rmdir(tmpdir)

