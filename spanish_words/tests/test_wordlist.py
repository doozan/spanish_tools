import pytest
from spanish_words.wordlist import SpanishWordlist
import spanish_words.wordlist
import os

obj = None


def test_general(tmp_path):
    wordlist = SpanishWordlist()

    datafile = tmp_path / "dictionary.txt"
    print(datafile)
    with open(datafile, "w") as outfile:
        outfile.write(
"""amigo {m} :: friend
amiga {f} :: feminine noun of amigo, friend
enemigo {m} :: foe, enemy
casa {f} :: house
chico {adj} :: small
chico {m} :: boy; kid
chica {f} :: feminine noun of chico, girl
chica {f} [colloquial] :: gal, chick
cura {f} :: cure (something that restores good health)
cura {m} :: priest
cura {f} [Colombia, dated] :: avocado"""
        )
    wordlist.load_dictionary(datafile)

    assert wordlist.has_word("amigo") == True
    assert wordlist.has_word("amigo", "noun") == True
    assert wordlist.has_word("amigo", "verb") == False
    assert wordlist.has_word("myword", "noun") == False

    test_def = wordlist.parse_line("myword {m} :: my def1, def2; def 3\n")
    test_def2 = wordlist.parse_line("myword {m} :: def 4\n")
    assert test_def == {'word': 'myword', 'pos': 'm', 'note': '', 'def': 'my def1, def2; def 3'}

    wordlist.add_def(test_def)
    wordlist.add_def(test_def2)
    assert wordlist.has_word("myword", "noun") == True

    rm_def = wordlist.parse_line("myword")
    wordlist.remove_def(rm_def)
    assert wordlist.has_word("myword", "noun") == False

    wordlist.add_def(test_def)
    assert wordlist.has_word("myword", "noun") == True

    rm_def = wordlist.parse_line("myword {m}")
    wordlist.remove_def(rm_def)
    assert wordlist.has_word("myword", "noun") == False


    #test_remove_def():
    #test_add_def():

def test_init():
    global obj
    obj = SpanishWordlist()

def test_init_dictionary():
    load_dictionary = obj.load_dictionary

    with pytest.raises(FileNotFoundError) as e_info:
         load_dictionary("not_a_file") == "yes"

    load_dictionary("spanish_data/es-en.txt")

def test_get_all_pos():
    get_all_pos = obj.get_all_pos
    assert get_all_pos("notaword") == []
    assert get_all_pos("hablar") == ["verb"]
    assert get_all_pos("casa") == ["noun"]
    assert get_all_pos("rojo") == ["adj", "noun"]

def test_has_word():
    has_word = obj.has_word
    assert has_word("", "verb") == False
    assert has_word("notaword", "verb") == False
    assert has_word("casa", "noun") == True
    assert has_word("tener", "verb") == True
    assert has_word("casa", "verb") == False
    assert has_word("casa", "") == True
    assert has_word("dos", "num") == True
    assert has_word("dos", "noun") == False
    assert has_word("verde", "adj") == True

def test_has_verb():
    has_verb = obj.has_verb
    assert has_verb("tener") == True
    assert has_verb("tenor") == False

def test_has_noun():
    has_noun = obj.has_noun
    assert has_noun("casa") == True
    assert has_noun("tener") == False

def test_do_analysis():
    do_analysis = obj.do_analysis

    defs = {
            'm': { '': ['male usage'] },
            'f': { '': ['female usage'] }
    }
    assert do_analysis("hacer", defs) == {'m-f': {'m': ['male usage'], 'f': ['female usage']}}

    defs = {
            'mf': { '': ['male/female usage'] },
            'f': { '': ['female only usage'] }
    }
    assert do_analysis("hacer", defs) == {'m-f': {'f': ['female only usage'], 'mf': ['male/female usage']}}


    # doing a lookup for "amigo" should detect female use and change 'm' to 'm/f'
    defs = { 'm': { '': ['usage'] } }
    assert do_analysis("amigo", defs) == {'m/f': {'': ['usage']}}


    # doing a lookup for "tío" should detect female use and change 'm' to 'm/f' and add the extra usage
    defs = { 'm': { '': ['usage'] } }
    assert do_analysis("tío", defs) == {'m/f': {'m': ['usage'], 'f, colloquial, Spain': ['woman, chick']}}

    defs = { 'f': { '': ['water'] } }
    assert do_analysis("agua", defs) == { 'f-el': { '': ['water'] } }

    return



