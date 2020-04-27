from collections import defaultdict
from .lemmas import SpanishLemmas
import re
import sys
import os

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def fail(*args, **kwargs):
    eprint(*args, **kwargs)
    exit(1)


def parse_spanish(data):

    res = re.match("^(.*) ?\{(.*?)\} ?\[?([^\]]*)\]?", data)

    # This only applies to 4 obscure entries in the database
    # better to just delete the bad lines
    if not res:
        print("DOES NOT MATCH REGEX: '%s'"% data)
        return {}

    tags = []
    if res.group(3) != "":
        tags = [ item.strip() for item in res.group(3).split(',') ]

    return {
        'lemma': res.group(1).strip(),
        'pos': res.group(2),
        'tags': tags
    }

def parse_line(line):
    esp, eng = line.split("::")
    return {
       'esp': parse_spanish(esp),
       'eng': eng.strip()
    }

def pos_is_verb(pos):
    return pos.startswith("v")

noun_tags = set([
    "n",    # noun (very few cases, mainly just cruft in wiktionary)
    "f",    # feminine (casa)
    "fp",   # feminine always plural (uncommon) (las esposas - handcuffs)
    "fs",   # feminine singular - not used (wiktionary crufy)
    "m",    # masculine (frijole)
    "mf",   # uses el/la to indicate gender of person (el/la dentista)
    "mp",   # masculine plural, nouns that are always plural (lentes)
    "ms",   # masculine singular - not used (more cruft)

    # These don't appear in the dictionary, but are generated during word analysis
    "m-f",  # uses el/la to indigate different meanings of word (la cura, el cura)
    "f-el", # feminine, but uses "el" when singular
    "m/f"   # part of a masculine/feminine noun pair (amigo/amiga)
])

def pos_is_noun(pos):
    if pos in noun_tags:
        return True

def common_pos(pos):
    if not pos:
        return

    if pos_is_verb(pos):
        return "verb"
    if pos_is_noun(pos):
        return "noun"

    return pos.lower()

def strip_eng_verb(eng):
    if eng.startswith("to "):
        return eng[3:]
    return eng

def should_ignore(item):
    if {"archaic", "dated", "historical", "obsolete", "rare"} & { tag.lower() for tag in item['tags'] }:
        return True

    return False


el_f_nouns = [ 'acta', 'agua', 'ala', 'alba', 'alma', 'ama', 'ancla', 'ansia', 'area',
        'arma', 'arpa', 'asma', 'aula', 'habla', 'habla', 'hacha', 'hambre', 'águila']


# splits a list by comma, but with awareness of ()
# split_defs("one, two (2, II), three") will result in
# [ "one", "two (2, II)", "three" ]
def split_def(data):
    splits=[]
    nested=0

    last_split=0

    for idx in range(0,len(data)):
        c = data[idx]
        if c == "(" or c == "[":
            nested += 1
        elif c == ")" or c == "]":
            nested = nested-1 if nested else 0
        elif c == "," and not nested:
            splits.append(data[last_split:idx].strip())
            last_split=idx+1

    if idx>last_split:
        splits.append(data[last_split:idx+1].strip())

    return splits



def lines_to_usage(items):
    usage = {}

    for item in items:
        if should_ignore(item['esp']):
            continue

        pos = item['esp']['pos']
        if pos not in usage:
            usage[pos] = {}

        tag = "x"
        if len(item['esp']['tags']):
            tag = ", ".join(item['esp']['tags'])
        if tag not in usage[pos]:
            usage[pos][tag] = []

        # Definitions are separated by commas and semicolons
        for defs in item['eng'].split("; "):
            is_new_def=True
            for eng in split_def(defs):
                if pos_is_verb(pos):
                    eng = strip_eng_verb(eng)
                if is_new_def:
                    eng = ";" + eng

                if eng not in usage[pos][tag]:
                    usage[pos][tag].append(eng)
                is_new_def = False
    return usage

# "primary" defs start with a ';' and synonyms follow
# for word with many definitons this can be too much info

