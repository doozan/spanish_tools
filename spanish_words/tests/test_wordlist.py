import pytest
from spanish_words.wordlist import SpanishWordlist
from spanish_words.verbs import SpanishVerbs
from spanish_words.nouns import SpanishNouns
import spanish_words.wordlist
import os

def test_general(tmp_path):

    datafile = tmp_path / "dictionary.txt"
    print(datafile)
    with open(datafile, "w") as outfile:
        outfile.write(
"""amigo {m} :: friend
amiga {f} :: feminine noun of amigo, friend
casa {f} :: house
chico {adj} :: small
chico {m} :: boy; kid
chica {f} :: feminine noun of chico, girl
chica {f} [colloquial] :: gal, chick
cura {f} :: cure (something that restores good health)
cura {m} :: priest
cura {f} [Colombia, dated] :: avocado
enemigo {m} :: foe, enemy
mino {meta-noun} :: f=mina; fpl=minas; pl=minos
mino {m} [Argentina, Chile, colloquial] :: boy (young man)
mina {meta-noun} :: pl=minas
mina {f} :: mine (excavation from which ore is taken)
yuso {adv} [obsolete] :: down
zelo {m} :: obsolete form of celo
test {m} :: testing
test {m} :: obsoleto form of terst
""")
    wordlist = SpanishWordlist(dictionary="dictionary.txt", data_dir=tmp_path, custom_dir=tmp_path)
   # wordlist.load_dictionary("dictionary.txt", tmp_path, tmp_path)

    assert wordlist._has_word("amigo") == True
    assert wordlist._has_word("amigo", "noun") == True
    assert wordlist._has_word("amigo", "verb") == False
    assert wordlist._has_word("myword", "noun") == False
#    assert wordlist._has_word("yuso") == False
#    assert wordlist._has_word("zelo") == False
#    assert wordlist.get_lemma("zelo") == "celo"
#    assert wordlist._has_word("test") == True
#    assert wordlist.get_lemma("terst") == None
    assert wordlist.get_lemma("minas", "noun") == "mina"

    test_def = wordlist.parse_line("myword {m} :: my def1, def2; def 3\n")
    assert test_def == {'word': 'myword', 'pos': 'm', 'note': '', 'syn': '', 'def': 'my def1, def2; def 3'}

    test_def = wordlist.parse_line("alma {f} | ánima :: soul\n")
    assert test_def == {'word': 'alma', 'pos': 'f', 'note': '', 'syn': 'ánima', 'def': 'soul'}

    test_def = wordlist.parse_line("myword {m} [note1, note2] :: my def1, def2; def 3\n")
    assert test_def == {'word': 'myword', 'pos': 'm', 'note': 'note1, note2', 'syn': '',  'def': 'my def1, def2; def 3'}

    test_def = wordlist.parse_line("myword {m} [note1, note2] | syn1; syn2 :: my def1, def2; def 3\n")
    assert test_def == {'word': 'myword', 'pos': 'm', 'note': 'note1, note2', 'syn': 'syn1; syn2', 'def': 'my def1, def2; def 3'}

    test_def = wordlist.parse_line("myword {m} | syn1; syn2 :: my def1, def2; def 3\n")
    assert test_def == {'word': 'myword', 'pos': 'm', 'note': '', 'syn': 'syn1; syn2', 'def': 'my def1, def2; def 3'}

    test_def2 = wordlist.parse_line("myword {m} :: def 4\n")

    wordlist.add_def(test_def)
    wordlist.add_def(test_def2)
    assert wordlist._has_word("myword", "noun") == True

    rm_def = wordlist.parse_line("myword")
    wordlist.remove_def(rm_def)
    assert wordlist._has_word("myword", "noun") == False

    wordlist.add_def(test_def)
    assert wordlist._has_word("myword", "noun") == True

    rm_def = wordlist.parse_line("myword {m}")
    wordlist.remove_def(rm_def)
    assert wordlist._has_word("myword", "noun") == False

    # don't use process line
    nmeta_def = wordlist.parse_line("myword {meta-noun} :: f=mywordalisa; pl=mywordz; pl=mywordzzz\n")
    wordlist.add_def(test_def)
    wordlist.add_forms(nmeta_def)
    assert wordlist._has_word("myword") == True
    assert wordlist._has_word("mywordalisa") == False
    assert wordlist._has_word("mywordz") == False

    assert wordlist.get_lemma("mywordalisa", "noun") == "myword"
    assert wordlist.get_lemma("mywordz", "noun") == "myword"
    assert wordlist.get_lemma("mywordzzz", "noun") == "myword"
    assert wordlist.get_feminine_noun("myword") == "mywordalisa"
