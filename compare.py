import csv
import os
import sys
import argparse
#import spanish_words

parser = argparse.ArgumentParser(description='Compare two wordlists and merge into a third')
parser.add_argument('file1', help="Primary wordlist")
parser.add_argument('file2', help="Words to compare against")
#parser.add_argument('outfile', help="Target file")
args = parser.parse_args()

def format_def(item):
    result = ""
    for pos in item:
        prefix = "[%s]: " % pos
        for tag in item[pos]:
            if result != "":
                result += "\n"
            result += prefix
            defs = spanish_dictionary.get_best_defs(item[pos][tag],4)
            usage = spanish_dictionary.defs_to_string(defs, pos)

            if tag == "x":
                result += usage
            else:
                result += "%s: %s" % (tag, usage)
    return result

def format_sentences(sentences):
    return "\n".join('spa: %s\neng: %s' % pair[:2] for pair in sentences )



cleanpos = {
    "m": "noun",
    "f": "noun",
    "mf": "noun",
    "f-el": "noun",
    "m-f": "noun",
    "m/f": "noun",

    'v': 'verb',
}

lists = {}

def get_tag(item):
    #pos = cleanpos[row['pos']] if row['pos'] in cleanpos else row['pos']
    #return pos.lower() +":"+ item['spanish'].lower()
    return item['spanish'].lower()


for filename in [ args.file1, args.file2 ]:
    with open(filename) as infile:
        csvreader = csv.DictReader(infile)
        listtag = filename
        lists[listtag] = {}
        for row in csvreader:
            pos = cleanpos[row['pos']] if row['pos'] in cleanpos else row['pos']
            pos = pos.lower()
            tag = row['spanish'].lower()
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
    print("~ %s %s -> %s"%(k, lists[list1][k], lists[list2][k]))

for k in lists[list1].keys() - lists[list2].keys():
    print("- %s%s" %(k, lists[list1][k]))

for k in lists[list2].keys() - lists[list1].keys():
    print("+ %s%s" %(k, lists[list2][k]))


exit()

with open(args.file2) as infile:
    csvreader = csv.DictReader(infile)
    listtag = "2"
    lists[listtag] = {}
    for row in csvreader:
#        if row['rank'] not in ["x", "dup", "nosent", "nodef"]:
            tag = get_tag(row)
#            merged[tag] = 'common' if tag in merged else "2"
            lists[listtag][tag] = row




for wordtag,listtag in merged.items():
    if listtag != 'common':
        item = lists[listtag][wordtag]
        pos,word = wordtag.split(":")
        print(",".join([
              listtag,
#              item['rank'],
              word,
              pos,
            ]))
exit()
seen = {}

with open(args.file1) as infile, open(args.outfile,'w', newline='') as outfile:
    csvreader = csv.DictReader(infile)
    fields = csvreader.fieldnames
    for newfield in [ "guid", "oldrank" ]:
        if newfield not in fields:
            fields =+ newfield
    csvwriter = csv.DictWriter(outfile, fieldnames=fields)
    csvwriter.writeheader()

    for row in csvreader:
        tag = get_tag(row)
        flags = []
        word = row['spanish']
        #row['flags'].split(" ")

        row['flags'] = ""
        row['deftext'] = ""

        if row['rank'] in ['x','dup','nosent']:
#            csvwriter.writerow(row)
            continue

        if word in seen:
            flags.append("repeat")
        else:
            seen[word] = 1

#        csvwriter.writerow(row)


    with open(args.file2) as infile2:
        csvreader2 = csv.DictReader(infile2)
        for row in csvreader2:
            item = {}
            if row['rank'] in ["x", "dup", "nosent", "nodef"]:
                continue
            tag = get_tag(row)
            word = row['spanish']
            pos = row['pos']
            if merged[tag] != "common":
                item['deftext'] = format_def(spanish_dictionary.lookup(word))

                if word in seen:
                    item['flags'] = "repeat"
                else:
                    seen[word] = 1

                for k in [ "rank", "spanish", "pos" ]:
                    item[k] = row[k]

                csvwriter.writerow(item)


#    with open(args.file1) as infile:
#        csvreader = csv.DictReader(infile)
#        for line in csvreader:

