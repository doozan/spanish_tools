from collections import defaultdict
from .lemmas import SpanishLemmas
import re
import sys
import os

el_f_nouns = [ 'acta', 'agua', 'ala', 'alba', 'alma', 'ama', 'ancla', 'ansia', 'area',
        'arma', 'arpa', 'asma', 'aula', 'habla', 'habla', 'hacha', 'hambre', 'águila']

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

def parse_line(data):
    #re.match("^([^{]+)(?:{([a-z]+)})?", line) #}

    pattern = r"""(?x)
         (?P<word>[^{:]+)             # The word (anything not an opening brace)

         ([ ]{                        # (optional) a space
           (?P<pos>[^}]*)             #    and then the the part of speech, enclosed in curly braces
         \})*                         #    (this may be specified more than once)

         ([ ]\[                       # (optional) a space
           (?P<note>[^\]]*)           #    and then the note, enclosed in square brackets
         \])?

         (                            # this whole bit can be optional
           [ ]*::[ ]                  #   :: optionally preceded by whitespace and followed by a mandatory space

           (?P<def>.*)                #   the definition
         )?
         \n                           # newline
    """
    res = re.match(pattern, data)

    # This only applies to one entry in the 4/20/2020 wiktionary dump
    if not res:
#        print("DOES NOT MATCH REGEX: '%s'"% data.strip())
        return {'word':'', 'pos':'', 'note': '', 'def': ''}

    word = res.group('word').strip()
    #tags = [ item.strip() for item in res.group('tags').split(',') ] if res.group('tags') else []
    note = res.group('note') if res.group('note') else ''
    pos = res.group('pos') if res.group('pos') else ''
    definition = res.group('def') if res.group('def') else ''

    return {
        'word': word,
        'pos': pos,
        'note': note,
        'def': definition
    }

def pos_is_verb(pos):
    return pos.startswith("v")

def pos_is_noun(pos):
    if pos in noun_tags:
        return True
    return False

def common_pos(pos):
    if not pos:
        return ""

    if pos_is_verb(pos):
        return "verb"
    if pos_is_noun(pos):
        return "noun"

    return pos.lower()

def strip_eng_verb(eng):
    if eng.startswith("to "):
        return eng[3:]
    return eng

def should_ignore_note(note):
    if {"archaic", "dated", "historical", "obsolete", "rare"} & { n.strip().lower() for n in note.split(',') }:
        return True

    return False

def should_ignore_def(definition):
    if definition.startswith("obsolete") and (
         definition.startswith("obsolete spelling") or
         definition.startswith("obsolete form of")):
        return True
    return False


# splits a list by comma, but with awareness of ()
# split_defs("one, two (2, II), three") will result in
# [ "one", "two (2, II)", "three" ]
# probably doable as a regex
def split_sep(data, separator):
    if not data or data == "":
        return []

    splits=[]
    nested=0

    last_split=0

    openers = ["(", "[", "{"]
    closers = [")", "]", "}"]
    separators = [","]

    for idx in range(0,len(data)):
        c = data[idx]
        if c in openers:
            nested += 1
        elif c in closers:
            nested = nested-1 if nested else 0
        elif not nested and c == separator:
            splits.append(data[last_split:idx].strip())
            last_split=idx+1

    if idx>last_split:
        splits.append(data[last_split:idx+1].strip())

    return splits


def split_defs(defs):
    res = []
    for d in defs:
        for main in split_sep(d, ';'):
            res.append([ sub for sub in split_sep(main, ',') ])

    return res

def get_split_defs(alldefs):

    res = []
    for pos,notes in alldefs.items():
        for note, defs in notes.items():
            res += split_defs( defs )

    return res

def get_best_defs(defs,limit):
    return defs

""" # This is old code

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


#    # TODO: split the defs
#        # TODO: Move this to get_best_def
#        # Definitions are separated by commas and semicolons
#        for defs in item['def'].split("; "):
#            is_new_def=True
#            for eng in split_def(defs):
#                if pos_is_verb(pos):
#                    eng = strip_eng_verb(eng)
#                if is_new_def:
#                    eng = ";" + eng
#
#                if eng not in usage[pos][note]:
#                    usage[pos][note].append(eng)
#                is_new_def = False

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
""" and None

def defs_to_string(defs, pos):
    usage = ""
    if pos_is_verb(pos):
        usage = "to "

    return "; ".join( [ usage + ", ".join(subs) for subs in defs ] )


def filter_defs(alldefs, filter_pos=None, filter_phrase=None):
    res = {}
    if filter_pos: filter_pos = filter_pos.lower()

    for pos,notes in alldefs.items():

        # Remove all defs that don't match the filter_pos
        if filter_pos and filter_pos != "":
            if filter_pos == "verb":
                if not pos_is_verb(pos):
                    continue
            elif filter_pos == "noun":
                if not pos_is_noun(pos):
                    continue
            elif filter_pos != pos:
                continue

        # Filter out all defs that contain the filter_phrase
        for note, defs in notes.items():

            for d in defs:
                if filter_phrase and filter_phrase in d:
                    continue
                if pos not in res:
                    res[pos] = {}
                if note not in res[pos]:
                    res[pos][note] = []
                if d not in res[pos][note]:
                    res[pos][note].append(d)

    return res



