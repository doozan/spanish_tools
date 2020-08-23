import argparse
import zipfile
import json
import sqlite3
import tempfile
import csv
import re
import os


parser = argparse.ArgumentParser(description="Decompile anki deck")
parser.add_argument("infile", help="Anki package to decompile")
parser.add_argument("outdir", help="Destination folder")
args = parser.parse_args()

if not os.path.isfile(args.infile):
    print("Cannot open orig file %s" % args.infile, file=sys.stderr)
    exit(1)

if not os.path.isdir(args.outdir):
    os.mkdir(args.outdir)


myzip = zipfile.ZipFile(args.infile)

tmpdir = tempfile.mkdtemp()
myzip.extract("media", tmpdir)
myzip.extract("collection.anki2", tmpdir)
myzip.extract("collection.anki2", args.outdir)

FILE = os.path.join(tmpdir, "collection.anki2")
conn = sqlite3.connect(FILE)
c = conn.cursor()

c.execute("select decks, models from col where id=1")
row = next(c)
deck_data = json.loads(row[0])
model_data = json.loads(row[1])
json_data = {"deck": deck_data, "model": model_data}

FILE = os.path.join(args.outdir, "deck.json")
with open(FILE, "w") as outfile:
    json.dump(json_data, outfile, indent=4, ensure_ascii=False)


# TODO: get name of notes from json


# get fieldnames from notes
fieldnames = ["guid"]
model_guid = list(model_data.keys())[0]
for field in model_data[model_guid]["flds"]:
    fieldnames.append(field["name"])

FILE = os.path.join(args.outdir, "notes.csv")
with open(FILE, "w") as outfile:
    csvwriter = csv.writer(outfile, lineterminator="\n")
    csvwriter.writerow(fieldnames)

    c.execute("select guid, flds from notes")
    for row in c:
        item = [row[0]] + row[1].split(chr(31))
        csvwriter.writerow(item)

destnames = {}
FILE = os.path.join(tmpdir, "media")
with open(FILE) as jsonfile:
    media = json.load(jsonfile)
    for filename in media.keys():
        destnames[filename] = media[filename]

zipinfos = myzip.infolist()
for item in zipinfos:
    if item.filename in destnames:
        item.filename = destnames[item.filename]
        myzip.extract(item, args.outdir)

conn.close()
os.remove(os.path.join(tmpdir, "media"))
os.remove(os.path.join(tmpdir, "collection.anki2"))
os.rmdir(tmpdir)
