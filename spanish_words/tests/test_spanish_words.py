import spanish_words
#import spanish_words.wordlist

words = None

def test__init__(spanish):
    global words
    words = spanish

def test_get_lemma():
    get_lemma = words.get_lemma

    assert get_lemma("notaword", "verb") == "notaword"

    assert get_lemma("hablo", "verb") == "hablar"
    assert get_lemma("fuiste", "verb") == "ir|ser"

    assert get_lemma("notaword", "noun") == "notaword"

    assert get_lemma("casas", "noun") == "casa"
    assert get_lemma("amigo", "noun") == "amigo"
    assert get_lemma("amigos", "noun") == "amigo"
    assert get_lemma("amiga", "noun") == "amigo"
    assert get_lemma("amigas", "noun") == "amigo"
    assert get_lemma("narices", "noun") == "nariz"

    assert get_lemma("notaword", "adj") == "notaword"

    assert get_lemma("bellos", "adj") == "bello"
    assert get_lemma("bellas", "adj") == "bello"
    assert get_lemma("bella", "adj") == "bello"

    assert get_lemma("escocés", "adj") == "escocés"

    assert get_lemma("piernas", "noun") == "pierna"

    assert get_lemma("dos", "noun") == "dos"
    assert get_lemma("autobús", "noun") == "autobús"
    assert get_lemma("cubrebocas", "noun") == "cubrebocas"
    assert get_lemma("gas", "noun") == "gas"

    assert get_lemma("mentirosas", "noun") == "mentiroso"

    assert get_lemma("espráis", "noun") == "espray"

    assert get_lemma("bordes", "noun") == "borde"
    assert get_lemma("tardes", "noun") == "tarde"

    assert get_lemma("meses", "noun") == "mes"

    assert get_lemma("escocés", "noun") == "escocés"
    assert get_lemma("ratones", "noun") == "ratón"

    assert get_lemma("órdenes", "noun") == "orden"

    assert get_lemma("mejicana", "noun") == "mexicano"
    assert get_lemma("mejicanas", "noun") == "mexicano"


def test_has_word():
    has_word = words.has_word

    assert has_word("", "verb") == False
    assert has_word("notaword", "verb") == False
    assert has_word("casa") == True
    assert has_word("casa", "noun") == True
    assert has_word("casa", "verb") == False
    assert has_word("tener", "verb") == True
    assert has_word("casa", "") == True
    assert has_word("dos", "num") == True
    assert has_word("dos", "noun") == False
    assert has_word("verde", "adj") == True
    assert has_word("sentido", "part") == True


def test_lookup():
    lookup = words.lookup

    # adjectives that are past participles should add a note and then the verb usage
    res = lookup("descubierto", "adj")
    print(res)
    assert res == {'adj': {'': 'discovered', 'verb': 'past particple of descubrir'}, 'v': {'': 'to discover; to reveal; to invent'}}

    # nouns and adjectives that share a word should add each other's usage
    res = lookup("santo", "adj")
    assert res == {'adj': {'': 'holy, godly'}, 'm/f': {'': 'saint; name day'}}

    res = lookup("santo", "noun")
    assert res == {'m/f': {'': 'saint; name day'}, 'adj': {'': 'holy, godly'}}


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





#def xtest_get_synonyms():
#    assert words.get_synonyms("utilizar") ==  []
#    assert words.get_synonyms("oler") == ['apestar', 'olermal', 'olor']