class SpanishWords:
    def __init__(self, dictionary, synonyms, iverbs):
        self.allwords = {}
        self.allsyns = {}
        self.nouns_ending_s = {}
        self.irregular_verbs = {}
        self.reverse_irregular_verbs = defaultdict(list)

        self.init_dictionary(dictionary)
        self.init_syns(synonyms)
        self.lemmas = lemmas.SpanishLemmas(self, iverbs)

    def get_lemma(self, word, pos, debug=False):
        return self.lemmas.get_lemma(word, pos, debug)

    def conjugate(self, verb, form=None, debug=False):
        return self.lemmas.conjugate(verb, form, debug)

    def remove_def(self, item):
        word = item['word']
        pos = item['pos']
        note = item['note']
        definition = item['def']

        if not word or word not in self.allwords:
            return

        if not pos:
            del self.allwords[word]
            return

        if pos not in self.allwords[word]:
            return


        # TODO: there are unintended consequences having the default note be ''
        # it makes it impossible to detect if we should delete all notes for a pos
        # or just the default note.  The current usage is likely counter-intuitive.
        # since it will leave all definitions with notes when a user specifies just
        # a word and a pos to remove
        if note not in self.allwords[word][pos]:
            return

        if not definition:
            del self.allwords[word][pos][note]

        else:
            for d in self.allwords[word][pos][note]:
                if d.startswith(definition):
                    self.allwords[word][pos][note].remove(d)

    def add_def(self, item):
        word = item['word']
        pos = item['pos']
        note = item['note']
        definition = item['def']

        if word not in self.allwords:
            self.allwords[word] = { pos: { note: [ definition ] } }
        else:
            if pos not in self.allwords[word]:
                self.allwords[word][pos] = { note: [ definition ] }
            else:
                if note not in self.allwords[word][pos]:
                    self.allwords[word][pos][note] = [ definition ]
                else:
                    self.allwords[word][pos][note].append(definition)


    def init_dictionary(self, datafile):
        if not os.path.isfile(datafile):
            raise FileNotFoundError("Cannot open dictionary: '%s'"%datafile)

        with open(datafile) as infile:
            for line in infile:
                res = parse_line(line)
                if should_ignore_def(res['def']) or should_ignore_note(res['note']):
                    continue
                word = res['word']
                pos = res['pos']

                if pos and (pos_is_noun(pos) or pos == "num") and word.endswith("s"):
                    self.nouns_ending_s[word] = 1

                self.add_def(res)


        if not os.path.isfile(datafile + ".custom"):
            return

        with open(datafile+".custom") as infile:
            for line in infile:
                if line.strip().startswith("#") or line.strip() == "":
                    continue

                if line.startswith("-"):
                    res = parse_line(line[1:])
                    self.remove_def(res)
                else:
                    res = parse_line(line)
                    self.add_def(res)

    def init_syns(self, datafile):
        if not os.path.isfile(datafile):
            fail("Cannot open synonyms:", datafile)

        with open(datafile) as infile:
            for line in infile:
                word, syns = line.split(':')
                syns = syns.strip()
                self.allsyns[word] = syns # syns.split('/')


    # returns a list of all pos usage for a word, normalizing specific verb and noun tags to simply "verb" or "noun"
    def get_all_pos(self, word):
        if word not in self.allwords:
            return []

        return list(dict.fromkeys([common_pos(k) for k in self.allwords[word].keys() ]))


    def is_verb(self, word):
        if word not in self.allwords:
            return False
        return any( pos_is_verb(k) for k in self.allwords[word].keys())

    def is_noun(self, word):
        if word not in self.allwords:
            return False
        return any( pos_is_noun(k) for k in self.allwords[word].keys())

    def do_analysis(self, word, alldefs):

        if len( {"m","f","mf"} & alldefs.keys() ) > 1:
            alldefs['m-f'] = {}
            for oldpos in ['m', 'f', 'mf']:
                if oldpos in alldefs:
                    for oldnote,use in alldefs[oldpos].items():
                        newnote = oldpos + ", " + oldnote if oldnote != "" else oldpos
                        alldefs['m-f'][newnote] = use
                    del alldefs[oldpos]

        elif "f" in alldefs and word in el_f_nouns:
            alldefs["f-el"] = alldefs.pop("f")

        elif "m" in alldefs:

            # If this has a "-a" feminine counterpart, reclassify the "m" defs as "m/f"
            # and add any feminine definitions (ignoring the "feminine noun of xxx" def)
            femnoun = self.get_feminine_noun(word)
            if femnoun:
                femdefs = self.allwords[femnoun]
                femdefs = filter_defs(femdefs, 'f', "feminine noun of "+word)

                if len(femdefs):
                    alldefs['f'] = femdefs['f']
                    alldefs['m/f'] = {}

                    for oldpos in ['m', 'f']:
                        for oldnote,defs in alldefs[oldpos].items():
                            newnote = oldpos + ", " + oldnote if oldnote != "" else oldpos
                            alldefs['m/f'][newnote] = defs
                        del alldefs[oldpos]

                else:
                    alldefs['m/f'] = alldefs.pop('m')

        return alldefs


    def get_synonyms(self, word):
        if word in self.allsyns and self.allsyns[word]:
            return self.allsyns[word].split('/')
        else:
            return []

    def lookup(self, word, pos=""):
        if word not in self.allwords:
            return

        alldefs = self.allwords[word]
        alldefs = filter_defs(alldefs, pos)

        return self.do_analysis(word, alldefs)


    def is_feminized_noun(self, word, masculine):
        if word not in self.allwords:
            return False

        alldefs = self.allwords[word]
        if 'f' not in alldefs:
            return False

        # Only search the first {f} note definitions (eliminates secondary uses like hamburguesa as a lady from Hamburg)
        if "feminine noun of "+masculine in list(alldefs['f'].values())[0][0]:
            return True

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

