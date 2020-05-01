import pytest
import spanish_words

words = None # spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt", synonyms="spanish_data/synonyms.txt", iverbs="spanish_data/irregular_verbs.json")

def test__init__():
    global words
    words = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt", synonyms="spanish_data/synonyms.txt", iverbs="spanish_data/irregular_verbs.json")
    assert words.conjugate("hablar", 7) == ['hablo']

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

    assert words.get_lemma("piernas", "noun") == "pierna"

    assert words.get_lemma("dos", "noun") == "dos"
    assert words.get_lemma("autobús", "noun") == "autobús"
    assert words.get_lemma("cubrebocas", "noun") == "cubrebocas"
    assert words.get_lemma("gas", "noun") == "gas"

def test_get_lemma_adj():
    assert words.get_lemma("notaword", "adj") == "notaword"

    assert words.get_lemma("bellos", "adj") == "bello"
    assert words.get_lemma("bellas", "adj") == "bello"
    assert words.get_lemma("bella", "adj") == "bello"

# TODO:
def test_remove_def():
    return

# TODO:
def test_add_def():
    return

# TODO:
def test_init_dictionary():
    with pytest.raises(FileNotFoundError) as e_info:
         words.init_dictionary("not_a_file") == "yes"

# TODO:
def test_init_syns():
    return

def test_get_all_pos():
    assert words.get_all_pos("notaword") == []
    assert words.get_all_pos("hablar") == ["verb"]
    assert words.get_all_pos("casa") == ["noun"]
    assert words.get_all_pos("rojo") == ["adj", "noun"]

def test_is_verb():
    assert words.is_verb("tener") == True
    assert words.is_verb("tenor") == False

def test_do_analysis():

    defs = {
            'm': { '': ['male usage'] },
            'f': { '': ['female usage'] }
    }
    assert words.do_analysis("hacer", defs) == {'m-f': {'m': ['male usage'], 'f': ['female usage']}}

    defs = {
            'mf': { '': ['male/female usage'] },
            'f': { '': ['female only usage'] }
    }
    assert words.do_analysis("hacer", defs) == {'m-f': {'f': ['female only usage'], 'mf': ['male/female usage']}}


    # doing a lookup for "amigo" should detect female use and change 'm' to 'm/f'
    defs = { 'm': { '': ['usage'] } }
    assert words.do_analysis("amigo", defs) == {'m/f': {'': ['usage']}}


    # doing a lookup for "tío" should detect female use and change 'm' to 'm/f' and add the extra usage
    defs = { 'm': { '': ['usage'] } }
    assert words.do_analysis("tío", defs) == {'m/f': {'m': ['usage'], 'f, colloquial, Spain': ['woman, chick']}}

    defs = { 'f': { '': ['water'] } }
    assert words.do_analysis("agua", defs) == { 'f-el': { '': ['water'] } }

    return


def test_get_synonyms():
    assert words.get_synonyms("utilizar") ==  []
    assert words.get_synonyms("oler") == ['apestar', 'olermal', 'olor']

def test_lookup():

    res = words.lookup("gafa", "noun")
    assert res == {'f': {'': ['grapple', 'clamp'], 'chiefly in the plural': ['eyeglasses']}}

    # ommiting pos should work
    res = words.lookup("gafa", "")
    assert res == {'f': {'': ['grapple', 'clamp'], 'chiefly in the plural': ['eyeglasses']}}

    # m/f detection
    res = words.lookup("alumno", "noun")
    assert res == {'m/f': {'': ['pupil, student']}}

    res = words.lookup("abuelo", "noun")
    assert res == {'m/f': {'m': ['grandfather', "loose tufts of hair in the nape when one's hair is messed up"], 'm, colloquial, affectionate': ['an elderly person'], 'f, colloquial': ['old woman'], 'f, Mexico': ['a kind of flying ant ']}}

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



