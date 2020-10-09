from .paradigms import paradigms
import re
import sys
import os

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
    "m-f",  # uses el/la to indicate different meanings of word (la cura, el cura)
    "f-el", # feminine, but uses "el" when singular
    "m/f"   # part of a masculine/feminine noun pair (amigo/amiga)
])


class SpanishWordlist:
    def __init__(self, parent=None, dictionary="es-en.txt", data_dir=None, custom_dir=None):
        self.irregular_verbs = {}
        self.xnouns = {}
        self.lemmas = {}
        self.allwords = {}
        # allwords = {
        #     "word": {
        #         "pos": {
        #             "label": [
        #                 "def1",
        #                 "def2",
        #             ]
        #         }
        #     }
        #  }
        self.wordforms = {}  # { "word": {(pos, form), (pos, form2)} }
        self.allsyns = {}
        self.meta_buffer = []
        self.parent=parent
        if dictionary:
            self.load_dictionary(dictionary, data_dir, custom_dir)
        self._trantab = str.maketrans("áéíóú", "aeiou")

        self.el_f_nouns = [ 'abra', 'acta', 'agua', 'ala', 'alba', 'alma', 'ama', 'ancla', 'ansia',
                'area', 'arma', 'arpa', 'asma', 'aula', 'ave', 'habla', 'hada', 'hacha', 'hambre', 'águila']

        self.prev_pos = "xx"

    def remove_def(self, item):
        word = item['word']
        pos = item['pos']
        note = item['note']
        definition = item['def']

        if not word or word not in self.allwords:
            print(f"{item} does not match any entries in wordlist, cannot be removed", file=sys.stderr)
            return

        if not pos:
            del self.allwords[word]
            return

        if pos not in self.allwords[word]:
            print(f"{item} does not match any entries in wordlist, cannot be removed", file=sys.stderr)
            return

        if not note and not definition:
            del self.allwords[word][pos]

        else:

            if note not in self.allwords[word][pos]:
                print(f"{item} does not match any entries in wordlist, cannot be removed", file=sys.stderr)
                return

            if not definition:
                del self.allwords[word][pos][note]

            else:
                found = False
                for d in self.allwords[word][pos][note]:
                    if d.startswith(definition):
                        found=True
                        self.allwords[word][pos][note].remove(d)
                if not len(self.allwords[word][pos][note]):
                    found=True
                    del self.allwords[word][pos][note]

                if not found:
                    print(f"{item} does not match any entries in wordlist, cannot be removed", file=sys.stderr)

            # cleanup if we've deleted all of something
            if not len(self.allwords[word][pos]):
                del self.allwords[word][pos]

        if not len(self.allwords[word]):
            del self.allwords[word]


    def add_syn(self, word, pos, syn):
        if syn == "":
            return

        #if syn != word and syn in self.allwords and pos in self.allwords[word]:
        # don't check if sym is in allwords because allwords is not fully populated yet
        if syn != word:
            if word not in self.allsyns:
                self.allsyns[word] = { pos: [syn] }
            elif pos not in self.allsyns[word]:
                self.allsyns[word][pos] = [ syn ]
            else:
                self.allsyns[word][pos].append(syn)


    def add_syns(self, item, add_both_ways=False):
        word = item['word']
        pos = item['pos']
        synstring = item['syn']

        for syn in synstring.split("; "):
            if syn.startswith("Thesaurus:"):
                syn = syn[len("Thesaurus:"):]
            self.add_syn(word, pos, syn)

            if add_both_ways:
                self.add_syn(syn, pos, word)

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


    def parse_tags(self, data):
        tags = {}
        for match in re.finditer(r"([^: ]*):'([^']*)'", data):
            k = match.group(1)
            v = match.group(2)
            if k not in tags:
                tags[k] = [v]
            else:
                tags[k].append(v)

        return tags


    def buffer_meta(self, data):
        self.meta_buffer.append(data)

    def apply_meta(self):
        for data in self.meta_buffer:
            if data['pos'].startswith("meta-lemma-"):
                pos = data['pos'].split("-", 2)[2]
                if self.pos_is_noun(pos):
                    self.add_meta_lemma(data, "noun")
                elif self.pos_is_verb(pos):
                    self.add_meta_lemma(data, "verb")
                else:
                    self.add_meta_lemma(data, pos)
            elif data['pos'] == "meta-noun": # and self._has_word(data['word'], "noun"):
                self.add_nmeta(data)
            elif data['pos'] == "meta-verb": # and self._has_word(data['word'], "verb"):
                self.add_vmeta(data)
            elif data['pos'] == "meta-adj": # and self._has_word(data['word'], "verb"):
                self.add_ameta(data)

    def add_meta_lemma(self, item, pos):
        word = item['word']
        tags = self.parse_tags(item['def'])
        if 'lemma' in tags:
            for lemma in tags['lemma']:
                self.add_lemma(word, lemma, pos)

    def add_form(self, word, form, pos):
        if word not in self.wordforms:
            self.wordforms[word] = { (pos,form) }
        else:
            self.wordforms[word].add( (pos,form) )

    def add_lemma(self, word, lemma, pos):
        #if pos not in self.lemmas:
        #    self.lemmas[pos] = {}
        #self.lemmas[pos][word] = lemma
        if word not in self.lemmas:
            self.lemmas[word] = {}

        if pos not in self.lemmas[word]:
            self.lemmas[word][pos] = [lemma]
        elif lemma not in self.lemmas[word][pos]:
            self.lemmas[word][pos].append(lemma)

        self.add_form(lemma, word, pos)

    def get_lemmas(self, word):
        if word not in self.lemmas:
            return None

        return self.lemmas[word].get(pos)

    def get_lemma(self, word, pos):
        lemma = None

        search = word
        found = False
        depth = 0

        while search in self.lemmas and pos in self.lemmas[search]:
            found = True
            if self.lemmas[search][pos] in [ "-", "+", search ]: # -/+ indicate the word is its own lemma
                break
            search = self.lemmas[search][pos][-1]
            depth = depth+1
            if depth > 10:
