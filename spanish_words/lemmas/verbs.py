from .paradigms import paradigms
from .inflections import inflections
import re
import os
import json
import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def fail(*args, **kwargs):
    eprint(*args, **kwargs)
    exit(1)

all_verb_endings = [
    'ar', 'er', 'ir',
    'arse', 'erse', 'irse',
    'ár', 'ér', 'ír',
    'árse', 'érse', 'írse',
]

# object endings
pronouns = [
        'me',
        'te',
        'le',
        'nos',
        'os',
        'les',
        'se',
        'lo', 'la', 'los', 'las',
        'melo', 'mela', 'melos', 'melas',
        'telo', 'tela', 'telos', 'telas',
        'noslo', 'nosla', 'noslos', 'noslas',
        'oslo',  'osla',  'oslos',  'oslas',
        'selo', 'sela', 'selos', 'selas',
]

class SpanishVerbs:
    def __init__(self, spanish_words, iverbs):
        self.irregular_verbs = {}
        self.reverse_irregular_verbs = {}
        self.spanish_words = spanish_words

        self.build_reverse_conjugations(iverbs)
        self.reverse_endings = {
            'ar':  self.get_endings("-ar", ""),
            'er':  self.get_endings("-er", ""),
            'ir':  self.get_endings("-ir", ""),
            'ír':  self.get_endings("-ír", ""),
            'car':  self.get_endings("-ar", "-car"),
            'gar':  self.get_endings("-ar", "-gar"),
            'zar':  self.get_endings("-ar", "-zar"),
        }

        self.build_reverse_inflections()


    def build_reverse_inflections(self):
        self._reverse_inflections = {}
        for num, clist in inflections.items():
            for criteria in clist:
                key = ";".join( sorted( [ str(k)+":"+str(v) for k,v in criteria.items() ] ) ).lower()
                if key not in self._reverse_inflections:
                    self._reverse_inflections[key] = [ num ]
                else:
                    self._reverse_inflections[key].append(num)

    def get_inflection_id(criteria):
        if not self._reverse_inflections:
            build_reverse_inflections()
        key = ";".join( sorted( [ str(k)+":"+str(v) for k,v in criteria.items() ] ) ).lower()
        return self._reverse_inflections[key]

    def build_reverse_conjugations(self, filename):
        if not os.path.isfile(filename):
            fail("Cannot open irregular verbs:", filename)
        with open(filename, encoding='utf-8') as infile:
            verbs = json.load(infile)

        for verb, vdata in verbs.items():
            ending = "-"+verb[-4:-2] if verb.endswith("se") else "-"+verb[-2:]
            for item in vdata:
                conjugations = self.conjugate( item['stems'], ending, item['pattern'], only_pattern=True )

                for meta,words in conjugations.items():
                    for word in words:
                        if word in self.reverse_irregular_verbs:
                            self.reverse_irregular_verbs[word].append( { "verb": verb, "tense": meta } )
                        else:
                            self.reverse_irregular_verbs[word] = [ { "verb": verb, "tense": meta } ]


    def get_endings(self, ending, pattern):
        res = {}
        data =  self.conjugate([""], ending, pattern)
        for conj,endings in data.items():
            for ending in endings:
                if ending not in res:
                    res[ending] = [ conj ]
                else:
                    res[ending].append(conj)
        return res


    # Returns a list of dicts containing all possible matches [ { "verb": "infinitive", "tense": X } ]
    def reverse_conjugate(self, word):
        word = word.lower().strip()

        valid_verbs =[]

        # Check if it's already an infinitive
        if any(word.endswith(ending) for ending in all_verb_endings):
            return [ { "verb": word, "tense": 1 } ]

        # Check if it's an irregular verb
        if word in self.reverse_irregular_verbs:
            valid_verbs += self.reverse_irregular_verbs[word]

        # Find the longest matching conjugated ending for each matching infinitive ending
        matched_endings = []
        for endtype, endings in self.reverse_endings.items():
            for ending in endings:
                if word.endswith(ending):
                    tense = endings[ending]
                    matched_endings.append({'old': ending, 'new': endtype, 'tenses': tense})

        if matched_endings:
            possible_verbs = []
            for match in matched_endings:
                for tense in match['tenses']:
                    possible_verbs.append({"verb": word[:-len(match['old'])]+match['new'], "tense": tense })

            # Check the verbs against the dictionary and throw out any we've invented
            valid_verbs += [ v for v in possible_verbs if self.spanish_words.is_verb(v['verb']) ]

        # No results, try stripping any direct/indirect objects (dime => di)
        # TODO: the results should be filtered to throw out impossible matches (verb forms that don't take pronoun endings)
        endings = [ending for ending in pronouns if word.endswith(ending)]
        for ending in endings:
            valid_verbs += self.reverse_conjugate( word[:len(ending)*-1] )

        return valid_verbs

    def conjugate(self, stems, ending, pattern, only_pattern=False):

        data = {}

        # This has to be a deep copy, since we're overwriting values
        ending_data = json.loads(json.dumps(paradigms[ending][""])) # Deep copy

        # If a pattern is specified, overlay its data on top of ending_data
        if pattern:
            pattern_data = paradigms[ending][pattern]

            if only_pattern:
                for k in ending_data['patterns'].keys() - pattern_data['patterns'].keys():
                    ending_data['patterns'][k] = None

            if "replacement" in pattern_data:
                for pk,pv in pattern_data['replacement'].items():
                    for ek,ev in ending_data['patterns'].items():
                        if ev:
                            ending_data['patterns'][ek] = ev.replace(str(pk), pv)

            for pk,pv in pattern_data["patterns"].items():
                if pv == '-':
                    ending_data["patterns"][pk] = None
                else:
                    ending_data["patterns"][pk] = pv

        results = {}
        for ek,ev in ending_data["patterns"].items():
            if ev:
                if not len(stems):
                    results[ek] = [ ev ]
                else:
                    results[ek] = []
                    for sk, sv in enumerate(stems,1):
                        results[ek] += [ k.strip() for k in ev.replace(str(sk), sv).split(',') ]

        return results
