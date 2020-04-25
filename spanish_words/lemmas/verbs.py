from collections import defaultdict
import re
import os

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

ir_endings = {
    '1pre': 'o', '2pre': 'es', '3pre': 'e',
    '4pre': 'imos', '5pre': 'ís', '6pre': 'en',
    '1pas': 'í', '2pas': 'iste', '3pas': 'ió',
    '4pas': 'imos', '5pas': 'isteis', '6pas': 'ieron',
    '1fut': 'iré', '2fut': 'irás', '3fut': 'irá',
    '4fut': 'iremos', '5fut': 'iréis', '6fut': 'irán',
    '1cop': 'ía', '2cop': 'ías', '3cop': 'ía',
    '4cop': 'íamos', '5cop': 'íais', '6cop': 'ían',
    '1pos': 'iría', '2pos': 'irías', '3pos': 'iría',
    '4pos': 'iríamos', '5pos': 'iríais', '6pos': 'irían',
    '1pres': 'a', '2pres': 'as', '3pres': 'a',
    '4pres': 'amos', '5pres': 'áis', '6pres': 'an',
    '1pass': 'iera', '2pass': 'ieras', '3pass': 'iera',
    '4pass': 'iéramos', '5pass': 'ierais', '6pass': 'ieran',
    '1passb': 'iese', '2passb': 'ieses', '3passb': 'iese',
    '4passb': 'iésemos', '5passb': 'ieseis', '6passb': 'iesen',
    '1futs': 'iere', '2futs': 'ieres', '3futs': 'iere',
    '4futs': 'iéremos', '5futs': 'iereis', '6futs': 'ieren',
    '2imp': 'e', '3imp': 'a',
    '4imp': 'amos', '5imp': 'id', '6imp': 'an',
    'gerundio': 'iendo', 'participio': 'ido',
}

er_endings = {
    '1pre': 'o', '2pre': 'es', '3pre': 'e',
    '4pre': 'emos', '5pre': 'éis', '6pre': 'en',
    '1pas': 'í', '2pas': 'iste', '3pas': 'ió',
    '4pas': 'imos', '5pas': 'isteis', '6pas': 'ieron',
    '1fut': 'eré', '2fut': 'erás', '3fut': 'erá',
    '4fut': 'eremos', '5fut': 'eréis', '6fut': 'erán',
    '1cop': 'ía', '2cop': 'ías', '3cop': 'ía',
    '4cop': 'íamos', '5cop': 'íais', '6cop': 'ían',
    '1pos': 'ería', '2pos': 'erías', '3pos': 'ería',
    '4pos': 'eríamos', '5pos': 'eríais', '6pos': 'erían',
    '1pres': 'a', '2pres': 'as', '3pres': 'a',
    '4pres': 'amos', '5pres': 'áis', '6pres': 'an',
    '1pass': 'iera', '2pass': 'ieras', '3pass': 'iera',
    '4pass': 'iéramos', '5pass': 'ierais', '6pass': 'ieran',
    '1passb': 'iese', '2passb': 'ieses', '3passb': 'iese',
    '4passb': 'iésemos', '5passb': 'ieseis', '6passb': 'iesen',
    '1futs': 'iere', '2futs': 'ieres', '3futs': 'iere',
    '4futs': 'iéremos', '5futs': 'iereis', '6futs': 'ieren',
    '2imp': 'e', '3imp': 'a',
    '4imp': 'amos', '5imp': 'ed', '6imp': 'an',
    'gerundio': 'iendo', 'participio': 'ido',
}