def test_get_masculine_noun():
    assert words.get_masculine_noun("hermana") == "hermano"
    assert words.get_masculine_noun("casa") == None
    assert words.get_masculine_noun("hamburguesa") == None



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


def test_pos_is_noun():
    assert spanish_words.pos_is_noun("m") == True
    assert spanish_words.pos_is_noun("m/f") == True
    assert spanish_words.pos_is_noun("f-el") == True
    assert spanish_words.pos_is_noun("f") == True
    assert spanish_words.pos_is_noun("vt") == False
    assert spanish_words.pos_is_noun("") == False


def test_pos_is_verb():
    assert spanish_words.pos_is_verb("v") == True
    assert spanish_words.pos_is_verb("vt") == True
    assert spanish_words.pos_is_verb("vr") == True
    assert spanish_words.pos_is_verb("m") == False
    assert spanish_words.pos_is_verb("") == False


def test_common_pos():
    assert spanish_words.common_pos("m") == "noun"
    assert spanish_words.common_pos("m/f") == "noun"
    assert spanish_words.common_pos("f-el") == "noun"
    assert spanish_words.common_pos("f") == "noun"
    assert spanish_words.common_pos("v") == "verb"
    assert spanish_words.common_pos("vt") == "verb"
    assert spanish_words.common_pos("vr") == "verb"
    assert spanish_words.common_pos("xxxx") == "xxxx"
    assert spanish_words.common_pos("adj") == "adj"
    assert spanish_words.common_pos("") == ""

def test_strip_eng_verb():
    assert spanish_words.strip_eng_verb("to be") == "be"
    assert spanish_words.strip_eng_verb("together") == "together"
    assert spanish_words.strip_eng_verb("have to go") == "have to go"


def test_should_ignore_note():
    assert spanish_words.should_ignore_note("obsolete") == True
    assert spanish_words.should_ignore_note("new, obsolete") == True
    assert spanish_words.should_ignore_note("new, obsolete, test") == True
    assert spanish_words.should_ignore_note("not yet obsolete") == False

def test_should_ignore_def():
    assert spanish_words.should_ignore_def("obsolete spelling of isla") == True
    assert spanish_words.should_ignore_def("obsolete form of isla") == True
    assert spanish_words.should_ignore_def("obsolete is the meaning of the word") == False
    assert spanish_words.should_ignore_def("obsolete") == False

def test_split_sep():
    assert spanish_words.split_sep(None, ",") == []
    assert spanish_words.split_sep("", ",") == []
    assert spanish_words.split_sep("one", ",") == ["one"]
    assert spanish_words.split_sep("one,", ",") == ["one"]
    assert spanish_words.split_sep("one, two", ",") == ["one", "two"]
    assert spanish_words.split_sep("one; two, three", ",") == ["one; two", "three"]
    assert spanish_words.split_sep("one; two, three", ";") == ["one", "two, three"]
    assert spanish_words.split_sep("one, two (2, II), three", ",") == [ "one", "two (2, II)", "three" ]
    assert spanish_words.split_sep("one, two (2, II), three ([(nested, deep)]), four", ",") == [ "one", "two (2, II)", "three ([(nested, deep)])", "four" ]



def test_split_defs():
     assert spanish_words.split_defs([ "a1, a2, a3; b1, b2", "c1, c2, c3" ]) == [['a1', 'a2', 'a3'], ['b1', 'b2'], ['c1', 'c2', 'c3']]


def test_get_split_defs():
    defs = {
            'pos': {
                '': [ "a1, a2, a3; b1, b2", "c1, c2, c3"],
                'note': [ "d1, d2; e1, e2 (stuff, more; stuff), e3; f1"]
            },
    }

    assert spanish_words.get_split_defs(defs) == [['a1', 'a2', 'a3'], ['b1', 'b2'], ['c1', 'c2', 'c3'], ['d1', 'd2'], ['e1', 'e2 (stuff, more; stuff)', 'e3'], ['f1']]

