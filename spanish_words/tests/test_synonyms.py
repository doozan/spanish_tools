import pytest
from spanish_words.synonyms import SpanishSynonyms

obj = None

def test_init():
    global obj
    obj = SpanishSynonyms()

def test_load_data():
    load_data = obj.load_data

    with pytest.raises(FileNotFoundError) as e_info:
         load_data("not_a_file") == "yes"

    load_data("spanish_data/synonyms.txt")

def test_get_synonyms():
    get_synonyms = obj.get_synonyms

    assert get_synonyms(None) == []
    assert get_synonyms("notaword") == []
    assert get_synonyms("casa") == ['hogar', 'vivienda']
