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


class SpanishWordlist:
    def __init__(self, dictionary=None):
        self.allwords = {}
        if dictionary:
            self.load_dictionary(dictionary)
        self._trantab = str.maketrans("áéíóú", "aeiou")

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
            if not len(self.allwords[word][pos][note]):
                del self.allwords[word][pos][note]

        # cleanup if we've deleted all of something
        if not len(self.allwords[word][pos]):
            del self.allwords[word][pos]
            if not len(self.allwords[word]):
                del self.allwords[word]


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


    def load_dictionary(self, datafile):
        if not os.path.isfile(datafile):
            raise FileNotFoundError(f"Cannot open dictionary: '{datafile}'")

        with open(datafile) as infile:
            for line in infile:
                res = self.parse_line(line)
                if self.should_ignore_def(res['def']) or self.should_ignore_note(res['note']):
                    continue
                word = res['word']
                pos = res['pos']

                self.add_def(res)

        if not os.path.isfile(str(datafile) + ".custom"):
            return

        with open(str(datafile)+".custom") as infile:
            for line in infile:
                if line.strip().startswith("#") or line.strip() == "":
                    continue

                if line.startswith("-"):
                    res = self.parse_line(line[1:])
                    self.remove_def(res)
                else:
                    res = self.parse_line(line)
                    self.add_def(res)


    # returns a list of all pos usage for a word, normalizing specific verb and noun tags to simply "verb" or "noun"
    def get_all_pos(self, word):
        if word not in self.allwords:
            return []

        return list(dict.fromkeys([self.common_pos(k) for k in self.allwords[word].keys() ]))


    def has_verb(self, word):
        if word not in self.allwords:
            return False
        return any( self.pos_is_verb(k) for k in self.allwords[word].keys())

    def has_noun(self, word):
        if word not in self.allwords:
            return False
        return any( self.pos_is_noun(k) for k in self.allwords[word].keys())

    def has_word(self, word, pos=None):
        if not word or word not in self.allwords:
            return False

        if not pos or pos == "":
            return True
        if pos == "noun":
            return self.has_noun(word)
        elif pos == "verb":
            return self.has_verb(word)
        elif pos in self.allwords[word].keys():
            return True
        return False

    def do_analysis(self, word, alldefs):

        if len( {"m","f","mf"} & alldefs.keys() ) > 1:
            alldefs['m-f'] = {}
            for oldpos in ['f', 'mf', 'm']:
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
                femdefs = self.filter_defs(femdefs, 'f', "feminine noun of "+word)
                femdefs = self.filter_defs(femdefs, 'f', "female equivalent of "+word)

                if len(femdefs):
                    alldefs['f'] = femdefs['f']
                    alldefs['m/f'] = {}

                    for oldpos in ['f', 'm']:
                        for oldnote,defs in alldefs[oldpos].items():
                            newnote = oldpos + ", " + oldnote if oldnote != "" else oldpos
                            alldefs['m/f'][newnote] = defs
                        del alldefs[oldpos]

                else:
                    alldefs['m/f'] = alldefs.pop('m')

        return alldefs


    def lookup(self, word, pos=""):
        if word not in self.allwords:
            return

        alldefs = self.allwords[word]
        alldefs = self.filter_defs(alldefs, pos)

        alldefs = self.do_analysis(word, alldefs)

        for pos,notes in alldefs.items():
            for note, defs in notes.items():
                notes[note] = self.defs_to_string(pos, self.split_defs(pos, defs))

        return alldefs


    def is_feminized_noun(self, word, masculine=""):
        if word not in self.allwords:
            return False

        alldefs = self.allwords[word]
        if 'f' not in alldefs:
            return False

        # Only search the first {f} note definitions (eliminates secondary uses like hamburguesa as a lady from Hamburg)
        if "feminine noun of "+masculine in list(alldefs['f'].values())[0][0] or \
           "(female" in list(alldefs['f'].values())[0][0] or \
           "female " in list(alldefs['f'].values())[0][0]:
            return True

        return False


    def unstress(self, word):
        return word.translate(self._trantab)

    def get_feminine_noun(self, word):
        femnoun = None

        # hermano/a  jefe/a  tigre/tigresa
        if word.endswith("o") or word.endswith("e"):
            femnoun = word[:-1]+"a"
            if self.is_feminized_noun(femnoun, word):
                return femnoun

            femnoun = self.unstress(word)+"sa"

        # bailarín / bailarina
        else:
            femnoun = self.unstress(word)+"a"

        if self.is_feminized_noun(femnoun, word):
            return femnoun

        return None


    def get_masculine_noun(self, word):
        if word not in self.allwords or 'f' not in self.allwords[word]:
            return

        maindef = list(self.allwords[word]['f'].values())[0][0]
        res = re.match('fem(?:inine noun|ale equivalent) of ([^;,:]*)', maindef)
        if res:
            return res.group(1)

        # if it doesn't end with a there are no good rules
        if not word.endswith("a"):
            return

        # only check words that have a hint of being female in their primary definition
        if not maindef.startswith("female ") and "(female" not in maindef:
            return

        # hermana -> hermano
        masculine = word[:-1]+"o"
        if self.has_word(masculine, "m"):
            return masculine

        # jefa -> jefe
        masculine = word[:-1]+"e"
        if self.has_word(masculine, "m"):
            return masculine

        # doctora / doctor
        masculine = word[:-1]
        if self.has_word(masculine, "m"):
            return masculine

        # tigresa -> tigre
        if word.endswith("sa"):
            masculine = word[:-2]
            if self.has_word(masculine, "m"):
                return masculine

        if self.is_feminized_noun(word, masculine):
            return masculine

    @staticmethod
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
             \n?$                         # an optional newline at the end
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

    @staticmethod
    def pos_is_verb(pos):
        return pos.startswith("v")

    @staticmethod
    def pos_is_noun(pos):
        if pos in noun_tags:
            return True
        return False

    @staticmethod
    def common_pos(pos):
        if not pos:
            return ""

        if SpanishWordlist.pos_is_verb(pos):
            return "verb"
        if SpanishWordlist.pos_is_noun(pos):
            return "noun"

        return pos.lower()


    @staticmethod
    def should_ignore_def(definition):
        if definition.startswith("obsolete") and (
             definition.startswith("obsolete spelling") or
             definition.startswith("obsolete form of")):
            return True
        return False

    @staticmethod
    def should_ignore_note(note):
        if {"archaic", "dated", "historical", "obsolete", "rare"} & { n.strip().lower() for n in note.split(',') }:
            return True

        return False



    # splits a list by comma, but with awareness of ()
    # split_defs("one, two (2, II), three") will result in
    # [ "one", "two (2, II)", "three" ]
    # probably doable as a regex
    @staticmethod
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


    @staticmethod
    def clean_def(pos, d):
        if SpanishWordlist.pos_is_verb(pos):
            if d.startswith("to "):
                return d[3:]
        return d

    @staticmethod
    def split_defs(pos, defs):
        res = []
        for d in defs:
            for main in SpanishWordlist.split_sep(d, ';'):
                res.append([ SpanishWordlist.clean_def(pos, sub) for sub in SpanishWordlist.split_sep(main, ',') ])
        return res

    @staticmethod
    def get_split_defs(alldefs):

        res = []
        for pos,notes in alldefs.items():
            for note, defs in notes.items():
                res += SpanishWordlist.split_defs(pos, defs)

        return res

    @staticmethod
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


    @staticmethod
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
    #                if self.pos_is_verb(pos):
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

    @staticmethod
    def defs_to_string(pos, defs):
        if not defs:
            return defs

        usage = ""
        if SpanishWordlist.pos_is_verb(pos):
            usage = "to "

        return "; ".join( [ usage + ", ".join(subs) for subs in defs ] )


    @staticmethod
    def filter_defs(alldefs, filter_pos=None, filter_phrase=None):
        res = {}
        if filter_pos: filter_pos = filter_pos.lower()

        for pos,notes in alldefs.items():

            # Remove all defs that don't match the filter_pos
            if filter_pos and filter_pos != "":
                if filter_pos == "verb":
                    if not SpanishWordlist.pos_is_verb(pos):
                        continue
                elif filter_pos == "noun":
                    if not SpanishWordlist.pos_is_noun(pos):
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




