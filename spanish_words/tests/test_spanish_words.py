import spanish_words

words = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt", synonyms="spanish_data/synonyms.txt", iverbs="spanish_data/irregular_verbs.json")

def test_conjugate():
    # Regular
    assert words.conjugate("hablar", 7) == ['hablo']

    # Irregular
    assert words.conjugate("ser", 21) == ['fuiste']

    # Pattern has multiple words for form
    assert words.conjugate("proveer", 3) == ['proveído', 'provisto']

    # Pattern uses multiple stems
    assert words.conjugate("mirar") == {1: ['mirar'], 2: ['mirando'], 3: ['mirado'], 4: ['mirada'], 5: ['mirados'], 6: ['miradas'], 7: ['miro'], 8: ['miras'], 9: ['mirás'], 10: ['mira'], 11: ['miramos'], 12:
['miráis'], 13: ['miran'], 14: ['miraba'], 15: ['mirabas'], 16: ['miraba'], 17: ['mirábamos'], 18: ['mirabais'], 19: ['miraban'], 20: ['miré'], 21: ['miraste'], 22: ['miró'], 23: ['miramos'], 24: ['mirasteis'], 25: ['miraron'], 26: ['miraré'], 27: ['mirarás'], 28: ['mirará'], 29: ['miraremos'], 30: ['miraréis'], 31: ['mirarán'], 32: ['miraría'], 33: ['mirarías'], 34: ['miraría'], 35: ['miraríamos'], 36: ['miraríais'], 37: ['mirarían'], 38: ['mire'], 39: ['mires'], 40: ['mirés'], 41: ['mire'], 42: ['miremos'], 43: ['miréis'], 44: ['miren'], 45: ['mirara'], 46: ['miraras'], 47: ['mirara'], 48: ['miráramos'], 49: ['mirarais'], 50: ['miraran'], 51: ['mirase'], 52: ['mirases'], 53: ['mirase'], 54: ['mirásemos'], 55: ['miraseis'], 56: ['mirasen'], 57: ['mirare'], 58: ['mirares'], 59: ['mirare'], 60: ['miráremos'], 61: ['mirareis'], 62: ['miraren'], 63: ['mira'], 64: ['mirá'], 65: ['mire'], 66: ['miremos'], 67: ['mirad'], 68: ['miren'], 69: ['mires'], 70: ['mire'], 71: ['miremos'], 72: ['miréis'], 73: ['miren']}

    # verb uses two different conjugation patterns
    assert words.conjugate("emparentar", 7) == ['empariento', 'emparento']


def test_get_lemma_verb():
    assert words.get_lemma("notaword", "verb") == "notaword"

    assert words.get_lemma("hablo", "verb") == "hablar"
    assert words.get_lemma("fuiste", "verb") == "ser|ir"
    assert words.get_lemma("proveído", "verb") == "proveer"
    assert words.get_lemma("provisto", "verb") == "proveer"

    assert words.get_lemma("mirando", "verb") == "mirar"
    assert words.get_lemma("mirabais", "verb") == "mirar"

    assert words.get_lemma("emparento", "verb") == "emparentar"
    assert words.get_lemma("empariento", "verb") == "emparentar"

    assert words.get_lemma("damelos", "verb") == "dar"
    assert words.get_lemma("dalosme", "verb") == "dalosme"
    assert words.get_lemma("daloslos", "verb") == "daloslos"

def test_get_lemma_noun():
    assert words.get_lemma("notaword", "noun") == "notaword"

    assert words.get_lemma("casas", "noun") == "casa"
    assert words.get_lemma("narices", "noun") == "nariz"

    assert words.get_lemma("dos", "noun") == "dos"
    assert words.get_lemma("autobús", "noun") == "autobús"
    assert words.get_lemma("cubrebocas", "noun") == "cubrebocas"
    assert words.get_lemma("gas", "noun") == "gas"

def test_get_lemma_adj():
    assert words.get_lemma("notaword", "adj") == "notaword"

    assert words.get_lemma("bellos", "adj") == "bello"
    assert words.get_lemma("bellas", "adj") == "bello"
    assert words.get_lemma("bella", "adj") == "bello"