# given the following input:
# [ ";def1", "def1-syn1", "def1-syn2", ";def2", ";def3", "def3-syn1" ]
# limit=2 gives [ ";def1", ";def2" ]
# limit=4 gives [ ";def1", "syn1-1", ";def2", ";def3" ]
# limit=5 gives [ ";def1", "syn1-1", ";def2", ";def3", "def3-syn1" ]


def get_best_defs(defs,limit):
    best = []

    if len(defs) <= limit:
        return defs

    #primary_defs = [ x[1:] for x in defs if x.startswith(';') ]

    # number of primary defs >= limit just return first limit defs
    #if len(primary_defs) >= limit:
    #    return primary_defs[:limit]

    # only one primary def, just return the first limit defs
    #elif len(primary_defs) == 1:
    #    return defs[:limit]

    # otherwise, build a list of defs to keep starting with primary defs
    # then the first syn of each def
    # then the second...
    # until we've hit the limit of keepers
    # Since it's important to keep the primary def and the synonyms together
    # we build a list of keepers by their index and then sort that index to
    # get things in the correct order

    keepidx = []
    keep_depth = 0

    while len(keepidx) < limit:
        cur_depth=0
        index=0
        for item in defs:
            if item.startswith(';'):
                cur_depth=0
            else:
                cur_depth += 1

            if cur_depth == keep_depth:
                keepidx.append(index)
                if len(keepidx) >= int(limit):
                    break
            index += 1
        keep_depth += 1
        if keep_depth > 3:
            break;

    keepers = []
    for idx in sorted(keepidx):
        keepers.append(defs[idx])

    return keepers

def defs_to_string(defs, pos):
    usage = ""
    if pos_is_verb(pos):
        usage = "to "

    first=True
    for item in defs:
        sep=','
        word = item
        if item.startswith(';'):
            sep=';'
            word=item[1:]

        if not first:
            usage += sep+" "+word
        else:
            usage += word
            first=False

    return usage

def filter_def_phrase(defs, phrase):

    if not phrase or phrase == "":
        return defs

    return [ d for d in defs if phrase not in d['eng'] ]


def filter_def_pos(defs, pos):

    if not pos or pos == "":
        return defs

    # do pos filtering
    filtered = []
    for item in defs:
        item_pos = item['esp']['pos']
        if (pos == "verb" and pos_is_verb(item_pos)) or \
           (pos == "noun" and pos_is_noun(item_pos)) or \
           (pos == item_pos):
               filtered.append(item)
    if not len(filtered):
        removed = [ item['esp']['pos'] for item in defs ]
        #print("%s: %s not in %s" % (word,pos, removed))

    return filtered



