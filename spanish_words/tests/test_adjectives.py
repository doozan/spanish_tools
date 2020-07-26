from spanish_words.adjectives import SpanishAdjectives
import pytest

obj = None

def test_init():
    global obj
    obj = SpanishAdjectives()

def test_get_lemma():
    get_lemma = obj.get_lemma

    test_words = {
        "dentista": "dentista",
        "dentistas": "dentista",

        "profesores": "profesor",
        "profesoras": "profesor",
        "profesora": "profesor",

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

    for k,v in test_words.items():
        assert v in get_lemma(k)