ar_endings = {
    '1pre': 'o', '2pre': 'as', '3pre': 'a',
    '4pre': 'amos', '5pre': 'áis', '6pre': 'an',
    '1pas': 'é', '2pas': 'aste', '3pas': 'ó',
    '4pas': 'amos', '5pas': 'steis', '6pas': 'aron',
    '1fut': 'aré', '2fut': 'arás', '3fut': 'ará',
    '4fut': 'aremos', '5fut': 'aréis', '6fut': 'arán',
    '1cop': 'aba', '2cop': 'abas', '3cop': 'aba',
    '4cop': 'ábamos', '5cop': 'abais', '6cop': 'aban',
    '1pos': 'aría', '2pos': 'arías', '3pos': 'aría',
    '4pos': 'aríamos', '5pos': 'aríais', '6pos': 'arían',
    '1pres': 'e', '2pres': 'es', '3pres': 'e',
    '4pres': 'emos', '5pres': 'éis', '6pres': 'en',
    '1pass': 'ara', '2pass': 'aras', '3pass': 'ara',
    '4pass': 'áramos', '5pass': 'arais', '6pass': 'aran',
    '1passb': 'ase', '2passb': 'ases', '3passb': 'ase',
    '4passb': 'ásemos', '5passb': 'aseis', '6passb': 'asen',
    '1futs': 'are', '2futs': 'ares', '3futs': 'are',
    '4futs': 'áremos', '5futs': 'areis', '6futs': 'aren',
    '2imp': 'a', '3imp': 'e',
    '4imp': 'emos', '5imp': 'ad', '6imp': 'en',
    'gerundio': 'ando', 'participio': 'ado',
}

zar_endings = {
    '1pas': 'cé',
    '1pres': 'ce', '2pres': 'ces', '3pres': 'ce',
    '4pres': 'cemos', '5pres': 'céis', '6pres': 'cen',
    '3imp': 'ce', '4imp': 'cemos', '6imp': 'cen',
}

car_endings={
    '1pas': 'qué',
    '1pres': 'que', '2pres': 'ques', '3pres': 'que',
    '4pres': 'quemos', '5pres': 'quéis', '6pres': 'quen',
    '3imp': 'que', '4imp': 'quemos', '6imp': 'quen',
}

gar_endings={
    '1pas': 'gué',
    '1pres': 'gue', '2pres': 'ues', '3pres': 'gue',
    '4pres': 'guemos', '5pres': 'guéis', '6pres': 'guen',
    '3imp': 'gue', '4imp': 'guemos', '6imp': 'guen',
}

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

        if not os.path.isfile(iverbs):
            fail("Cannot open irregular verbs:", iverbs)

        # Irregular verbs forms loading
        with open(iverbs) as verbs_file:
            for line in verbs_file:
                if ':' not in line:
                    continue

                # parse:
                # infinitive:conj1|word1,conj2|word2,conj3|word4,word5,word6
                # into:
                # { word1: infinitive, word2: infinitive, word3: infinitive, word4: infinitive, word5: infinitive, word6: infinitive }
                # { infinitive: { conj1: [word1], conj2: [word2], conj3: [word4, word5, word6] } }

                infinitive, forms = line.strip().split(':')

                for form in forms.split(','):
                    values = form.split('|')
                    value = values[1] if len(values) == 2 else values[0]
                    self.reverse_irregular_verbs[value] = infinitive


    def reverse_conjugate(self, verb_tense):
        verb_tense = verb_tense.lower().strip()

        # Check if it's already an infinitive
        if any(verb_tense.endswith(ending) for ending in all_verb_endings):
            return [verb_tense]

        # Check if it's an irregular verb
        if verb_tense in self.reverse_irregular_verbs:
            return [ self.reverse_irregular_verbs[verb_tense] ]

        all_endings = {
            'ir': ir_endings,
            'er': er_endings,
            'ar': ar_endings,
            'car': car_endings,
            'zar': zar_endings,
            'gar': gar_endings,
        }

        # Find the longest matching conjugated ending for each matching infinitive ending
        matched_endings = {}
        for endtype, endings in all_endings.items():
            for conj, ending in endings.items():
                if verb_tense.endswith(ending):
                    if endtype in matched_endings:
                        # select the longest matching ending
                        # take -iendo over -o for ir type ending (dependiendo)
                        # take -eréis over -éis for er type ending (veréis)
                        if len(ending) > len(matched_endings[endtype]):
                            matched_endings[endtype] = ending
                    else:
                        matched_endings[endtype] = ending

        if not matched_endings:
            return []

        possible_verbs = [ verb_tense[:-len(oldending)]+newending for newending,oldending in matched_endings.items() ]

        # Check the verbs against the dictionary and throw out any we've invented
        valid_verbs = [ v for v in possible_verbs if self.spanish_words.is_verb(v) ]

        # No results, try stripping any direct/indirect objects (dime => di)
        if not len(valid_verbs):
            endings = [ending for ending in pronouns if verb_tense.endswith(ending)]
            for ending in endings:
                res = self.reverse_conjugate( verb_tense[:len(ending)*-1] )
                if len(res):
                    return res

        return valid_verbs
