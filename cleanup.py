import csv
import re
import os
import sys
import argparse
import spanish_words
import spanish_sentences

parser = argparse.ArgumentParser(description='Check word list for mistakes')
parser.add_argument('infile', help="Wordlist to check")
parser.add_argument('outfile', help="Wordlist to write to")
parser.add_argument('--basefile', help="Use words included in basefile when flagging duplicate or repeat words")
parser.add_argument('--onlyclean', action='store_true', help="Only write unflagged words to outfile")
parser.add_argument('--console', action='store_true', help="Write flagged words to console")
parser.add_argument('--all', action='store_true', help="Run all checks" )
parser.add_argument('--dup', action='store_true', help="Flag duplicate word+pos")
parser.add_argument('--repeat', action='store_true', help="Flag words that repeat with a different POS")
parser.add_argument('--nodef', action='store_true', help="Flag words without a definition")
parser.add_argument('--wrongpos', action='store_true', help="Flag words that only have definitions for a different POS")
parser.add_argument('--nosent', action='store_true', help="Flag words without sentences")
parser.add_argument('--fuzzysent', action='store_true', help="Flag words with fuzzy-matched sentences")
parser.add_argument('--showdef', action='store_true', help="Include definitions for all tagged words")
parser.add_argument('--showsent', action='store_true', help="Include definitions for all tagged words")
args = parser.parse_args()

if args.all:
    args.dup = True
    args.repeat = True
    args.nodef = True
    args.wrongpos = True
    args.nosent = True
    args.fuzzysent = True


if not (args.dup or args.repeat or args.nodef or args.wrongpos or args.nosent or args.fuzzysent):
    print("You didn't specify anything to flag")
    exit(1)


words = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt", synonyms="spanish_data/synonyms.txt", iverbs="spanish_data/irregular_verbs.json")
spanish_sentences = spanish_sentences.sentences("spanish_data/spanish.json")

def format_def(item):
    result = ""
    for pos in item:
        prefix = "[%s]: " % pos
        for tag in item[pos]:
            if result != "":
                result += "\n"
            result += prefix
            defs = spanish_words.get_best_defs(item[pos][tag],4)
            usage = spanish_words.defs_to_string(defs, pos)

            if tag == "x":
                result += usage
            else:
                result += "%s: %s" % (tag, usage)
    return result

def format_sentences(sentences):
    return "\n".join('spa: %s\neng: %s' % pair[:2] for pair in sentences )


seen = {}
seenword = {}
if args.basefile:
    with open(args.basefile) as infile:
        csvreader = csv.DictReader(infile)
        fields = csvreader.fieldnames
        for row in csvreader:
            word = row['spanish'].lower()
            pos = row['pos'].lower()

            seen[pos+":"+word] = 1
            if word in seenword:
                seenword[word] += "-" +pos
            else:
                seenword[word] = pos



with open(args.infile) as infile, open(args.outfile,'w') as outfile:
    csvreader = csv.DictReader(infile)
    fields = csvreader.fieldnames

    # If we're only printing clean lines, don't add new headers
    if not (args.onlyclean):
        if "_flags" not in fields:
            fields.append("_flags")
        if (args.showdef) and "_definition" not in fields:
            fields.append("_definition")
        if (args.showdef) and "_sentences" not in fields:
            fields.append("_sentences")

    csvwriter = csv.DictWriter(outfile, fieldnames=fields)
    csvwriter.writeheader()

    for row in csvreader:

        flags = []
        word = row['spanish'].lower()
        pos = row['pos'].lower()

        if (args.dup):
            if pos+":"+word in seen:
                flags.append("dup")
            else:
                seen[pos+":"+word] = 1

        if (args.repeat):
            if word in seenword:
                flags.append( "repeat-" + seenword[word] )
                seenword[word] += "-" +pos
            else:
                seenword[word] = pos

        newpos = pos

        deftext = ""
        definition = words.lookup(word,pos.lower())
        if not definition:
            if (args.nodef):
                flags.append("nodef")

            if (args.wrongpos):
                definition = words.lookup(word)
                if len(definition):
                    flags.append("wrongpos-" + "-".join(definition.keys()))

        if (args.showdef):
            definition = words.lookup(word)
            deftext = format_def(definition)

#        if pos == "VERB" and word.endswith("se"):
#            definition = words.lookup(word[:-2],"verb")
#            deftext = format_def(definition)
#            definition = words.lookup(word,"verb")
#            deftext += "###########\n"+ format_def(definition)
#            flags.append("reflexive")


        matches = spanish_sentences.get_sentences(word,newpos,3)
        if not len(matches['sentences']):
            if (args.nosent):
                flags.append("nosent")

        elif matches["matched"] == "fuzzy":
            flags.append("fuzzy_sentences")



        if (args.onlyclean):
            if len(flags):
                continue
        else:
            row['_flags'] = " ".join(flags)

        if args.showdef:
            if len(flags):
                definition = words.lookup(word,pos.lower())
                row['_definition'] = format_def(definition)
            else:
                row['_definition'] = ""

        if args.showsent:
            if len(flags):
                matches = spanish_sentences.get_sentences(word,newpos,3)
                row['_sentences'] = format_sentences(matches)
            else:
                row['_sentences'] = ""



        if (args.console) and len(flags):
            print("%s, %s = %s" %(word, pos, " ".join(flags)))


        csvwriter.writerow(row)
