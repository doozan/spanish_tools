import csv
import argparse

parser = argparse.ArgumentParser(description="Compare two wordlists")
parser.add_argument("file1", help="Primary wordlist")
parser.add_argument("file2", help="Words to compare against")
args = parser.parse_args()

cleanpos = {
    "m": "noun",
    "f": "noun",
    "mf": "noun",
    "f-el": "noun",
    "m-f": "noun",
    "m/f": "noun",
    "v": "verb",
}

lists = {}

for filename in [args.file1, args.file2]:
    with open(filename) as infile:
        csvreader = csv.DictReader(infile)
        listtag = filename
        lists[listtag] = {}
        for row in csvreader:
            pos = cleanpos.get(row["pos"], row["pos"])
            pos = pos.lower()
            tag = row["spanish"].lower()
            if tag not in lists[listtag]:
                lists[listtag][tag] = []
            if pos not in lists[listtag][tag]:
                lists[listtag][tag].append(pos)


new_pos = {}
list1 = args.file1
list2 = args.file2

overlap = lists[list1].keys() & lists[list2].keys()
for k in overlap:
    if lists[list1][k] != lists[list2][k]:
        new_pos[k] = 1

for k in new_pos:
    print("~ %s %s -> %s" % (k, lists[list1][k], lists[list2][k]))

for k in lists[list1].keys() - lists[list2].keys():
    print("- %s%s" % (k, lists[list1][k]))

for k in lists[list2].keys() - lists[list1].keys():
    print("+ %s%s" % (k, lists[list2][k]))