class SpanishWords:
    def __init__(self, dictionary, synonyms, iverbs):
        self.allverbs = {}
        self.allwords = {}
        self.allsyns = {}
        self.wordpos = {}
        self.nouns_ending_s = {}
        self.irregular_verbs = {}
        self.reverse_irregular_verbs = defaultdict(list)

        self.init_dictionary(dictionary)
        self.init_syns(synonyms)
        self.lemmas = lemmas.SpanishLemmas(self, iverbs)


    def init_dictionary(self, datafile):
        if not os.path.isfile(datafile):
            fail("Cannot open dictionary:", datafile)

        with open(datafile) as infile:
            for line in infile:
                res = re.match("^([^{]+)(?:{([a-z]+)})?", line)
                word = res.group(1).strip()
                pos = common_pos(res.group(2))

                if pos and pos == "verb":
                    self.allverbs[word] = 1
                elif pos and pos == "noun" and word[-1:] == "s":
                    self.nouns_ending_s[word] = 1
                if word not in self.allwords:
                    self.allwords[word] = []

                self.allwords[word].append(line)

                if word not in self.wordpos:
                    self.wordpos[word] = []

                if pos not in self.wordpos[word]:
                    self.wordpos[word].append(pos)

        if not os.path.isfile(datafile + ".custom"):
            return

        with open(datafile+".custom") as infile:
            for line in infile:
                if line.startswith("#"):
                    continue

                word = re.match("^([^{]+)", line).group(1)
                word = word.strip()

                if word.startswith("-"):
                    word = word[1:]
                    self.delete_entries(word, line[1:])
                    continue

                if word not in self.allwords:
                    self.allwords[word] = [line]
                else:
                    self.allwords[word].append(line)


    def init_syns(self, datafile):
        if not os.path.isfile(datafile):
            fail("Cannot open synonyms:", datafile)

        with open(datafile) as infile:
            for line in infile:
                word, syns = line.split(':')
                syns = syns.strip()
                self.allsyns[word] = syns # syns.split('/')

    def delete_entries(self, word, line):
        if word not in self.allwords:
            return

        line = line.strip()
        self.allwords[word] = [ v for v in self.allwords[word] if not v.startswith(line) ]

    def get_all_pos(self, word):
        if word not in self.wordpos:
            return []
        return self.wordpos[word]

    def is_verb(self, word):
        return 'verb' in self.get_all_pos(word)

    def do_analysis(self, word, items):

        usage = lines_to_usage(items)

        if len( {"m","f","mf"} & usage.keys() ) > 1:
    #    if "m" in usage and "f" in usage:
            usage['m-f'] = {}
            for oldtag in ['m', 'f', 'mf']:
                if oldtag in usage:
                    for tag in usage[oldtag].keys():
                        newtag = oldtag + ' ' + tag if tag != 'x' else oldtag
                        usage['m-f'][newtag] = usage[oldtag][tag]
                    del usage[oldtag]

        elif "f" in usage and word in el_f_nouns:
            usage["f-el"] = usage.pop("f")

        elif "m" in usage:

            # If this has a "-a" feminine counterpart, reclassify the "m" defs as "m/f"
            # and add any feminine definitions (ignoring the "feminine noun of xxx" def)
            femnoun = self.get_feminine_noun(word)
            if femnoun:
                femdefs = self.get_all_defs(femnoun)
                femdefs = filter_def_pos(femdefs, "f")
                femdefs = filter_def_phrase(femdefs, "feminine noun of "+word)
                femusage = lines_to_usage(femdefs)
#                for k in list(femusage['f'].keys()):
#                    if ";feminine noun of " + word in femusage['f'][k]:
#                        del femusage['f'][k] #.remove(";feminine noun of " + word)
#                        if not(len(femusage['f'][k])):
#                            del femusage['f'][k]

                if 'f' in femusage and len(femusage['f'].keys()):
                    usage['f'] = femusage['f']
                    usage['m/f'] = {}

                    for oldtag in ['m', 'f']:
                        for tag in usage[oldtag].keys():
                            newtag = oldtag + ' ' + tag if tag != 'x' else oldtag
                            usage['m/f'][newtag] = usage[oldtag][tag]
                        del usage[oldtag]
                else:
                    usage['m/f'] = usage.pop('m')

        return usage


    def get_synonyms(self, word):
        if word in self.allsyns and self.allsyns[word]:
            return self.allsyns[word].split('/')
        else:
            return []

    def get_raw_defs(self, word):
        return self.allwords[word] if word in self.allwords else []

    def get_all_defs(self, word):
        return [ parse_line(x) for x in self.get_raw_defs(word) ]


    def lookup(self, word, pos=""):
        pos = pos.lower()

        defs = self.get_all_defs(word)
        filtered = filter_def_pos(defs, pos)

        analysis = self.do_analysis(word, filtered)
        return analysis

    def get_lemma(self, word, pos):
        return self.lemmas.get_lemma(word, pos)


    def is_feminized_noun(self, word, masculine):
        if not word.endswith("a"):
            return

        defs = self.get_all_defs(word)
        for item in defs:
            if item['esp']['pos'] == 'f':
                if "feminine noun of "+masculine in item['eng']:
                    return True
                # Only search the first {f} definition (eliminates secondary uses like hamburguesa as a lady from Hamburg)
                else:
                    return False
        return False


    def get_feminine_noun(self, word):
        if not word.endswith("o"):
            return

        feminine = word[:-1]+"a"
        if self.is_feminized_noun(feminine, word):
            return feminine


    def get_masculine_noun(self, word):
        if not word.endswith("a"):
            return

        masculine = word[:-1]+"o"
        if self.is_feminized_noun(word, masculine):
            return masculine

