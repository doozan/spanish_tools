from .paradigms import paradigms
from .inflections import inflections
from .irregular_verbs import irregular_verbs
import re
import os
import json
import sys
#import weakref

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def fail(*args, **kwargs):
    eprint(*args, **kwargs)
    exit(1)

all_verb_endings = [
    'ar', 'er', 'ir', 'ír',
    'arse', 'erse', 'irse', 'írse'
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
    def __init__(self, parent):
        self.parent = parent #weakref.ref(parent)
        self.reverse_irregular_verbs = {}

        self.build_reverse_conjugations()
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
        self._trantab = str.maketrans("áéíóú", "aeiou")

    def build_reverse_inflections(self):
        self._reverse_inflections = {}
        for num, clist in inflections.items():
            for criteria in clist:
                key = ";".join( sorted( [ str(k)+":"+str(v) for k,v in criteria.items() ] ) ).lower()
                if key not in self._reverse_inflections:
                    self._reverse_inflections[key] = num
                else:
                    raise ValueError("dup inflection", key, num, self._reverse_inflections[key])

    def get_inflection_id(self, criteria):
        if not self._reverse_inflections:
            build_reverse_inflections()
        key = ";".join( sorted( [ str(k)+":"+str(v) for k,v in criteria.items() ] ) ).lower()
        return self._reverse_inflections[key]

    def build_reverse_conjugations(self):

        for verb, vdata in irregular_verbs.items():
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

    def select_best(self, forms, debug=False):

        if not forms:
            return []

        if len(forms)==1:
            return forms

        best = []
        best_score = -2
        dbg = []
        for item in forms:
            score = self.get_score(item)
            if score == best_score:
                best.append(item)
            elif score > best_score:
                best = [ item ]
                best_score = score
            if debug: dbg.append({"score": score, **item})

        if debug: print(dbg)

        return best

    # convert a verb/form to a score of likely usage
    # scoring cumulative:
    # 4 = form is irregular
    #
    # 50 = infinitive
    # 8 = gerund
    # 8 = past participle
    # 2 = imperative
    # 2 = indicative
    #
    # 1 = not a region specific use (vos/vosotros,etc)
    # 1 = first person
    def get_score(self, item):
        if not item or item['form'] not in inflections:
            return -1

        score = 0
        verb = item['verb']
        if verb in irregular_verbs:
            form = item['form']

            # determine if usage is irregular by checking against what the regular use would be
            ending = "-"+verb[-4:-2] if verb.endswith("se") else "-"+verb[-2:]
            stem = verb[:-4] if verb.endswith("se") else verb[:-2]
            regular_forms = self.do_conjugate( [stem], ending, '' )

            ending = "-"+verb[-4:-2] if verb.endswith("se") else "-"+verb[-2:]
            for paradigm in irregular_verbs[item['verb']]:
                forms = self.do_conjugate( paradigm['stems'], ending, paradigm['pattern'] )
                if form in forms and forms[form] != regular_forms[form]:
                    score += 2
                    break

        i = inflections[item['form']]
        if any([ x for x in i if x['mood'] in ['infinitive'] ]):
            score += 50
        elif any([ x for x in i if x['mood'] in ['gerund', 'past participle'] ]):
            score += 8
        elif any([ x for x in i if x['mood'] in ['imperative'] ]):
            score += 4
        elif any([ x for x in i if x['mood'] in ['indicative'] ]):
            score += 1

        if any([ x for x in i if 'pers' in x and x['pers'] == 1 ]):
            score += 1

        if any([ x for x in i if 'region' not in x ]):
            score += 1

        return score


    # Returns a list of dicts containing all possible matches [ { 'verb': "infinitive", 'form': X } ]
    def reverse_conjugate(self, word, check_pronouns=True):
        word = word.lower().strip()

        valid_verbs =[]

        # Check if it's already an infinitive listed in the dictionary
        if any(word.endswith(ending) for ending in all_verb_endings) and self.parent.has_word(word, "verb"):
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
                if self.parent.has_word(v['verb'], "verb"):
                    valid_verbs.append(v)
                # Check for reflexive only verbs
                elif self.parent.has_word(v['verb']+"se", "verb"):
                    v['verb'] += "se"
                    valid_verbs.append(v)

        # No results, try stripping any direct/indirect objects (dime => di)
        # pronouns can only be atteched to infinitive (1), gerund (2) and affirmative commands (63-68)
        if check_pronouns:
            endings = [ending for ending in pronouns if word.endswith(ending)]
            for ending in endings:
                valid_verbs += [ v for v in self.reverse_conjugate( self.unstress(word[:len(ending)*-1]), check_pronouns =  False ) if v['form'] in [ 1, 2, 63, 64, 65, 66, 67, 68 ] ]

        return valid_verbs

    def unstress(self, word):
        return word.translate(self._trantab)

    # Returns True if a verb is irregular in the specified form
    def is_irregular(self, verb, form):
        if verb in irregular_verbs:
            ending = "-"+verb[-4:-2] if verb.endswith("se") else "-"+verb[-2:]
            for item in irregular_verbs[verb]:
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
        if verb in irregular_verbs or \
            (verb.endswith("se") and verb[:-2] in irregular_verbs):
            for paradigm in irregular_verbs[verb]:
                forms = self.do_conjugate( paradigm['stems'], ending, paradigm['pattern'], debug=debug )
                for k,v in forms.items():
                    if k not in res:
                        res[k] = v
                    else:
                        res[k] += [i for i in v if i not in res[k]]


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
