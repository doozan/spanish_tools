import argparse
import csv
import spanish_words
import os

parser = argparse.ArgumentParser(description='Fix bad part of speech')
parser.add_argument('infile', help="CSV file to parse, must have columns named 'spanish' and 'pos'")
args = parser.parse_args()

if not os.path.isfile(args.infile):
    print("Cannot open orig file %s"%args.infile, file=sys.stderr)
    exit(1)

pos2nouns = {
    'nm': 'm',
    'nf': 'f',
    'nc': 'mf',
    'nmf': 'm-f',
}

dic2pos = {
"adj": "adj",
"adv": "adv",
"f": "nf",
"fp": "nf",
"m": "nm",
"mf": "nc",
"mp": "nm",
"n": "nm",
"num": "num",
"proverb": "phrase",
"v": "verb",
"vi": "verb",
"vip": "verb",
"vir": "verb",
"vit": "verb",
"vitr": "verb",
"vp": "verb",
"vr": "verb",
"vri": "verb",
"vrp": "verb",
"vrt": "verb",
"vt": "verb",
"vti": "verb",
"vtir": "verb",
"vtp": "verb",
"vtr": "verb",
}

with open(args.infile, newline='') as csvfile:
    csvreader = csv.DictReader(csvfile)

    for row in csvreader:
        results = spanish_words.lookup(row['spanish'])

        if not results:
            #print("Spanish '%s' not found dictionary"%(row['spanish']))
            continue

        pos = row['pos']
        all_pos = results.keys()

        if not ((pos in all_pos) or \
           (pos in ['phrase', 'nf-el', 'nm/f']) or \
           (pos == "v" and any( item[0] == "v" for item in all_pos )) or \
           (pos in pos2nouns and pos2nouns[pos] in all_pos)):

            #print("%s: %s not in %s" % (row['spanish'], pos, all_pos))

            # we have one result, use it
            if len(all_pos) == 1:
                new_pos = dic2pos[list(results)[0]] if list(results)[0] in dic2pos else list(results)[0]
                print("Fixing pos for %s (%s -> %s)"%(row['spanish'], row['pos'], new_pos))
                row['pos'] = new_pos
#            else:
#                print("%s: %s not in %s" % (row['spanish'], pos, all_pos))