def test_lookup():
    lookup = obj.lookup

    res = lookup("gafa", "noun")
    assert res == {'f': {'': 'grapple; clamp', 'chiefly in the plural': 'eyeglasses'}}

    # ommiting pos should work
    res = lookup("gafa", "")
    assert res == {'f': {'': 'grapple; clamp', 'chiefly in the plural': 'eyeglasses'}}

    # m/f detection
    res = lookup("alumno", "noun")
    assert res == {'m/f': {'': 'pupil, student'}}

    res = lookup("abuelo", "noun")
    assert res == {'m/f': {'f': 'grandmother', 'm': "grandfather; loose tufts of hair in the nape when one's hair is messed up", 'm, colloquial, affectionate': 'an elderly person'}}

    # f-el detection
    res = lookup("alma", "noun")
    assert res == {'f-el': {'': 'soul'}}

    # m-f detection
    res = lookup("batería", "noun")
    assert res == {'m-f': {'f': 'large battery; drum set; set (collection of things)', 'mf': 'drummer'}}

    # verb
    res = lookup("arrestar", "verb")
    assert res == {'v': {'': 'to arrest'}}

    # filter everything out
    res = lookup("arrestar", "noun")
    assert res == {}



def test_is_feminized_noun():
    is_feminized_noun = obj.is_feminized_noun
    assert is_feminized_noun("hermana", "hermano") == True
    assert is_feminized_noun("hermano", "hermano") == False
    assert is_feminized_noun("casa", "caso") == False
    assert is_feminized_noun("hamburguesa", "hamburgueso") == False
    assert is_feminized_noun("profesora", "profesor") == True
    assert is_feminized_noun("alcaldesa", "alcalde") == True
    assert is_feminized_noun("campeona", "campeón") == True


def test_get_feminine_noun():
    get_feminine_noun = obj.get_feminine_noun
    assert get_feminine_noun("hermano") == "hermana"
#    assert get_feminine_noun("camarero") == "camarera"
    assert get_feminine_noun("hermana") == None
    assert get_feminine_noun("caso") == None
    assert get_feminine_noun("hamburgueso") == None

    # Has feminine noun, but not for the primary definition
    assert get_feminine_noun("pato") == None


    # Other word endings
    assert get_feminine_noun("jefe") == "jefa"
    assert get_feminine_noun("doctor") == "doctora"
    assert get_feminine_noun("alcalde") == "alcaldesa"
    assert get_feminine_noun("tigre") == "tigresa"

    # feminine loses accent on last vowel
    assert get_feminine_noun("campeón") == "campeona"
    assert get_feminine_noun("taiwanés") == "taiwanesa"