#                raise ValueError(f"Lemma loop detected: '{search}' -> '{self.lemmas[pos][search]}'")
                print(f"Lemma loop detected: '{search}' -> '{self.lemmas[search][pos]}'", file=sys.stderr)
                break

        if found:
            lemma = search

        elif self._has_word(word, pos):
            lemma = word

        return lemma


    def add_ameta(self, item):
        word = item['word']
        tags = self.parse_tags(item['def'])

        # used for gender neutral terms
        if 'm' in tags and 'f' in tags:
            return

        for k,v in tags.items():

            if k in ["m", "pl", "mpl", "fpl"]:
                for altword in v:
                    self.add_lemma(altword, word, "adj")


    def add_nmeta(self, item):
        word = item['word']
        tags = self.parse_tags(item['def'])

        # used for gender neutral terms
        if 'm' in tags and 'f' in tags:
            return

        for k,v in tags.items():

            if k == "pl":
                for plural in v:
                    # some pl: tags have a - to indicate the noun is uncountable
                    if plural in ["-", "+"]:
                        continue
                    self.add_lemma(plural, word, "noun")


            elif k in ["f", "m"]:
                tag = k+":"+word
                for xnoun in v:

                    # some f: tags have a 1 to indicate they follow normal rules
                    # TODO: Add support for f=1
                    if xnoun in ["1", "-"]:
                        continue
                    self.xnouns[tag] = xnoun

                    # Femine nouns that specify a masculine counterpart
                    # should add a femnoun -> masculine lemma
                    # Note: Do not do this the other ways (m nouns with f parts creating lemmas)
                    # because it creates incorrect lemmas for words like pata and hambugrguesa which are feminine
                    # nouns first and feminine pairs of masculine nouns second
                    if k == "m":
                        self.add_lemma(word, xnoun, "noun")

            # explicitly tagged lemmas are generated when words are ignored as being obsolete versions of new words
            elif k == "lemma":
                for lemma in v:
                    self.add_lemma(word, lemma, "noun")

            else:
                print(f"unknown nmeta value: {k} in {word}", file=sys.stderr)

        return

    # def = "pattern:'-gir' stems:['compun']"
    def add_vmeta(self, item):

        verb = item['word']
        ending = "-"+verb[-4:-2] if verb.endswith("se") else "-"+verb[-2:]

        tags = self.parse_tags(item['def'])
        if "pattern" not in tags:
            tags["pattern"] = [""]
        if "stem" not in tags:
            tags["stem"] = [""]

        iverb = { "pattern": tags["pattern"][0],
                  "stems": tags["stem"] }

        if ending == iverb["pattern"]:
