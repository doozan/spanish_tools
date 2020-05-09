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


def test_get_forms():
    get_forms = obj.get_forms

    assert get_forms("girador", "m") == {'ms': 'girador', 'mp': 'giradores', 'fs': 'giradora', 'fp': 'giradoras'}
    assert get_forms("batidora", "f") == {'ms': 'batidor', 'mp': 'batidores', 'fs': 'batidora', 'fp': 'batidoras'}
    assert get_forms("alta", "f") == {'ms': 'alto', 'mp': 'altos', 'fs': 'alta', 'fp': 'altas'}
    assert get_forms("optimista", "m") == {'ms': 'optimista', 'mp': 'optimistas', 'fs': 'optimista', 'fp': 'optimistas'}
    assert get_forms("eficaz", "m") == {'ms': 'eficaz', 'mp': 'eficaces', 'fs': 'eficaz', 'fp': 'eficaces'}
    assert get_forms("amoral", "m") == {'ms': 'amoral', 'mp': 'amorales', 'fs': 'amoral', 'fp': 'amorales'}
    assert get_forms("columnar", "m") == {'ms': 'columnar', 'mp': 'columnares', 'fs': 'columnar', 'fp': 'columnares'}
    assert get_forms("mandón", "m") == {'ms': 'mandón', 'mp': 'mandones', 'fs': 'mandón', 'fp': 'mandones'}
    assert get_forms("común", "m") == {'ms': 'común', 'mp': 'comunes', 'fs': 'común', 'fp': 'comunes'}
    assert get_forms("jafán", "m") == {'ms': 'jafán', 'mp': 'jafanes', 'fs': 'jafana', 'fp': 'jafanas'}
    assert get_forms("cortés", "m") == {'ms': 'cortés', 'mp': 'corteses', 'fs': 'cortesa', 'fp': 'cortesas'}
    assert get_forms("calorín", "m") == {'ms': 'calorín', 'mp': 'calorines', 'fs': 'calorina', 'fp': 'calorinas'}

    assert get_forms("fresco", "m") ==  {'fp': 'frescas', 'fs': 'fresca', 'mp': 'frescos', 'ms': 'fresco'}

