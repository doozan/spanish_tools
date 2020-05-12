from spanish_words.adjectives import SpanishAdjectives
import pytest

obj = None

def test_init(spanish):
    global obj
    obj = SpanishAdjectives(spanish)

def test_get_lemma():
    get_lemma = obj.get_lemma

    assert get_lemma("notaword") == "notaword"

    assert get_lemma("bellos") == "bello"
    assert get_lemma("bellas") == "bello"
    assert get_lemma("bella") == "bello"

    assert get_lemma("escocés") == "escocés"

