import pytest
import spanish_words

pytest._spanish = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt", synonyms="spanish_data/synonyms.txt")