#            print(f"Useless pattern declaration {verb}: {item}", file=sys.stderr)
            return

        if iverb["pattern"] not in paradigms[ending]:
            print(f"Bad pattern specified in vmeta for {verb}: {item['def']}", file=sys.stderr)
            return

        # Ignore reflexives if the non-reflexive is in the database
        if verb.endswith("se") and verb[:-2] in self.irregular_verbs:
            return
        # Replace existing reflexive with no-reflexive
        elif verb+"se" in self.irregular_verbs:
            self.irregular_verbs.pop(verb+"se")

        if verb not in self.irregular_verbs:
            self.irregular_verbs[verb] = [ iverb ]
        else:
            self.irregular_verbs[verb].append(iverb)

    def process_line(self, line):

        if line.startswith("#"):
            return

        if line.startswith("- "):
            res = self.parse_line(line[2:])
            self.remove_def(res)
            return

        res = self.parse_line(line)
        if res['pos'].startswith("meta-"):
            self.buffer_meta(res)
        else:

            is_first_pos_def = True
            cur_pos = self.common_pos(res['pos'])

            if res['word'] in self.allwords and cur_pos == self.prev_pos:
                is_first_pos_def = False

            self.add_def(res)
            self.add_syns(res, is_first_pos_def)
            self.prev_pos = cur_pos


    def load_dictionary(self, filename, data_dir, custom_dir):
        dataprefix = os.path.splitext(filename)[0]

        if not data_dir:
            data_dir = os.environ.get("SPANISH_DATA_DIR", "spanish_data")

        if not custom_dir:
            custom_dir = os.environ.get("SPANISH_CUSTOM_DIR", "spanish_custom")

        datafile = os.path.join(data_dir, filename)
        if not os.path.isfile(datafile):
            raise FileNotFoundError(f"Cannot open dictionary: '{datafile}'")

        with open(datafile) as infile:
            for line in infile:
                self.process_line(line)

        for custom in [ os.path.join(dirname, dataprefix + ".custom") for dirname in [ data_dir, custom_dir ] if dirname ]:
            if not os.path.isfile(custom):
                continue
            with open(custom) as infile:
                for line in infile:
                    if line.strip().startswith("#") or line.strip() == "":
                        continue
                    self.process_line(line)

        self.apply_meta()



    # returns a list of all pos usage for a word, normalizing specific verb and noun tags to simply "verb" or "noun"
    def get_all_pos(self, word):
        if word not in self.allwords:
            return []

        return dict.fromkeys( [ self.common_pos(k) for k in self.allwords[word] ]).keys()


    def has_verb(self, word):
        if word not in self.allwords:
            return False
        return any( self.pos_is_verb(k) for k in self.allwords[word])

    def has_noun(self, word):
        if word not in self.allwords:
            return False
        return any( self.pos_is_noun(k) for k in self.allwords[word])

    def _has_word(self, word, pos=None):
        if not word or word not in self.allwords:
            return False

        if not pos or pos == "":
            return True
        if pos == "noun":
            return self.has_noun(word)
        elif pos == "verb":
            return self.has_verb(word)
        elif pos in self.allwords[word]:
            return True
        return False

    def do_analysis(self, word, alldefs):

        # If there are independent defs for masculine and feminine use,
        # tag it as m-f
        if len( {"m","f","mf"} & alldefs.keys() ) > 1:
            alldefs['m-f'] = {}
            for oldpos in ['f', 'mf', 'm']:
                if oldpos in alldefs:
                    for oldnote,use in alldefs[oldpos].items():
                        newnote = oldpos + ", " + oldnote if oldnote != "" else oldpos
                        alldefs['m-f'][newnote] = use
                    del alldefs[oldpos]

        # Tag f-el nouns
        elif "f" in alldefs and word in self.el_f_nouns:
            alldefs["f-el"] = alldefs.pop("f")

        # Check for feminine equivalent nouns and tag as m/f
        elif "m" in alldefs:

            # If this has a "-a" feminine counterpart, reclassify the "m" defs as "m/f"
            # and add any feminine definitions (ignoring the "feminine noun of xxx" def)
            femnoun = self.get_feminine_noun(word)
            if femnoun:
                femdefs = []
                if femnoun in self.allwords:
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

    def get_synonyms(self, word, pos):
        if word not in self.allwords or word not in self.allsyns:
            return

        allsyns = self.allsyns[word]
        allsyns = self.filter_syns(allsyns, pos)

        synonyms = []
        for pos,syns in allsyns.items():
            for syn in syns:
                # Don't filter by pos because it's the specific pos and not the clean pos
                # ie demora (f) is a syn of retraso (m) even though f!=m
                if syn in self.allwords: # and pos in self.allwords[syn]:
                    synonyms.append(syn)

        return dict.fromkeys(synonyms).keys()


    def is_feminized_noun(self, word, masculine=""):
        if 'm:'+word in self.xnouns:
            return True


        # Only search the first {f} note definitions (eliminates secondary uses like hamburguesa as a lady from Hamburg)
