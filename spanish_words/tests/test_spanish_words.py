import pytest
import spanish_words
#import spanish_words.wordlist

words = None # spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt", synonyms="spanish_data/synonyms.txt")

def test__init__():
    global words
    words = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt", synonyms="spanish_data/synonyms.txt")
    assert words.selftest() == "OK"
#    assert words.conjugate("hablar", 7) == ['hablo']

def test_conjugate():
    # Regular
    assert words.verb.conjugate("hablar", 7) == ['hablo']

    # Irregular
    assert words.verb.conjugate("ser", 21) == ['fuiste']

    # Pattern has multiple words for form
    assert words.verb.conjugate("proveer", 3) == ['proveído', 'provisto']

    # Pattern uses multiple stems
    assert words.verb.conjugate("mirar") == {1: ['mirar'], 2: ['mirando'], 3: ['mirado'], 4: ['mirada'], 5: ['mirados'], 6: ['miradas'], 7: ['miro'], 8: ['miras'], 9: ['mirás'], 10: ['mira'], 11: ['miramos'], 12:
['miráis'], 13: ['miran'], 14: ['miraba'], 15: ['mirabas'], 16: ['miraba'], 17: ['mirábamos'], 18: ['mirabais'], 19: ['miraban'], 20: ['miré'], 21: ['miraste'], 22: ['miró'], 23: ['miramos'], 24: ['mirasteis'], 25: ['miraron'], 26: ['miraré'], 27: ['mirarás'], 28: ['mirará'], 29: ['miraremos'], 30: ['miraréis'], 31: ['mirarán'], 32: ['miraría'], 33: ['mirarías'], 34: ['miraría'], 35: ['miraríamos'], 36: ['miraríais'], 37: ['mirarían'], 38: ['mire'], 39: ['mires'], 40: ['mirés'], 41: ['mire'], 42: ['miremos'], 43: ['miréis'], 44: ['miren'], 45: ['mirara'], 46: ['miraras'], 47: ['mirara'], 48: ['miráramos'], 49: ['mirarais'], 50: ['miraran'], 51: ['mirase'], 52: ['mirases'], 53: ['mirase'], 54: ['mirásemos'], 55: ['miraseis'], 56: ['mirasen'], 57: ['mirare'], 58: ['mirares'], 59: ['mirare'], 60: ['miráremos'], 61: ['mirareis'], 62: ['miraren'], 63: ['mira'], 64: ['mirá'], 65: ['mire'], 66: ['miremos'], 67: ['mirad'], 68: ['miren'], 69: ['mires'], 70: ['mire'], 71: ['miremos'], 72: ['miréis'], 73: ['miren']}

    # verb uses two different conjugation patterns
    assert words.verb.conjugate("emparentar", 7) == ['empariento', 'emparento']


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

    assert words.get_lemma("mentirosas", "noun") == "mentiroso"

    assert words.get_lemma("espráis", "noun") == "espray"

    assert words.get_lemma("bordes", "noun") == "borde"
    assert words.get_lemma("tardes", "noun") == "tarde"

    assert words.get_lemma("meses", "noun") == "mes"

    assert words.get_lemma("escocés", "noun") == "escocés"
    assert words.get_lemma("ratones", "noun") == "ratón"

def test_get_lemma_adj():
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
