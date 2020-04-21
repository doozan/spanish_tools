import glob
import sys
import os
import re

lemmadb = {}

srcdir = os.path.dirname(__file__)
fileglob = os.path.join(srcdir, '*.txt')

files = [ f for f in glob.glob( fileglob ) if os.path.isfile(f) ]
# always load custom.txt last, so we can overwrite existing data
if "custom.txt" in files:
    files.remove("custom.txt")
    files.append("custom.txt")

if not len(files):
    print("No text files in %s"%srcdir, file=sys.stderr)
    print("Download lemmas from https://github.com/ChatScript/ChatScript/blob/master/DICT/SPANISH/", sys.stderr)
    exit(1)


desc2pos = {
'ADVERB': 'ADV',
'ADJECTIVE': 'ADJ',
'ADJECTIVE_NUMBER': 'ADJ',
'CONJUNCTION_COORDINATE': 'CONJ',
'CONJUNCTION_SUBORDINATE': 'CONJ',
'DETERMINER': 'DET',
'NOUN': 'NOUN',
'NOUN_GERUND': 'NOUN',
'NOUN_NUMBER': 'NOUN',
'NOUN_PLURAL': 'NOUN',
'NOUN_PROPER_PLURAL': 'NOUN',
'NOUN_PROPER_SINGULAR': 'NOUN',
'NOUN_SINGULAR': 'NOUN',
'PREPOSITION': 'PREP',
'PRONOUN_OBJECT': 'PRON',
'PRONOUN_SUBJECT': 'PRON',
'VERB': 'VERB',
'VERB_INFINITIVE': 'VERB',
'VERB_PAST_PARTICIPLE': 'VERB'
}



# sample file data
# casada ( VERB_PAST_PARTICIPLE VERB ADJECTIVE ) lemma=`casado`casar` ADJ  VLadj
# niño ( NOUN NOUN_SINGULAR NOUN_PLURAL )
# niños ( NOUN NOUN_SINGULAR NOUN_PLURAL ) lemma=`niño` NC
# poniéndose ( VERB_PAST_PARTICIPLE NOUN VERB NOUN_GERUND ) lemma=`poner`poner` VCLIger  VLadj
# verde ( NOUN ADJECTIVE NOUN_SINGULAR NOUN_PLURAL ) lemma=`verde`verde` ADJ  NC
# vete ( VERB ) lemma=`ir|ver`vetar` VCLIfin  VLfin


#tags = {}
words = {}
for _file in files:
    with open(_file) as infile:
        for line in infile:
            res = re.match(" (.*) \( (.*)?\)( lemma=`(.*)` (.*))?", line)
            if not res:
                continue

            word = res.group(1)
            if len(res.group(2)):
                words[word] = [ desc2pos[x] for x in res.group(2).strip().split(" ") ]
            #pos = res.group(2).strip().split(" ")

            lemmas = res.group(4).strip().split('`') if res.group(4) else []
            lemmas_pos = res.group(5).strip().split("  ") if res.group(4) else []
            lemmadict = dict(zip(lemmas_pos, lemmas))
            for oldpos in lemmas_pos:
                newpos = ""
                if oldpos[0] == "V":
                    newpos = "VERB"
                elif oldpos in [ "NC", "NM", "NMEA" ]:
                    newpos = "NOUN"
                else:
                    continue
                if newpos in lemmadict and lemmadict[newpos] != lemmadict[oldpos]:
                    lemmadict[newpos] += "|" + lemmadict.pop(oldpos)
                else:
                    lemmadict[newpos] = lemmadict.pop(oldpos)

            lemmadb[word] = lemmadict

#print(sorted(tags.keys()))
#        lemmadb = dict([line.split() for line in infile])

def get_lemma(item,pos):
    if item in lemmadb:
        if pos in lemmadb[item]:
            return lemmadb[item][pos]
        else:
            keys = list(lemmadb[item].keys())
            if len(keys):
                return lemmadb[item][keys[0]]

def get_lemmas(item):
    if item in lemmadb:
        return lemmadb[item]


def get_all_pos(word):
    if word in words:
        # Filter duplicates, but preserve order of list
        unique = []
        for item in words[word]:
            if item not in unique:
                unique.append(item)
    return []
