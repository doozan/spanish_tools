from spanish_words.wordlist import SpanishWordlist
import spanish_words.wordlist
import pytest

worddb = None

def test_init():
    global worddb
    worddb = SpanishWordlist()

# TODO:
def test_init_dictionary():
    with pytest.raises(FileNotFoundError) as e_info:
         worddb.load_dictionary("not_a_file") == "yes"

    worddb.load_dictionary("spanish_data/es-en.txt")



# TODO:
def xtest_remove_def():
    return

# TODO:
def xtest_add_def():
    return


# TODO:
def xtest_init_syns():
    return


def test_parse_line():
    res = spanish_words.wordlist.parse_line("abanderada {f} :: feminine noun of abanderado\n")
    assert res['word'] == 'abanderada'
    assert res['pos'] == 'f'
    assert res['note'] == ''
    assert res['def'] == 'feminine noun of abanderado'

    res = spanish_words.wordlist.parse_line("abandonamiento {m} [rare] :: abandonment\n")
    assert res['word'] == 'abandonamiento'
    assert res['pos'] == 'm'
    assert res['note'] == 'rare'
    assert res['def'] == 'abandonment'

    res = spanish_words.wordlist.parse_line("otólogo  :: otologist\n")
    assert res['word'] == 'otólogo'
    assert res['pos'] == ''
    assert res['note'] == ''
    assert res['def'] == 'otologist'

    res = spanish_words.wordlist.parse_line("cliente {mf} {m} [computing] :: client\n")
    assert res['word'] == 'cliente'
    assert res['pos'] == 'm'
    assert res['note'] == 'computing'
    assert res['def'] == 'client'


def test_pos_is_noun():
    assert spanish_words.wordlist.pos_is_noun("m") == True
    assert spanish_words.wordlist.pos_is_noun("m/f") == True
    assert spanish_words.wordlist.pos_is_noun("f-el") == True
    assert spanish_words.wordlist.pos_is_noun("f") == True
    assert spanish_words.wordlist.pos_is_noun("vt") == False
    assert spanish_words.wordlist.pos_is_noun("") == False


def test_pos_is_verb():
    assert spanish_words.wordlist.pos_is_verb("v") == True
    assert spanish_words.wordlist.pos_is_verb("vt") == True
    assert spanish_words.wordlist.pos_is_verb("vr") == True
    assert spanish_words.wordlist.pos_is_verb("m") == False
    assert spanish_words.wordlist.pos_is_verb("") == False


def test_common_pos():
    assert spanish_words.wordlist.common_pos("m") == "noun"
    assert spanish_words.wordlist.common_pos("m/f") == "noun"
    assert spanish_words.wordlist.common_pos("f-el") == "noun"
    assert spanish_words.wordlist.common_pos("f") == "noun"
    assert spanish_words.wordlist.common_pos("v") == "verb"
    assert spanish_words.wordlist.common_pos("vt") == "verb"
    assert spanish_words.wordlist.common_pos("vr") == "verb"
    assert spanish_words.wordlist.common_pos("xxxx") == "xxxx"
    assert spanish_words.wordlist.common_pos("adj") == "adj"
    assert spanish_words.wordlist.common_pos("") == ""

def test_clean_def():
    assert spanish_words.wordlist.clean_def("v", "to be") == "be"
    assert spanish_words.wordlist.clean_def("n", "to be") == "to be"
    assert spanish_words.wordlist.clean_def("v", "together") == "together"
    assert spanish_words.wordlist.clean_def("v", "have to go") == "have to go"


def test_should_ignore_note():
    assert spanish_words.wordlist.should_ignore_note("obsolete") == True
    assert spanish_words.wordlist.should_ignore_note("new, obsolete") == True
    assert spanish_words.wordlist.should_ignore_note("new, obsolete, test") == True
    assert spanish_words.wordlist.should_ignore_note("not yet obsolete") == False

def test_should_ignore_def():
    assert spanish_words.wordlist.should_ignore_def("obsolete spelling of isla") == True
    assert spanish_words.wordlist.should_ignore_def("obsolete form of isla") == True
    assert spanish_words.wordlist.should_ignore_def("obsolete is the meaning of the word") == False
    assert spanish_words.wordlist.should_ignore_def("obsolete") == False

