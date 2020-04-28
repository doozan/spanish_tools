# Based on GPL code from https://github.com/Neuw84/SpanishInflectorStemmer

irregular_nouns = {
    "oes": "o",
    "espráis": "espray",
    "noes": "no",
    "yoes": "yos",
    "volúmenes": "volumen",
    "cracs": "crac",
    "albalaes": "albalá",
    "faralaes": "faralá",
    "clubes": "club",
    "países": "país",
    "jerséis": "jersey",
    "especímenes": "espécimen",
    "caracteres": "carácter",
    "menús": "menú",
    "regímenes": "régimen",
    "currículos": "curriculum",
    "ultimatos": "ultimátum",
    "memorandos": "memorándum",
    "referendos": "referéndum",
    "sándwiches": "sándwich"
}

noplural_nouns = [
    "nada",
    "nadie",
    "pereza",
    "adolescencia",
    "generosidad",
    "pánico",
    "decrepitud",
    "eternidad",
    "caos",
    "yo",
    "tu",
    "tú",
    "el",
    "él",
    "ella",
    "nosotros",
    "nosotras",
    "vosotros",
    "vosotras",
    "ellos",
    "ellas",
    "viescas"
]


# This relies on spanish_words for feminine noun lookups
# and the list of nouns ending with -s

class SpanishNouns:
    def __init__(self, spanish_words):
        self.spanish_words = spanish_words

    def get_base_noun(self, word):
        word = word.lower()
        lemma = word

        if word in irregular_nouns:
            lemma = irregular_nouns[word]

        elif word in self.spanish_words.nouns_ending_s:
            lemma = word

        elif word in noplural_nouns:
            lemma = word

        # canciones, coleciones
        elif len(word) > 5 and word.endswith("iones"):
            lemma = word[:-5] + "ión"

        # profesores, doctores, actores
        elif len(word) > 4 and word.endswith("ores"):
            lemma = word[:-4] + "or"

        elif len(word) > 3 and word.endswith("ces"):
            lemma = word[:-3] + "z"

        elif len(word) > 3 and word[-3:] in [ "éis", "áis", "óis", "úis" ]:
            lemma = word[:-3] + "y"

        elif len(word) > 3 and word[-3:] in [ "des", "jes", "les", "mes", "nes", "oes", "res", "xes", "yes", "íes" ]:
            lemma = word[:-2]

        elif len(word) > 2 and word[-2:] in [ "as", "bs", "cs", "ds", "es", "fs", "gs", "ks", "ls", "ms", "ns", "os", "ps", "rs", "ts", "vs", "ás", "ís", "ós", "ús" ]:
            lemma = word[:-1]

        # Check definitions for "feminine of word-o" and use word-o as lemma (mentiroso/a)
        if lemma.endswith("a"):
            masculine = self.spanish_words.get_masculine_noun(lemma)
            if masculine:
                lemma = masculine

        return lemma