#    assert wordlist.get_masculine_noun("mywordalisa") == None

    test_def = wordlist.parse_line("mywordalisa {f} :: def 4\n")
    nmeta_def = wordlist.parse_line("mywordalisa {meta-noun} :: m=myword\n")
    wordlist.add_def(test_def)
    wordlist.add_forms(nmeta_def)
    assert wordlist._has_word("mywordalisa") == True
#    assert wordlist.get_masculine_noun("mywordalisa") == "myword"
    assert wordlist.get_lemma("mywordalisa", "noun") == "myword"

    verb_def = wordlist.parse_line("myverbolver {v} :: def\n")
    wordlist.add_def(verb_def)
    vmeta_def = wordlist.parse_line("myverbolver {meta-verb} :: pattern=-olver; stem=abs")
    wordlist.add_vmeta(vmeta_def)
    assert wordlist._has_word("myverbolver", "verb") == True
#    verb = SpanishVerbs(None)
#    assert verb.conjugate("myverbolver") == {1: ['myverbolver'], 2: ['myverbolviendo'], 3: ['myverbolvido'], 4: ['myverbolvida'], 5: ['myverbolvidos'], 6: ['myverbolvidas'], 7: ['myverbolvo'], 8: ['myverbolves'], 9: ['myverbolvés'], 10: ['myverbolve'], 11: ['myverbolvemos'], 12: ['myverbolvéis'], 13: ['myverbolven'], 14: ['myverbolvía'], 15: ['myverbolvías'], 16: ['myverbolvía'], 17: ['myverbolvíamos'], 18: ['myverbolvíais'], 19: ['myverbolvían'], 20: ['myverbolví'], 21: ['myverbolviste'], 22: ['myverbolvió'], 23: ['myverbolvimos'], 24: ['myverbolvisteis'], 25: ['myverbolvieron'], 26: ['myverbolveré'], 27: ['myverbolverás'], 28: ['myverbolverá'], 29: ['myverbolveremos'], 30: ['myverbolveréis'], 31: ['myverbolverán'], 32: ['myverbolvería'], 33: ['myverbolverías'], 34: ['myverbolvería'], 35: ['myverbolveríamos'], 36: ['myverbolveríais'], 37: ['myverbolverían'], 38: ['myverbolva'], 39: ['myverbolvas'], 40: ['myverbolvás'], 41: ['myverbolva'], 42: ['myverbolvamos'], 43: ['myverbolváis'], 44: ['myverbolvan'], 45: ['myverbolviera'], 46: ['myverbolvieras'], 47: ['myverbolviera'], 48: ['myverbolviéramos'], 49: ['myverbolvierais'], 50: ['myverbolvieran'], 51: ['myverbolviese'], 52: ['myverbolvieses'], 53: ['myverbolviese'], 54: ['myverbolviésemos'], 55: ['myverbolvieseis'], 56: ['myverbolviesen'], 57: ['myverbolviere'], 58: ['myverbolvieres'], 59: ['myverbolviere'], 60: ['myverbolviéremos'], 61: ['myverbolviereis'], 62: ['myverbolvieren'], 63: ['myverbolve'], 64: ['myverbolvé'], 65: ['myverbolva'], 66: ['myverbolvamos'], 67: ['myverbolved'], 68: ['myverbolvan'], 69: ['myverbolvas'], 70: ['myverbolva'], 71: ['myverbolvamos'], 72: ['myverbolváis'], 73: ['myverbolvan']}



#def test_init_dictionary():
#    load_dictionary = obj.load_dictionary
#
#    with pytest.raises(FileNotFoundError) as e_info:
#         load_dictionary("not_a_file","","") == "yes"
#
#    load_dictionary("es-en.txt", "../spanish_data", "../spanish_custom")

def test_get_all_pos(wordlist):
    get_all_pos = wordlist.get_all_pos
    assert list(get_all_pos("notaword")) == []
    assert list(get_all_pos("hablar")) == ["verb"]
    assert list(get_all_pos("casa")) == ["noun"]
    assert list(get_all_pos("rojo")) == ["adj", "noun"]

