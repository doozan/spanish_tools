from spanish_data.paradigms import paradigms

inflections = {
    1:  [ {'mood': 'infinitive'} ],

    2:  [ {'mood': 'gerund'} ],

    3:  [ {'mood': 'past participle', 'gender': 'm', 'number': 's'} ],
    4:  [ {'mood': 'past participle', 'gender': 'f', 'number': 's'} ],
    5:  [ {'mood': 'past participle', 'gender': 'm', 'number': 'p'} ],
    6:  [ {'mood': 'past participle', 'gender': 'f', 'number': 'p'} ],

    7:  [ {'mood': 'indicative', 'tense': 'present', 'pers': 1, 'number': 's'} ],
    8:  [ {'mood': 'indicative', 'tense': 'present', 'pers': 2, 'number': 's', 'formal': 'n'} ],
    9:  [ {'mood': 'indicative', 'tense': 'present', 'pers': 2, 'number': 's', 'formal': 'n', 'voseo': 'y', 'region': 'Latin America'} ],
    10: [ {'mood': 'indicative', 'tense': 'present', 'pers': 2, 'number': 's', 'formal': 'y'},
            {'mood': 'indicative', 'tense': 'present', 'pers': 3, 'number': 's'} ],
    11: [ {'mood': 'indicative', 'tense': 'present', 'pers': 1, 'number': 'p'} ],
    12: [ {'mood': 'indicative', 'tense': 'present', 'pers': 2, 'number': 'p', 'formal': 'n',              'region': 'Spain'} ],
    13: [ {'mood': 'indicative', 'tense': 'present', 'pers': 2, 'number': 'p', 'formal': 'y'},
            {'mood': 'indicative', 'tense': 'present', 'pers': 3, 'number': 'p'} ],

    14: [ {'mood': 'indicative', 'tense': 'imperfect', 'pers': 1, 'number': 's'} ],
    15: [ {'mood': 'indicative', 'tense': 'imperfect', 'pers': 2, 'number': 's', 'formal': 'n'} ],
    16: [ {'mood': 'indicative', 'tense': 'imperfect', 'pers': 2, 'number': 's', 'formal': 'y'},
            {'mood': 'indicative', 'tense': 'imperfect', 'pers': 3, 'number': 's'} ],
    17: [ {'mood': 'indicative', 'tense': 'imperfect', 'pers': 1, 'number': 'p'} ],
    18: [ {'mood': 'indicative', 'tense': 'imperfect', 'pers': 2, 'number': 'p', 'formal': 'n', 'region': 'Spain'} ],
    19: [ {'mood': 'indicative', 'tense': 'imperfect', 'pers': 2, 'number': 'p', 'formal': 'y'},
            {'mood': 'indicative', 'tense': 'imperfect', 'pers': 3, 'number': 'p'} ],

    20: [ {'mood': 'indicative', 'tense': 'preterite', 'pers': 1, 'number': 's'} ],
    21: [ {'mood': 'indicative', 'tense': 'preterite', 'pers': 2, 'number': 's', 'formal': 'n'} ],
    22: [ {'mood': 'indicative', 'tense': 'preterite', 'pers': 2, 'number': 's', 'formal': 'y'},
            {'mood': 'indicative', 'tense': 'preterite', 'pers': 3, 'number': 's'} ],
    23: [ {'mood': 'indicative', 'tense': 'preterite', 'pers': 1, 'number': 'p'} ],
    24: [ {'mood': 'indicative', 'tense': 'preterite', 'pers': 2, 'number': 'p', 'formal': 'n', 'region': 'Spain'} ],
    25: [ {'mood': 'indicative', 'tense': 'preterite', 'pers': 2, 'number': 'p', 'formal': 'y'},
            {'mood': 'indicative', 'tense': 'preterite', 'pers': 3, 'number': 'p'} ],

    26: [ {'mood': 'indicative', 'tense': 'future', 'pers': 1, 'number': 's'} ],
    27: [ {'mood': 'indicative', 'tense': 'future', 'pers': 2, 'number': 's', 'formal': 'n'} ],
    28: [ {'mood': 'indicative', 'tense': 'future', 'pers': 2, 'number': 's', 'formal': 'y'},
            {'mood': 'indicative', 'tense': 'future', 'pers': 3, 'number': 's'} ],
    29: [ {'mood': 'indicative', 'tense': 'future', 'pers': 1, 'number': 'p'} ],
    30: [ {'mood': 'indicative', 'tense': 'future', 'pers': 2, 'number': 'p', 'formal': 'n', 'region': 'Spain'} ],
    31: [ {'mood': 'indicative', 'tense': 'future', 'pers': 2, 'number': 'p', 'formal': 'y'},
            {'mood': 'indicative', 'tense': 'future', 'pers': 3, 'number': 'p'} ],

    32: [ {'mood': 'indicative', 'tense': 'conditional', 'pers': 1, 'number': 's'} ],
    33: [ {'mood': 'indicative', 'tense': 'conditional', 'pers': 2, 'number': 's', 'formal': 'n'} ],
    34: [ {'mood': 'indicative', 'tense': 'conditional', 'pers': 2, 'number': 's', 'formal': 'y'},
            {'mood': 'indicative', 'tense': 'conditional', 'pers': 3, 'number': 's'} ],
    35: [ {'mood': 'indicative', 'tense': 'conditional', 'pers': 1, 'number': 'p'} ],
    36: [ {'mood': 'indicative', 'tense': 'conditional', 'pers': 2, 'number': 'p', 'formal': 'n', 'region': 'Spain'} ],
    37: [ {'mood': 'indicative', 'tense': 'conditional', 'pers': 2, 'number': 'p', 'formal': 'y'},
            {'mood': 'indicative', 'tense': 'conditional', 'pers': 3, 'number': 'p'} ],

    38: [ {'mood': 'subjunctive', 'tense': 'present', 'pers': 1, 'number': 's'} ],
    39: [ {'mood': 'subjunctive', 'tense': 'present', 'pers': 2, 'number': 's', 'formal': 'n'} ],
    40: [ {'mood': 'subjunctive', 'tense': 'present', 'pers': 2, 'number': 's', 'formal': 'n', 'voseo': 'y',  'region': 'Latin America'} ],
    41: [ {'mood': 'subjunctive', 'tense': 'present', 'pers': 2, 'number': 's', 'formal': 'y'},
            {'mood': 'subjunctive', 'tense': 'present', 'pers': 3, 'number': 's'} ],
    42: [ {'mood': 'subjunctive', 'tense': 'present', 'pers': 1, 'number': 'p'} ],
    43: [ {'mood': 'subjunctive', 'tense': 'present', 'pers': 2, 'number': 'p', 'formal': 'n',               'region': 'Spain'} ],
    44: [ {'mood': 'subjunctive', 'tense': 'present', 'pers': 2, 'number': 'p', 'formal': 'y'},
            {'mood': 'subjunctive', 'tense': 'present', 'pers': 3, 'number': 'p'} ],

    45: [ {'mood': 'subjunctive', 'tense': 'imperfect', 'sera': 'ra', 'pers': 1, 'number': 's'} ],
    46: [ {'mood': 'subjunctive', 'tense': 'imperfect', 'sera': 'ra', 'pers': 2, 'number': 's', 'formal': 'n'} ],
    47: [ {'mood': 'subjunctive', 'tense': 'imperfect', 'sera': 'ra', 'pers': 2, 'number': 's', 'formal': 'y'},
            {'mood': 'subjunctive', 'tense': 'imperfect', 'sera': 'ra', 'pers': 3, 'number': 's'} ],
    48: [ {'mood': 'subjunctive', 'tense': 'imperfect', 'sera': 'ra', 'pers': 1, 'number': 'p'} ],
    49: [ {'mood': 'subjunctive', 'tense': 'imperfect', 'sera': 'ra', 'pers': 2, 'number': 'p', 'formal': 'n', 'region': 'Spain'} ],
    50: [ {'mood': 'subjunctive', 'tense': 'imperfect', 'sera': 'ra', 'pers': 2, 'number': 'p', 'formal': 'y'},
            {'mood': 'subjunctive', 'tense': 'imperfect', 'sera': 'ra', 'pers': 3, 'number': 'p'} ],

    51: [ {'mood': 'subjunctive', 'tense': 'imperfect', 'sera': 'se', 'pers': 1, 'number': 's'} ],
    52: [ {'mood': 'subjunctive', 'tense': 'imperfect', 'sera': 'se', 'pers': 2, 'number': 's', 'formal': 'n'} ],
    53: [ {'mood': 'subjunctive', 'tense': 'imperfect', 'sera': 'se', 'pers': 2, 'number': 's', 'formal': 'y'},
            {'mood': 'subjunctive', 'tense': 'imperfect', 'sera': 'se', 'pers': 3, 'number': 's'} ],
    54: [ {'mood': 'subjunctive', 'tense': 'imperfect', 'sera': 'se', 'pers': 1, 'number': 'p'} ],
    55: [ {'mood': 'subjunctive', 'tense': 'imperfect', 'sera': 'se', 'pers': 2, 'number': 'p', 'formal': 'n', 'region': 'Spain'} ],
    56: [ {'mood': 'subjunctive', 'tense': 'imperfect', 'sera': 'se', 'pers': 2, 'number': 'p', 'formal': 'y'},
            {'mood': 'subjunctive', 'tense': 'imperfect', 'sera': 'se', 'pers': 3, 'number': 'p'} ],

    57: [ {'mood': 'subjunctive', 'tense': 'future', 'pers': 1, 'number': 's'} ],
    58: [ {'mood': 'subjunctive', 'tense': 'future', 'pers': 2, 'number': 's', 'formal': 'n'} ],
    59: [ {'mood': 'subjunctive', 'tense': 'future', 'pers': 2, 'number': 's', 'formal': 'y'},
            {'mood': 'subjunctive', 'tense': 'future', 'pers': 3, 'number': 's'} ],
    60: [ {'mood': 'subjunctive', 'tense': 'future', 'pers': 1, 'number': 'p'} ],
    61: [ {'mood': 'subjunctive', 'tense': 'future', 'pers': 2, 'number': 'p', 'formal': 'n', 'region': 'Spain'} ],
    62: [ {'mood': 'subjunctive', 'tense': 'future', 'pers': 2, 'number': 'p', 'formal': 'y'},
            {'mood': 'subjunctive', 'tense': 'future', 'pers': 3, 'number': 'p'} ],

    63: [ {'mood': 'imperative', 'sense': 'affirmative', 'pers': 2, 'formal': 'n', 'number': 's'} ],
    64: [ {'mood': 'imperative', 'sense': 'affirmative', 'pers': 2, 'voseo': 'y', 'formal': 'n', 'number': 's', 'region': 'Latin America'} ],
    65: [ {'mood': 'imperative', 'sense': 'affirmative', 'pers': 2, 'formal': 'y', 'number': 's'} ],
    66: [ {'mood': 'imperative', 'sense': 'affirmative', 'pers': 1, 'number': 'p'} ],
    67: [ {'mood': 'imperative', 'sense': 'affirmative', 'pers': 2, 'formal': 'n', 'number': 'p', 'region': 'Spain'} ],
    68: [ {'mood': 'imperative', 'sense': 'affirmative', 'pers': 2, 'formal': 'y', 'number': 'p'} ],

    69: [ {'mood': 'imperative', 'sense': 'negative', 'pers': 2, 'formal': 'n', 'number': 's'} ],
    70: [],
    71: [ {'mood': 'imperative', 'sense': 'negative', 'pers': 1, 'number': 'p'} ],
    72: [ {'mood': 'imperative', 'sense': 'negative', 'pers': 2, 'formal': 'n', 'number': 'p', 'region': 'Spain'} ],
    73: []
}

def build_reverse_inflections():
    global _reverse_inflections
    _reverse_inflections = {}
    for num, clist in inflections.items():
        for criteria in clist:
            key = ";".join( sorted( [ str(k)+":"+str(v) for k,v in criteria.items() ] ) ).lower()
            if key not in _reverse_inflections:
                _reverse_inflections[key] = [ num ]
            else:
                _reverse_inflections[key].append(num)

def get_inflection_id(criteria):
    if not _reverse_inflections:
        build_reverse_inflections()
    key = ";".join( sorted( [ str(k)+":"+str(v) for k,v in criteria.items() ] ) ).lower()
    return _reverse_inflections[key]


def conjugate(stems, ending, pattern, only_pattern=False):

    data = {}

    ending_data = paradigms[ending][""].copy()
    pattern_data = paradigms[ending][pattern].copy() if pattern else ending_data.copy()

    inflections = {}

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

    for ek,ev in ending_data["patterns"].items():
        if ev:
            for sk, sv in enumerate(stems,1):
                inflections[ek] = [ k.strip() for k in ev.replace(str(sk), sv).split(',') ]

    return inflections


data = conjugate([ "" ], "-ar", "errar", only_pattern=True)
print(data)
