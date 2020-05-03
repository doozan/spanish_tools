import spanish_words
import spanish_sentences
import get_best_pos


def test_get_best_pos():
    words = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt", synonyms="spanish_data/synonyms.txt", iverbs="spanish_data/irregular_verbs.json")
    sentences = spanish_sentences.sentences("spanish_data/spa-tagged.txt")

    test_words = {
    "pesos": "noun",
    "casa": "noun",
#    "bota": "noun",
    "mira": "verb",
    "era": "verb",
    "anda": "verb",
    "apenas": "adv",
    "veras": "noun",
    "adelanto": "noun",
    "entendido": "adj",
    "lamento": "verb",
    "contento": "adj",
    "placer": "noun",
    "cuarto": "noun",
    "partido": "noun",
    "maestro": "noun",
    "haz": "verb",
    "sentido": "noun",
    "asesino": "noun",
    "drogas": "noun",
#    "salvo": "adv",
    "alrededor": "adv",
    "vete": "verb",
    "rosa": "adj",
    "noticias": "noun",
#    "doble": "adj",
    "comida": "noun",
    "chistes": "noun",
    "alerta": "noun",
    "ronda": "noun",
    "agencia": "noun",
    "mentiroso": "noun",
    "mira": "verb",
    }

    for word,pos in test_words.items():
        res = get_best_pos.get_best_pos(word, words, sentences, debug=False)
        assert res == pos