def test_split_sep():
    assert spanish_words.wordlist.split_sep(None, ",") == []
    assert spanish_words.wordlist.split_sep("", ",") == []
    assert spanish_words.wordlist.split_sep("one", ",") == ["one"]
    assert spanish_words.wordlist.split_sep("one,", ",") == ["one"]
    assert spanish_words.wordlist.split_sep("one, two", ",") == ["one", "two"]
    assert spanish_words.wordlist.split_sep("one; two, three", ",") == ["one; two", "three"]
    assert spanish_words.wordlist.split_sep("one; two, three", ";") == ["one", "two, three"]
    assert spanish_words.wordlist.split_sep("one, two (2, II), three", ",") == [ "one", "two (2, II)", "three" ]
    assert spanish_words.wordlist.split_sep("one, two (2, II), three ([(nested, deep)]), four", ",") == [ "one", "two (2, II)", "three ([(nested, deep)])", "four" ]



def test_split_defs():
     assert spanish_words.wordlist.split_defs("n", [ "a1, a2, a3; b1, b2", "c1, c2, c3" ]) == [['a1', 'a2', 'a3'], ['b1', 'b2'], ['c1', 'c2', 'c3']]
     assert spanish_words.wordlist.split_defs("v", [ "a1, to a2, a3; to b1, b2", "c1, c2, c3" ]) == [['a1', 'a2', 'a3'], ['b1', 'b2'], ['c1', 'c2', 'c3']]


def test_get_split_defs():
    defs = {
            'pos': {
                '': [ "a1, a2, a3; b1, b2", "c1, c2, c3"],
                'note': [ "d1, d2; e1, e2 (stuff, more; stuff), e3; f1"]
            },
    }

    assert spanish_words.wordlist.get_split_defs(defs) == [['a1', 'a2', 'a3'], ['b1', 'b2'], ['c1', 'c2', 'c3'], ['d1', 'd2'], ['e1', 'e2 (stuff, more; stuff)', 'e3'], ['f1']]

# TODO: Update this when the funcition gets fixed
def test_get_best_defs():
    defs = [['a1', 'a2', 'a3'], ['b1', 'b2'], ['c1', 'c2', 'c3'], ['d1', 'd2'], ['e1', 'e2 (stuff, more; stuff)', 'e3'], ['f1']]
    assert spanish_words.wordlist.get_best_defs(defs, 2) == defs
#    assert spanish_words.wordlist.get_best_defs([ ";def1", "def1-syn1", "def1-syn2", ";def2", ";def3", "def3-syn1" ], 2) == [ ";def1", ";def2" ]
#    assert spanish_words.wordlist.get_best_defs([ ";def1", "def1-syn1", "def1-syn2", ";def2", ";def3", "def3-syn1" ], 3) == [ ";def1", ";def2", ";def3" ]
#    assert spanish_words.wordlist.get_best_defs([ ";def1", "def1-syn1", "def1-syn2", ";def2", ";def3", "def3-syn1" ], 4) == [ ";def1", "def1-syn1", ";def2", ";def3" ]
#    assert spanish_words.wordlist.get_best_defs([ ";def1", "def1-syn1", "def1-syn2", ";def2", ";def3", "def3-syn1" ], 5) == [ ";def1", "def1-syn1", ";def2", ";def3", "def3-syn1" ]

#def test_defs_to_string():
#    defs = [['a1', 'a2', 'a3'], ['b1', 'b2'], ['c1', 'c2', 'c3'], ['d1', 'd2'], ['e1', 'e2 (stuff, more; stuff)', 'e3'], ['f1']]
#    assert spanish_words.wordlist.defs_to_string(defs, "noun") == "a1, a2, a3; b1, b2; c1, c2, c3; d1, d2; e1, e2 (stuff, more; stuff), e3; f1"
#    defs = [["run", "jog"], [ "sprint" ]]
#    assert spanish_words.wordlist.defs_to_string(defs, "verb") == "to run, jog; to sprint"

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
    assert spanish_words.wordlist.filter_defs(defs) == defs

    assert spanish_words.wordlist.filter_defs(defs, 'noun') == {'m': {'': ['new noun usage'], 'test, dated': ['old noun usage']}}

    # filtering does *not* match notes
    assert spanish_words.wordlist.filter_defs(defs, 'noun', 'test') == {'m': {'': ['new noun usage'], 'test, dated': ['old noun usage']}}

    # but instead matches definitions
    assert spanish_words.wordlist.filter_defs(defs, 'noun', 'old') == {'m': {'': ['new noun usage']}}

    assert spanish_words.wordlist.filter_defs(defs, 'verb') == {'v': {'Spain': ['to a1; to a2', 'to not c1', 'to c2 (clarification, notes)'], '': ['to b1', 'to b2', 'to b3; to b4', 'to b5'], 'vulgar, Chile': ['to d1']}, 'vr': {'': ['to e1']}}
    assert spanish_words.wordlist.filter_defs(defs, 'vr') == {'vr': {'': ['to e1']}}
    assert spanish_words.wordlist.filter_defs(defs, 'verb', 'to c') == {'v': {'Spain': ['to a1; to a2', 'to not c1'], '': ['to b1', 'to b2', 'to b3; to b4', 'to b5'], 'vulgar, Chile': ['to d1']}, 'vr': {'': ['to e1']}}

    assert spanish_words.wordlist.filter_defs(defs, 'adj') == {'adj': {'obsolete': ['adj usage']}}

    # deleting all entries should clear out the list
    assert spanish_words.wordlist.filter_defs(defs, 'adj', 'usage') == {}