def test_has_word(wordlist):
    has_word = wordlist._has_word
    assert has_word("", "verb") == False
    assert has_word("notaword", "verb") == False
    assert has_word("casa", "noun") == True
    assert has_word("tener", "verb") == True
    assert has_word("casa", "verb") == False
    assert has_word("casa", "") == True
    assert has_word("dos", "num") == True
    assert has_word("dos", "noun") == False
    assert has_word("verde", "adj") == True

def test_has_verb(wordlist):
    has_verb = wordlist.has_verb
    assert has_verb("tener") == True
    assert has_verb("tenor") == False

def test_has_noun(wordlist):
    has_noun = wordlist.has_noun
    assert has_noun("casa") == True
    assert has_noun("tener") == False

def test_do_analysis(wordlist):
    do_analysis = wordlist.do_analysis

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
    assert do_analysis("amigo", defs) == {'m/f': {'f': ['feminine noun of amigo, friend'], 'm': ['usage']}}

    # doing a lookup for "tío" should detect female use and change 'm' to 'm/f' and add the extra usage
    defs = { 'm': { '': ['usage'] } }
    assert do_analysis("tío", defs) == {'m/f': {'m': ['usage'], 'f': ['feminine noun of tío; aunt; the sister of either parent'], 'f, colloquial, Spain': ['woman, chick']}}

    defs = { 'f': { '': ['water'] } }
    assert do_analysis("agua", defs) == { 'f-el': { '': ['water'] } }

    return



def test_lookup(wordlist):
    lookup = wordlist.lookup

    res = lookup("gafa", "noun")
    assert res == {'f': {'': 'grapple; clamp', 'chiefly in the plural': 'eyeglasses'}}

    # ommiting pos should work
    res = lookup("gafa", "")
    assert res == {'f': {'': 'grapple; clamp', 'chiefly in the plural': 'eyeglasses'}}

    # m/f detection
    res = lookup("alumno", "noun")
    assert res == {'m/f': {'': 'pupil, student, learner'}}

    res = lookup("abuelo", "noun")
    assert res == {'m/f': {'f': 'grandmother, feminine noun of abuelo', 'f, colloquial': 'old woman', 'm': 'grandfather', 'm, colloquial, endearing': 'an elderly person'}} 

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
#    res = lookup("arrestar", "noun")
#    assert res == {}



def test_get_feminine_noun(wordlist):
    get_feminine_noun = wordlist.get_feminine_noun
    assert get_feminine_noun("hermano") == "hermana"
#    assert get_feminine_noun("camarero") == "camarera"
    assert get_feminine_noun("hermana") == None
    assert get_feminine_noun("caso") == None
#    assert get_feminine_noun("hamburgueso") == None

    # Other word endings
    assert get_feminine_noun("jefe") == "jefa"
    assert get_feminine_noun("doctor") == "doctora"
    assert get_feminine_noun("alcalde") == "alcaldesa"
    assert get_feminine_noun("tigre") == "tigresa"

    # feminine loses accent on last vowel
    assert get_feminine_noun("campeón") == "campeona"
    assert get_feminine_noun("taiwanés") == "taiwanesa"



# TODO:
def xtest_remove_def():
    return

# TODO:
def xtest_add_def():
    return


# TODO:
def xtest_init_syns():
    return


def test_parse_line(wordlist):
    parse_line = wordlist.parse_line

    res = parse_line("abanderada {f} :: feminine noun of abanderado\n")
    assert res['word'] == 'abanderada'
    assert res['pos'] == 'f'
    assert res['note'] == ''
    assert res['def'] == 'feminine noun of abanderado'

    res = parse_line("abandonamiento {m} [rare] :: abandonment\n")
    assert res['word'] == 'abandonamiento'
    assert res['pos'] == 'm'
    assert res['note'] == 'rare'
    assert res['def'] == 'abandonment'

    res = parse_line("otólogo  :: otologist\n")
    assert res['word'] == 'otólogo'
    assert res['pos'] == ''
    assert res['note'] == ''
    assert res['def'] == 'otologist'

    res = parse_line("cliente {mf} {m} [computing] :: client\n")
    assert res['word'] == 'cliente'
    assert res['pos'] == 'm'
    assert res['note'] == 'computing'
    assert res['def'] == 'client'


def test_pos_is_noun(wordlist):
    pos_is_noun = wordlist.pos_is_noun

    assert pos_is_noun("m") == True
    assert pos_is_noun("m/f") == True
    assert pos_is_noun("f-el") == True
    assert pos_is_noun("f") == True
    assert pos_is_noun("vt") == False
    assert pos_is_noun("") == False