def test_parse_line():
    res = spanish_words.parse_line("abanderada {f} :: feminine noun of abanderado\n")
    assert res['word'] == 'abanderada'
    assert res['pos'] == 'f'
    assert res['note'] == ''
    assert res['def'] == 'feminine noun of abanderado'

    res = spanish_words.parse_line("abandonamiento {m} [rare] :: abandonment\n")
    assert res['word'] == 'abandonamiento'
    assert res['pos'] == 'm'
    assert res['note'] == 'rare'
    assert res['def'] == 'abandonment'

    res = spanish_words.parse_line("otólogo  :: otologist\n")
    assert res['word'] == 'otólogo'
    assert res['pos'] == ''
    assert res['note'] == ''
    assert res['def'] == 'otologist'

    res = spanish_words.parse_line("cliente {mf} {m} [computing] :: client\n")
    assert res['word'] == 'cliente'
    assert res['pos'] == 'm'
    assert res['note'] == 'computing'
    assert res['def'] == 'client'



def test_lookup():

    res = words.lookup("gafa", "noun")
    assert res == {'f': {'': ['grapple', 'clamp'], 'chiefly in the plural': ['eyeglasses']}}

    # ommiting pos should work
    res = words.lookup("gafa", "")
    assert res == {'f': {'': ['grapple', 'clamp'], 'chiefly in the plural': ['eyeglasses']}}

    # m/f detection
    res = words.lookup("alumno", "noun")
    assert res == {'m/f': {'': ['pupil, student']}}

    # f-el detection
    res = words.lookup("alma", "noun")
    assert res == {'f-el': {'': ['soul']}}

    # m-f detection
    res = words.lookup("batería", "noun")
    assert res == {'m-f': {'f': ['large battery', 'drum set', 'set (collection of things)'], 'mf': ['drummer']}}

    # verb
    res = words.lookup("arrestar", "verb")
    assert res == {'v': {'': ['to arrest']}}

    # filter everything out
    res = words.lookup("arrestar", "noun")
    assert res == {}



def test_get_best_defs():
    assert spanish_words.get_best_defs([ ";def1", "def1-syn1", "def1-syn2", ";def2", ";def3", "def3-syn1" ], 2) == [ ";def1", ";def2" ]
    assert spanish_words.get_best_defs([ ";def1", "def1-syn1", "def1-syn2", ";def2", ";def3", "def3-syn1" ], 3) == [ ";def1", ";def2", ";def3" ]
    assert spanish_words.get_best_defs([ ";def1", "def1-syn1", "def1-syn2", ";def2", ";def3", "def3-syn1" ], 4) == [ ";def1", "def1-syn1", ";def2", ";def3" ]
    assert spanish_words.get_best_defs([ ";def1", "def1-syn1", "def1-syn2", ";def2", ";def3", "def3-syn1" ], 5) == [ ";def1", "def1-syn1", ";def2", ";def3", "def3-syn1" ]

def test_is_feminized_noun():
    assert words.is_feminized_noun("hermana", "hermano") == True
    assert words.is_feminized_noun("hermano", "hermano") == False
    assert words.is_feminized_noun("casa", "caso") == False
    assert words.is_feminized_noun("hamburguesa", "hamburgueso") == False


def test_get_feminine_noun():
    assert words.get_feminine_noun("hermano") == "hermana"
#    assert words.get_feminine_noun("camarero") == "camarera"
    assert words.get_feminine_noun("hermana") == None
    assert words.get_feminine_noun("caso") == None
    assert words.get_feminine_noun("hamburgueso") == None

    # Has feminine noun, but not for the primary definition
    assert words.get_feminine_noun("pato") == None


    # Other word endings
#    assert words.get_feminine_noun("jefe") == "jefa"
#    assert words.get_feminine_noun("doctor") == "doctora"

    # feminine loses accent on last vowel
#    assert words.get_feminine_noun("campeón") == "campeona"




