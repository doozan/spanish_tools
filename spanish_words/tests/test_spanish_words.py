import pytest
import spanish_words
#import spanish_words.wordlist

words = None

def test__init__():
    global words
    words = pytest._spanish

def test_get_lemma():
    assert words.get_lemma("notaword", "verb") == "notaword"

    assert words.get_lemma("hablo", "verb") == "hablar"
    assert words.get_lemma("fuiste", "verb") == "ser|ir"

    assert words.get_lemma("notaword", "noun") == "notaword"

    assert words.get_lemma("casas", "noun") == "casa"
    assert words.get_lemma("amigas", "noun") == "amigo"
    assert words.get_lemma("narices", "noun") == "nariz"

    assert words.get_lemma("notaword", "adj") == "notaword"

    assert words.get_lemma("bellos", "adj") == "bello"
    assert words.get_lemma("bellas", "adj") == "bello"
    assert words.get_lemma("bella", "adj") == "bello"

    assert words.get_lemma("escocés", "adj") == "escocés"

def test_get_all_pos():
    assert words.wordlist.get_all_pos("notaword") == []
    assert words.wordlist.get_all_pos("hablar") == ["verb"]
    assert words.wordlist.get_all_pos("casa") == ["noun"]
    assert words.wordlist.get_all_pos("rojo") == ["adj", "noun"]

def test_has_word():
    assert words.wordlist.has_word("notaword", "adj") == False
    assert words.wordlist.has_word("verde", "adj") == True

def test_has_verb():
    assert words.wordlist.has_verb("tener") == True
    assert words.wordlist.has_verb("tenor") == False

def test_has_noun():
    assert words.wordlist.has_noun("casa") == True
    assert words.wordlist.has_noun("tener") == False

def test_do_analysis():

    defs = {
            'm': { '': ['male usage'] },
            'f': { '': ['female usage'] }
    }
    assert words.wordlist.do_analysis("hacer", defs) == {'m-f': {'m': ['male usage'], 'f': ['female usage']}}

    defs = {
            'mf': { '': ['male/female usage'] },
            'f': { '': ['female only usage'] }
    }
    assert words.wordlist.do_analysis("hacer", defs) == {'m-f': {'f': ['female only usage'], 'mf': ['male/female usage']}}


    # doing a lookup for "amigo" should detect female use and change 'm' to 'm/f'
    defs = { 'm': { '': ['usage'] } }
    assert words.wordlist.do_analysis("amigo", defs) == {'m/f': {'': ['usage']}}


    # doing a lookup for "tío" should detect female use and change 'm' to 'm/f' and add the extra usage
    defs = { 'm': { '': ['usage'] } }
    assert words.wordlist.do_analysis("tío", defs) == {'m/f': {'m': ['usage'], 'f, colloquial, Spain': ['woman, chick']}}

    defs = { 'f': { '': ['water'] } }
    assert words.wordlist.do_analysis("agua", defs) == { 'f-el': { '': ['water'] } }

    return


def xtest_get_synonyms():
    assert words.get_synonyms("utilizar") ==  []
    assert words.get_synonyms("oler") == ['apestar', 'olermal', 'olor']