def test_get_masculine_noun():
    get_masculine_noun = obj.get_masculine_noun
    assert get_masculine_noun("hermana") == "hermano"
    assert get_masculine_noun("casa") == None
    assert get_masculine_noun("hamburguesa") == None

    assert get_masculine_noun("jefa") == "jefe"
    assert get_masculine_noun("campeona") == "campeón"
    assert get_masculine_noun("alcaldesa") == "alcalde"
    assert get_masculine_noun("doctora") == "doctor"



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
    res = obj.parse_line("abanderada {f} :: feminine noun of abanderado\n")
    assert res['word'] == 'abanderada'
    assert res['pos'] == 'f'
    assert res['note'] == ''
    assert res['def'] == 'feminine noun of abanderado'

    res = obj.parse_line("abandonamiento {m} [rare] :: abandonment\n")
    assert res['word'] == 'abandonamiento'
    assert res['pos'] == 'm'
    assert res['note'] == 'rare'
    assert res['def'] == 'abandonment'

    res = obj.parse_line("otólogo  :: otologist\n")
    assert res['word'] == 'otólogo'
    assert res['pos'] == ''
    assert res['note'] == ''
    assert res['def'] == 'otologist'

    res = obj.parse_line("cliente {mf} {m} [computing] :: client\n")
    assert res['word'] == 'cliente'
    assert res['pos'] == 'm'
    assert res['note'] == 'computing'
    assert res['def'] == 'client'


def test_pos_is_noun():
    assert obj.pos_is_noun("m") == True
    assert obj.pos_is_noun("m/f") == True
    assert obj.pos_is_noun("f-el") == True
    assert obj.pos_is_noun("f") == True
    assert obj.pos_is_noun("vt") == False
    assert obj.pos_is_noun("") == False


def test_pos_is_verb():
    assert obj.pos_is_verb("v") == True
    assert obj.pos_is_verb("vt") == True
    assert obj.pos_is_verb("vr") == True
    assert obj.pos_is_verb("m") == False
    assert obj.pos_is_verb("") == False


def test_common_pos():
    assert obj.common_pos("m") == "noun"
    assert obj.common_pos("m/f") == "noun"
    assert obj.common_pos("f-el") == "noun"
    assert obj.common_pos("f") == "noun"
    assert obj.common_pos("v") == "verb"
    assert obj.common_pos("vt") == "verb"
    assert obj.common_pos("vr") == "verb"
    assert obj.common_pos("xxxx") == "xxxx"
    assert obj.common_pos("adj") == "adj"
    assert obj.common_pos("") == ""

def test_clean_def():
    assert obj.clean_def("v", "to be") == "be"
    assert obj.clean_def("n", "to be") == "to be"
    assert obj.clean_def("v", "together") == "together"
    assert obj.clean_def("v", "have to go") == "have to go"


def test_should_ignore_note():
    should_ignore_note = obj.should_ignore_note
    assert should_ignore_note("obsolete") == True
    assert should_ignore_note("new, obsolete") == True
    assert should_ignore_note("new, obsolete, test") == True
    assert should_ignore_note("not yet obsolete") == False

def test_should_ignore_def():
    should_ignore_def = obj.should_ignore_def
    assert should_ignore_def("obsolete spelling of isla") == True
    assert should_ignore_def("obsolete form of isla") == True
    assert should_ignore_def("obsolete is the meaning of the word") == False
    assert should_ignore_def("obsolete") == False

def test_split_sep():
    assert obj.split_sep(None, ",") == []
    assert obj.split_sep("", ",") == []
    assert obj.split_sep("one", ",") == ["one"]
    assert obj.split_sep("one,", ",") == ["one"]
    assert obj.split_sep("one, two", ",") == ["one", "two"]
    assert obj.split_sep("one; two, three", ",") == ["one; two", "three"]
    assert obj.split_sep("one; two, three", ";") == ["one", "two, three"]
    assert obj.split_sep("one, two (2, II), three", ",") == [ "one", "two (2, II)", "three" ]
    assert obj.split_sep("one, two (2, II), three ([(nested, deep)]), four", ",") == [ "one", "two (2, II)", "three ([(nested, deep)])", "four" ]



def test_split_defs():
     assert obj.split_defs("n", [ "a1, a2, a3; b1, b2", "c1, c2, c3" ]) == [['a1', 'a2', 'a3'], ['b1', 'b2'], ['c1', 'c2', 'c3']]
     assert obj.split_defs("v", [ "a1, to a2, a3; to b1, b2", "c1, c2, c3" ]) == [['a1', 'a2', 'a3'], ['b1', 'b2'], ['c1', 'c2', 'c3']]


