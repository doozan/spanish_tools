from spanish_words.nouns import SpanishNouns
import pytest

noun = None

def test_init(spanish):
    global noun
    noun = SpanishNouns(spanish)

def test_get_lemma():
    get_lemma = noun.get_lemma

    assert get_lemma("casas") == "casa"

    assert get_lemma("notaword") == "notaword"

    assert get_lemma("casas") == "casa"
    assert get_lemma("narices") == "nariz"

    assert get_lemma("piernas") == "pierna"

    assert get_lemma("dos") == "dos"
    assert get_lemma("autobús") == "autobús"
    assert get_lemma("cubrebocas") == "cubrebocas"
    assert get_lemma("gas") == "gas"

    assert get_lemma("mentirosas") == "mentiroso"

    assert get_lemma("espráis") == "espray"

    assert get_lemma("bordes") == "borde"
    assert get_lemma("tardes") == "tarde"

    assert get_lemma("meses") == "mes"

    assert get_lemma("escocés") == "escocés"
    assert get_lemma("ratones") == "ratón"

    assert get_lemma("órdenes") == "orden"