# TODO: Update this when the funcition gets fixed
def test_get_best_defs():
    defs = [['a1', 'a2', 'a3'], ['b1', 'b2'], ['c1', 'c2', 'c3'], ['d1', 'd2'], ['e1', 'e2 (stuff, more; stuff)', 'e3'], ['f1']]
    assert spanish_words.get_best_defs(defs, 2) == defs
#    assert spanish_words.get_best_defs([ ";def1", "def1-syn1", "def1-syn2", ";def2", ";def3", "def3-syn1" ], 2) == [ ";def1", ";def2" ]
#    assert spanish_words.get_best_defs([ ";def1", "def1-syn1", "def1-syn2", ";def2", ";def3", "def3-syn1" ], 3) == [ ";def1", ";def2", ";def3" ]
#    assert spanish_words.get_best_defs([ ";def1", "def1-syn1", "def1-syn2", ";def2", ";def3", "def3-syn1" ], 4) == [ ";def1", "def1-syn1", ";def2", ";def3" ]
#    assert spanish_words.get_best_defs([ ";def1", "def1-syn1", "def1-syn2", ";def2", ";def3", "def3-syn1" ], 5) == [ ";def1", "def1-syn1", ";def2", ";def3", "def3-syn1" ]

def test_defs_to_string():
    defs = [['a1', 'a2', 'a3'], ['b1', 'b2'], ['c1', 'c2', 'c3'], ['d1', 'd2'], ['e1', 'e2 (stuff, more; stuff)', 'e3'], ['f1']]
    assert spanish_words.defs_to_string(defs, "noun") == "a1, a2, a3; b1, b2; c1, c2, c3; d1, d2; e1, e2 (stuff, more; stuff), e3; f1"
    defs = [["run", "jog"], [ "sprint" ]]
    assert spanish_words.defs_to_string(defs, "verb") == "to run, jog; to sprint"

def test_filter_defs():

    defs = {
            'v': {
                'Spain': ['to a1; to a2', 'to not c1', 'to c2 (clarification, notes)'],
                '': ['to b1', 'to b2', 'to b3; to b4', 'to b5'],
                'vulgar, Chile': ['to d1']
            },
            'vr': {
                '': ['to e1']
            },
            'm': {
                '': ['new noun usage'],
                'test, dated': ['old noun usage']
            },
            'adj': {
                'obsolete': ['adj usage']
            }
    }

    # no params, shouldn't filter anything
    assert spanish_words.filter_defs(defs) == defs

    assert spanish_words.filter_defs(defs, 'noun') == {'m': {'': ['new noun usage'], 'test, dated': ['old noun usage']}}

    # filtering does *not* match notes
    assert spanish_words.filter_defs(defs, 'noun', 'test') == {'m': {'': ['new noun usage'], 'test, dated': ['old noun usage']}}

    # but instead matches definitions
    assert spanish_words.filter_defs(defs, 'noun', 'old') == {'m': {'': ['new noun usage']}}

    assert spanish_words.filter_defs(defs, 'verb') == {'v': {'Spain': ['to a1; to a2', 'to not c1', 'to c2 (clarification, notes)'], '': ['to b1', 'to b2', 'to b3; to b4', 'to b5'], 'vulgar, Chile': ['to d1']}, 'vr': {'': ['to e1']}}
    assert spanish_words.filter_defs(defs, 'vr') == {'vr': {'': ['to e1']}}
    assert spanish_words.filter_defs(defs, 'verb', 'to c') == {'v': {'Spain': ['to a1; to a2', 'to not c1'], '': ['to b1', 'to b2', 'to b3; to b4', 'to b5'], 'vulgar, Chile': ['to d1']}, 'vr': {'': ['to e1']}}

    assert spanish_words.filter_defs(defs, 'adj') == {'adj': {'obsolete': ['adj usage']}}

    # deleting all entries should clear out the list
    assert spanish_words.filter_defs(defs, 'adj', 'usage') == {}
