import spanish_words
#import spanish_words.wordlist

words = None

def test__init__(spanish):
    global words
    words = spanish


def test_get_lemma_noun():
    get_lemma = words.get_lemma

    pairs = {
        "notaword": "notaword",

        "casas": "casa",
        "amigo": "amigo",
        "amigos": "amigo",
        "amiga": "amigo",
        "amigas": "amigo",
        "narices": "nariz",

        "piernas": "pierna",

        "dos": "dos",
        "autobús": "autobús",
        "cubrebocas": "cubrebocas",
        "gas": "gas",

        "mentirosas": "mentiroso",

        "espráis": "espray",

        "bordes": "borde",
        "tardes": "tarde",

        "meses": "mes",

        "escocés": "escocés",
        "ratones": "ratón",

        "órdenes": "orden",

        "mejicana": "mexicano",
        "mejicanas": "mexicano",
    }

    for k,v in pairs.items():
        assert get_lemma(k, "noun") == v



def test_get_lemma_adj():
    get_lemma = words.get_lemma

    pairs = {
        "notaword": "notaword",
        "notwords": "notwords",

        "titulares": "titular",

        "vitales": "vital",

        "torpones": "torpón",
        "comunes": "común",

        "veloces": "veloz",

        "bellos": "bello",
        "bellas": "bello",
        "bella": "bello",

        "escocés": "escocés"
    }

    for k,v in pairs.items():
        assert get_lemma(k, "adj") == v


def test_get_lemma_verb():
    get_lemma = words.get_lemma

    pairs = {
        "notaword": "notaword",
        "podría": "poder",
        "hablo": "hablar",
        "fuiste": "ir|ser",
        "comido": "comer",
        "ve": "ir",
        "sé": "saber",
        "haciendo": "hacer",
        "vete": "ir",
        "vengan": "venir",
        "volaste": "volar",
        "temes": "temer",
        "viste": "ver",
        "podemos": "poder",
        "suelen": "soler",
        "viven": "vivir",
        "diste": "dar",
#        "venda": "vender",
#        "sales": "salir",
#         "sumas": "sumar"
    }

    for k,v in pairs.items():
        assert get_lemma(k, "verb") == v



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
    assert res == {'m/f': {'': 'pupil, student, learner'}}

    res = lookup("abuelo", "noun")
    assert res == {'m/f': {'f': 'grandmother', 'f, colloquial': 'old woman', 'm': 'grandfather', 'm, colloquial, affectionate': 'an elderly person'}} 

    # f-el detection
    res = lookup("alma", "noun")
    assert res ==  {'f-el': {'': 'soul'}}

    # m-f detection
    res = lookup("batería", "noun")
    assert res == {'m-f': {'f': 'large battery; drum set; set (collection of things)', 'mf': 'drummer'}}

    # verb
    res = lookup("arrestar", "verb")
    assert res == {'v': {'': 'to arrest'}}

    # filter everything out
#    res = lookup("arrestar", "noun")
#    assert res == {}





#def xtest_get_synonyms():
#    assert words.get_synonyms("utilizar") ==  []
#    assert words.get_synonyms("oler") == ['apestar', 'olermal', 'olor']
