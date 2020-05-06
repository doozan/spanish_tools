import spanish_words
#import spanish_words.wordlist

words = None

def test__init__(spanish):
    global words
    words = spanish

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

#def xtest_get_synonyms():
#    assert words.get_synonyms("utilizar") ==  []
#    assert words.get_synonyms("oler") == ['apestar', 'olermal', 'olor']
