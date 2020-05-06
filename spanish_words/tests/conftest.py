import pytest
import spanish_words

@pytest.fixture(scope="session")
def spanish():
    return spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt", synonyms="spanish_data/synonyms.txt")
