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
            'ar':  self.get_endings('-ar', ''),
            'er':  self.get_endings('-er', ''),
            'ir':  self.get_endings('-ir', ''),
            'ír':  self.get_endings('-ír', ''),
            'car':  self.get_endings('-ar', '-car'),
            'gar':  self.get_endings('-ar', '-gar'),
            'zar':  self.get_endings('-ar', '-zar'),
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
            self.irregular_verbs = json.load(infile)

        for verb, vdata in self.irregular_verbs.items():
            ending = "-"+verb[-4:-2] if verb.endswith("se") else "-"+verb[-2:]
            for item in vdata:
                conjugations = self.do_conjugate( item['stems'], ending, item['pattern'], only_pattern=True )

                for meta,words in conjugations.items():
                    for word in words:
                        if word in self.reverse_irregular_verbs:
                            self.reverse_irregular_verbs[word].append( { 'verb': verb, 'form': meta } )
                        else:
                            self.reverse_irregular_verbs[word] = [ { 'verb': verb, 'form': meta } ]


    def get_endings(self, ending, pattern):
        res = {}
        data =  self.do_conjugate([""], ending, pattern)
        for conj,endings in data.items():
            for ending in endings:
                if ending not in res:
                    res[ending] = [ conj ]
                else:
                    res[ending].append(conj)
        return res


    # Returns a list of dicts containing all possible matches [ { 'verb': "infinitive", 'form': X } ]
    def reverse_conjugate(self, word):
        word = word.lower().strip()

        valid_verbs =[]

        # Check if it's already an infinitive
        if any(word.endswith(ending) for ending in all_verb_endings):
            return [ { 'verb': word, 'form': 1 } ]

        # Check if it's an irregular verb
        if word in self.reverse_irregular_verbs:
            valid_verbs += self.reverse_irregular_verbs[word]

        # Find the longest matching conjugated ending for each matching infinitive ending
        matched_endings = []
        for endtype, endings in self.reverse_endings.items():
            for ending in endings:
                if word.endswith(ending):
                    form = endings[ending]
                    matched_endings.append({'old': ending, 'new': endtype, 'forms': form})
        if matched_endings:
            possible_verbs = []
            for match in matched_endings:
                for form in match['forms']:
                    possible_verbs.append({'verb': word[:-len(match['old'])]+match['new'], 'form': form })

            # Throw out any verb forms that don't match the conjugations of that verb
            # This catches mismatches where the word is what an irregular verb form would be if the verb was regular
            possible_verbs = [ v for v in possible_verbs if not self.is_irregular(v['verb'], v['form']) ]

            # Check the verbs against the dictionary and throw out any we've invented
            for v in possible_verbs:
                if self.spanish_words.is_verb(v['verb']):
                    valid_verbs.append(v)
                # Check for reflexive only verbs
                elif self.spanish_words.is_verb(v['verb']+"se"):
                    v['verb'] += "se"
                    valid_verbs.append(v)

        # No results, try stripping any direct/indirect objects (dime => di)
        # pronouns can only be atteched to infinitive (1), gerund (2) and affirmative commands (63-68)
        endings = [ending for ending in pronouns if word.endswith(ending)]
        for ending in endings:
            valid_verbs += [ v for v in self.reverse_conjugate( word[:len(ending)*-1] ) if v['form'] in [ 1, 2, 63, 64, 65, 66, 67, 68 ] ]

        return valid_verbs


    # Returns True if a verb is irregular in the specified form
    def is_irregular(self, verb, form):
        if verb in self.irregular_verbs:
            ending = "-"+verb[-4:-2] if verb.endswith("se") else "-"+verb[-2:]
            for item in self.irregular_verbs[verb]:
                pattern = item['pattern']
                if form in paradigms[ending][pattern]['patterns']:
                    return True
        return False


    def conjugate(self, verb, form=None, debug=False):
        ending = verb[-4:-2] if verb.endswith("se") else verb[-2:]
        if ending not in all_verb_endings:
            return

        ending = "-"+ending

        res = {}
        if verb in self.irregular_verbs or \
            (verb.endswith("se") and verb[:-2] in irregular_verbs):
            for item in self.irregular_verbs[verb]:
                res = self.do_conjugate( item['stems'], ending, item['pattern'], debug=debug )

        else:
            stem = verb[:-4] if verb.endswith("se") else verb[:-2]
            res = self.do_conjugate( [ stem ], ending, "" )

        if form and form in res:
            return res[form]
        return res

    def do_conjugate(self, stems, ending, pattern, only_pattern=False, debug=False):

        # This has to be a deep copy, since we're overwriting values
        data = {k:v for k, v in paradigms[ending]['']['patterns'].items()}

        # Layer pattern data over base data
        if pattern:
            pattern_data = paradigms[ending][pattern]

            if only_pattern:
                for k in data.keys() - pattern_data['patterns'].keys():
                    del data[k]

            if 'replacement' in pattern_data:
                for pk,pv in pattern_data['replacement'].items():
                    for dk,dv in data.items():
                        if dv:
                            data[dk] = dv.replace(str(pk), pv)

            for pk,pv in pattern_data['patterns'].items():
                if pv == '-':
                    data[pk] = None
                else:
                    data[pk] = pv

        for dk,dv in data.items():
            if dv:
                if len(stems):
                    for sk, sv in enumerate(stems,1):
                        dv = dv.replace(str(sk), sv)
                data[dk] = [ k.strip() for k in dv.split(',') ]
            else:
                data[dk] = [ None ]

        return data
