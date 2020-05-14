from spanish_words.adjectives import SpanishAdjectives
import pytest

obj = None

def test_init():
    global obj
    obj = SpanishAdjectives()

def test_get_lemma():
    get_lemma = obj.get_lemma

    assert get_lemma("notaword") == ["notaword"]

    assert get_lemma("dentista") == ["dentista"]
    assert get_lemma("dentistas") == ["dentista"]

    assert get_lemma("profesores") == ["profesor"]
    assert get_lemma("profesoras") == ["profesor"]
    assert get_lemma("profesora") == ["profesor"]

    assert get_lemma("titulares") == ["titular"]

    assert get_lemma("vitales") == ["vital"]

    assert get_lemma("torpones") == ["torpón"]
    assert get_lemma("comunes") == ["común"]

    assert get_lemma("veloces") == ["veloz"]

    assert get_lemma("bellos") == ["bello","bellos"]
    assert "bello" in get_lemma("bellas")
    assert "bello" in get_lemma("bella")

    assert "escocés" in get_lemma("escocés")

