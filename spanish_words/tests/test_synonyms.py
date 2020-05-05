from spanish_words.synonyms import SpanishSynonyms
import pytest

syns = None

def test_init():
    global syns
    syns = SpanishSynonyms()

def test_load_data():
    with pytest.raises(FileNotFoundError) as e_info:
         syns.load_data("not_a_file") == "yes"

    syns.load_data("spanish_data/synonyms.txt")

def test_get_synonyms():
    assert syns.get_synonyms(None) == []
    assert syns.get_synonyms("notaword") == []
    assert syns.get_synonyms("casa") == ['hogar', 'vivienda']