def test_pos_is_verb(wordlist):
    pos_is_verb = wordlist.pos_is_verb

    assert pos_is_verb("v") == True
    assert pos_is_verb("vt") == True
    assert pos_is_verb("vr") == True
    assert pos_is_verb("m") == False
    assert pos_is_verb("") == False


def test_common_pos(wordlist):
    common_pos = wordlist.common_pos

    assert common_pos("m") == "noun"
    assert common_pos("m/f") == "noun"
    assert common_pos("f-el") == "noun"
    assert common_pos("f") == "noun"
    assert common_pos("v") == "verb"
    assert common_pos("vt") == "verb"
    assert common_pos("vr") == "verb"
    assert common_pos("xxxx") == "xxxx"
    assert common_pos("adj") == "adj"
    assert common_pos("") == ""

def test_clean_def(wordlist):
    clean_def = wordlist.clean_def
    assert clean_def("v", "to be") == "be"
    assert clean_def("n", "to be") == "to be"
    assert clean_def("v", "together") == "together"
    assert clean_def("v", "have to go") == "have to go"


def test_split_sep(wordlist):
    split_sep = wordlist.split_sep
    assert split_sep(None, ",") == []
    assert split_sep("", ",") == []
    assert split_sep("one", ",") == ["one"]
    assert split_sep("one,", ",") == ["one"]
    assert split_sep("one, two", ",") == ["one", "two"]
    assert split_sep("one; two, three", ",") == ["one; two", "three"]
    assert split_sep("one; two, three", ";") == ["one", "two, three"]
    assert split_sep("one, two (2, II), three", ",") == [ "one", "two (2, II)", "three" ]
    assert split_sep("one, two (2, II), three ([(nested, deep)]), four", ",") == [ "one", "two (2, II)", "three ([(nested, deep)])", "four" ]



def test_split_defs(wordlist):
    split_defs = wordlist.split_defs
    assert split_defs("n", [ "a1, a2, a3; b1, b2", "c1, c2, c3" ]) == [['a1', 'a2', 'a3'], ['b1', 'b2'], ['c1', 'c2', 'c3']]
    assert split_defs("v", [ "a1, to a2, a3; to b1, b2", "c1, c2, c3" ]) == [['a1', 'a2', 'a3'], ['b1', 'b2'], ['c1', 'c2', 'c3']]


def test_get_split_defs(wordlist):
    get_split_defs = wordlist.get_split_defs
    defs = {
            'pos': {
                '': [ "a1, a2, a3; b1, b2", "c1, c2, c3"],
                'note': [ "d1, d2; e1, e2 (stuff, more; stuff), e3; f1"]
            },
    }

    assert get_split_defs(defs) == [['a1', 'a2', 'a3'], ['b1', 'b2'], ['c1', 'c2', 'c3'], ['d1', 'd2'], ['e1', 'e2 (stuff, more; stuff)', 'e3'], ['f1']]

def test_filter_defs(wordlist):
    filter_defs = wordlist.filter_defs

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
    assert filter_defs(defs) == defs

    assert filter_defs(defs, 'noun') == {'m': {'': ['new noun usage'], 'test, dated': ['old noun usage']}}

    # filtering does *not* match notes
    assert filter_defs(defs, 'noun', 'test') == {'m': {'': ['new noun usage'], 'test, dated': ['old noun usage']}}

    # but instead matches definitions
    assert filter_defs(defs, 'noun', 'old') == {'m': {'': ['new noun usage']}}

    assert filter_defs(defs, 'verb') == {'v': {'Spain': ['to a1; to a2', 'to not c1', 'to c2 (clarification, notes)'], '': ['to b1', 'to b2', 'to b3; to b4', 'to b5'], 'vulgar, Chile': ['to d1']}, 'vr': {'': ['to e1']}}
    assert filter_defs(defs, 'vr') == {'vr': {'': ['to e1']}}
    assert filter_defs(defs, 'verb', 'to c') == {'v': {'Spain': ['to a1; to a2', 'to not c1'], '': ['to b1', 'to b2', 'to b3; to b4', 'to b5'], 'vulgar, Chile': ['to d1']}, 'vr': {'': ['to e1']}}

    assert filter_defs(defs, 'adj') == {'adj': {'obsolete': ['adj usage']}}

    # deleting all entries should clear out the list
    assert filter_defs(defs, 'adj', 'usage') == {}