#        if "feminine noun of "+masculine in list(alldefs['f'].values())[0][0] or \
#           "(female" in list(alldefs['f'].values())[0][0] or \
#           "female equivalent of " in list(alldefs['f'].values())[0][0]:
#            return True

        return False


    def unstress(self, word):
        return word.translate(self._trantab)

    def get_feminine_noun(self, word):
        return self.xnouns.get(f'f:{word}')

    def guess_feminine_noun(self, word):

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
        return self.xnouns.get(f'm:{word}')

    def guess_masculine_noun(self, word):
        # if it doesn't end with a there are no good rules
        if not word.endswith("a"):
            return

        # only check words that have a hint of being female in their primary definition
        if not maindef.startswith("female ") and "(female" not in maindef:
            return

        # hermana -> hermano
        masculine = word[:-1]+"o"
        if self._has_word(masculine, "m"):
            return masculine

        # jefa -> jefe
        masculine = word[:-1]+"e"
        if self._has_word(masculine, "m"):
            return masculine

        # doctora / doctor
        masculine = word[:-1]
        if self._has_word(masculine, "m"):
            return masculine

        # tigresa -> tigre
        if word.endswith("sa"):
            masculine = word[:-2]
            if self._has_word(masculine, "m"):
                return masculine

        if self.is_feminized_noun(word, masculine):
            return masculine

    @staticmethod
    def parse_line(data):

        pattern = r"""(?x)
             (?P<word>[^{:]+)             # The word (anything not an opening brace)

             ([ ]{                        # (optional) a space
               (?P<pos>[^}]*)             #    and then the the part of speech, enclosed in curly braces
             \})*                         #    (this may be specified more than once, the last one wins)

             ([ ]\[                       # (optional) a space
               (?P<note>[^\]]*)           #    and then the note, enclosed in square brackets
             \])?

             (?:[ ][|][ ]                    # (optional) a space and then a pipe | and a space
               (?P<syn>.*?)                #    and then a list of synonyms
             )?

             (                            # this whole bit can be optional
               [ ]*::[ ]                  #   :: optionally preceded by whitespace and followed by a mandatory space

               (?P<def>.*)                #   the definition
             )?
             \n?$                         # an optional newline at the end
        """
        res = re.match(pattern, data)

        # This only applies to one entry in the 4/20/2020 wiktionary dump
        if not res:
    #        print("DOES NOT MATCH REGEX: '%s'"% data.strip(), file=sys.stderr)
            return {'word':'', 'pos':'', 'note': '', 'syn': '', 'def': ''}

        word = res.group('word').strip()
        pos = res.group('pos') if res.group('pos') else ''
        note = res.group('note') if res.group('note') else ''
        syn = res.group('syn') if res.group('syn') else ''
        definition = res.group('def') if res.group('def') else ''

        res = {
            'word': word,
            'pos': pos,
            'note': note,
            'syn': syn,
            'def': definition
        }
        return res

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

        pos = pos.lower()
        if SpanishWordlist.pos_is_verb(pos):
            return "verb"
        if SpanishWordlist.pos_is_noun(pos):
            return "noun"

        return pos


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
            if d.startswith("to ") or d.startswith("To "):
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
    def defs_to_string(pos, defs):
        if not defs:
            return defs

        usage = ""
        if SpanishWordlist.pos_is_verb(pos):
            usage = "to "

        return "; ".join( [ usage + ", ".join(subs) for subs in defs ] )


    @staticmethod
    def filter_syns(allsyns, filter_pos=None):
        res = {}
        if filter_pos:
            filter_pos = filter_pos.lower()

        for pos,syns in allsyns.items():
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
            for syn in syns:
                if syn == "":
                    continue
                if pos not in res:
                    res[pos] = []
                if syn not in res[pos]:
                    res[pos].append(syn)

        return res


    @staticmethod
    def filter_defs(alldefs, filter_pos=None, filter_phrase=None):
        res = {}
        if filter_pos:
            filter_pos = filter_pos.lower()

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

            for note, defs in notes.items():

                for d in defs:
                    # Filter out all defs that contain the filter_phrase
                    if filter_phrase and filter_phrase in d:
                        continue
                    if pos not in res:
                        res[pos] = {}
                    if note not in res[pos]:
                        res[pos][note] = []
                    if d not in res[pos][note]:
                        res[pos][note].append(d)

        return res