def test_get_all_pos():
    assert worddb.get_all_pos("casa") == ["noun"]


def test_has_word():
    assert worddb.has_word("casa", "noun") == True
    assert worddb.has_word("tener", "verb") == True
    assert worddb.has_word("casa", "verb") == False
    assert worddb.has_word("notaword", "verb") == False
    assert worddb.has_word("", "verb") == False
    assert worddb.has_word("casa", "") == True
    assert worddb.has_word("dos", "num") == True
    assert worddb.has_word("dos", "noun") == False



def test_lookup():

    res = worddb.lookup("gafa", "noun")
    assert res == {'f': {'': 'grapple; clamp', 'chiefly in the plural': 'eyeglasses'}}

    # ommiting pos should work
    res = worddb.lookup("gafa", "")
    assert res == {'f': {'': 'grapple; clamp', 'chiefly in the plural': 'eyeglasses'}}

    # m/f detection
    res = worddb.lookup("alumno", "noun")
    assert res == {'m/f': {'': 'pupil, student'}}

    res = worddb.lookup("abuelo", "noun")
    assert res == {'m/f': {'f, Mexico': 'a kind of flying ant', 'f, colloquial': 'old woman', 'm': "grandfather; loose tufts of hair in the nape when one's hair is messed up", 'm, colloquial, affectionate': 'an elderly person'}}

    # f-el detection
    res = worddb.lookup("alma", "noun")
    assert res == {'f-el': {'': 'soul'}}

    # m-f detection
    res = worddb.lookup("batería", "noun")
    assert res == {'m-f': {'f': 'large battery; drum set; set (collection of things)', 'mf': 'drummer'}}

    # verb
    res = worddb.lookup("arrestar", "verb")
    assert res == {'v': {'': 'to arrest'}}

    # filter everything out
    res = worddb.lookup("arrestar", "noun")
    assert res == {}



def test_is_feminized_noun():
    assert worddb.is_feminized_noun("hermana", "hermano") == True
    assert worddb.is_feminized_noun("hermano", "hermano") == False
    assert worddb.is_feminized_noun("casa", "caso") == False
    assert worddb.is_feminized_noun("hamburguesa", "hamburgueso") == False
    assert worddb.is_feminized_noun("profesora", "profesor") == True
    assert worddb.is_feminized_noun("alcaldesa", "alcalde") == True
    assert worddb.is_feminized_noun("campeona", "campeón") == True


def test_get_feminine_noun():
    assert worddb.get_feminine_noun("hermano") == "hermana"
#    assert worddb.get_feminine_noun("camarero") == "camarera"
    assert worddb.get_feminine_noun("hermana") == None
    assert worddb.get_feminine_noun("caso") == None
    assert worddb.get_feminine_noun("hamburgueso") == None

    # Has feminine noun, but not for the primary definition
    assert worddb.get_feminine_noun("pato") == None


    # Other word endings
    assert worddb.get_feminine_noun("jefe") == "jefa"
    assert worddb.get_feminine_noun("doctor") == "doctora"
    assert worddb.get_feminine_noun("alcalde") == "alcaldesa"
    assert worddb.get_feminine_noun("tigre") == "tigresa"

    # feminine loses accent on last vowel
    assert worddb.get_feminine_noun("campeón") == "campeona"
    assert worddb.get_feminine_noun("taiwanés") == "taiwanesa"



def test_get_masculine_noun():
    assert worddb.get_masculine_noun("hermana") == "hermano"
    assert worddb.get_masculine_noun("casa") == None
    assert worddb.get_masculine_noun("hamburguesa") == None