def test_get_split_defs():
    defs = {
            'pos': {
                '': [ "a1, a2, a3; b1, b2", "c1, c2, c3"],
                'note': [ "d1, d2; e1, e2 (stuff, more; stuff), e3; f1"]
            },
    }

    assert obj.get_split_defs(defs) == [['a1', 'a2', 'a3'], ['b1', 'b2'], ['c1', 'c2', 'c3'], ['d1', 'd2'], ['e1', 'e2 (stuff, more; stuff)', 'e3'], ['f1']]

# TODO: Update this when the funcition gets fixed
def test_get_best_defs():
    defs = [['a1', 'a2', 'a3'], ['b1', 'b2'], ['c1', 'c2', 'c3'], ['d1', 'd2'], ['e1', 'e2 (stuff, more; stuff)', 'e3'], ['f1']]
    assert obj.get_best_defs(defs, 2) == defs
#    assert obj.get_best_defs([ ";def1", "def1-syn1", "def1-syn2", ";def2", ";def3", "def3-syn1" ], 2) == [ ";def1", ";def2" ]
#    assert obj.get_best_defs([ ";def1", "def1-syn1", "def1-syn2", ";def2", ";def3", "def3-syn1" ], 3) == [ ";def1", ";def2", ";def3" ]
#    assert obj.get_best_defs([ ";def1", "def1-syn1", "def1-syn2", ";def2", ";def3", "def3-syn1" ], 4) == [ ";def1", "def1-syn1", ";def2", ";def3" ]
#    assert obj.get_best_defs([ ";def1", "def1-syn1", "def1-syn2", ";def2", ";def3", "def3-syn1" ], 5) == [ ";def1", "def1-syn1", ";def2", ";def3", "def3-syn1" ]

#def test_defs_to_string():
#    defs = [['a1', 'a2', 'a3'], ['b1', 'b2'], ['c1', 'c2', 'c3'], ['d1', 'd2'], ['e1', 'e2 (stuff, more; stuff)', 'e3'], ['f1']]
#    assert obj.defs_to_string(defs, "noun") == "a1, a2, a3; b1, b2; c1, c2, c3; d1, d2; e1, e2 (stuff, more; stuff), e3; f1"
#    defs = [["run", "jog"], [ "sprint" ]]
#    assert obj.defs_to_string(defs, "verb") == "to run, jog; to sprint"

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
    assert obj.filter_defs(defs) == defs

    assert obj.filter_defs(defs, 'noun') == {'m': {'': ['new noun usage'], 'test, dated': ['old noun usage']}}

    # filtering does *not* match notes
    assert obj.filter_defs(defs, 'noun', 'test') == {'m': {'': ['new noun usage'], 'test, dated': ['old noun usage']}}

    # but instead matches definitions
    assert obj.filter_defs(defs, 'noun', 'old') == {'m': {'': ['new noun usage']}}

    assert obj.filter_defs(defs, 'verb') == {'v': {'Spain': ['to a1; to a2', 'to not c1', 'to c2 (clarification, notes)'], '': ['to b1', 'to b2', 'to b3; to b4', 'to b5'], 'vulgar, Chile': ['to d1']}, 'vr': {'': ['to e1']}}
    assert obj.filter_defs(defs, 'vr') == {'vr': {'': ['to e1']}}
    assert obj.filter_defs(defs, 'verb', 'to c') == {'v': {'Spain': ['to a1; to a2', 'to not c1'], '': ['to b1', 'to b2', 'to b3; to b4', 'to b5'], 'vulgar, Chile': ['to d1']}, 'vr': {'': ['to e1']}}

    assert obj.filter_defs(defs, 'adj') == {'adj': {'obsolete': ['adj usage']}}

    # deleting all entries should clear out the list
    assert obj.filter_defs(defs, 'adj', 'usage') == {}
