import spanish_words

words = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt", synonyms="spanish_data/synonyms.txt", iverbs="spanish_data/irregular_verbs.json")

def test_conjugate():
    assert words.conjugate("hablar", 7) == ['hablo']
    assert words.conjugate("proveer", 3) == ['proveído', 'provisto']
    assert words.conjugate("mirar") == {1: ['mirar'], 2: ['mirando'], 3: ['mirado'], 4: ['mirada'], 5: ['mirados'], 6: ['miradas'], 7: ['miro'], 8: ['miras'], 9: ['mirás'], 10: ['mira'], 11: ['miramos'], 12:
['miráis'], 13: ['miran'], 14: ['miraba'], 15: ['mirabas'], 16: ['miraba'], 17: ['mirábamos'], 18: ['mirabais'], 19: ['miraban'], 20: ['miré'], 21: ['miraste'], 22: ['miró'], 23: ['miramos'], 24: ['mirasteis'], 25: ['miraron'], 26: ['miraré'], 27: ['mirarás'], 28: ['mirará'], 29: ['miraremos'], 30: ['miraréis'], 31: ['mirarán'], 32: ['miraría'], 33: ['mirarías'], 34: ['miraría'], 35: ['miraríamos'], 36: ['miraríais'], 37: ['mirarían'], 38: ['mire'], 39: ['mires'], 40: ['mirés'], 41: ['mire'], 42: ['miremos'], 43: ['miréis'], 44: ['miren'], 45: ['mirara'], 46: ['miraras'], 47: ['mirara'], 48: ['miráramos'], 49: ['mirarais'], 50: ['miraran'], 51: ['mirase'], 52: ['mirases'], 53: ['mirase'], 54: ['mirásemos'], 55: ['miraseis'], 56: ['mirasen'], 57: ['mirare'], 58: ['mirares'], 59: ['mirare'], 60: ['miráremos'], 61: ['mirareis'], 62: ['miraren'], 63: ['mira'], 64: ['mirá'], 65: ['mire'], 66: ['miremos'], 67: ['mirad'], 68: ['miren'], 69: ['mires'], 70: ['mire'], 71: ['miremos'], 72: ['miréis'], 73: ['miren']}

def test_get_lemma():
    assert words.get_lemma("notaword", "verb") == "notaword"
    assert words.get_lemma("casas", "noun") == "casa"
    assert words.get_lemma("casas", "verb") == "casar"
    assert words.get_lemma("bellas", "adj") == "bello"
