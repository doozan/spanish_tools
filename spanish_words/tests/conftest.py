import pytest
import spanish_words

@pytest.fixture(scope="session")
def spanish():
    return spanish_words.SpanishWords(dictionary="es-en.txt", data_dir="../spanish_data", custom_dir="../spanish_custom")

@pytest.fixture(scope="session")
def wordlist(spanish):
    return spanish.wordlist
