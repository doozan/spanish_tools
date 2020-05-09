import re

# Based on GPL code from https://github.com/Neuw84/SpanishInflectorStemmer

irregular_nouns = {
    "oes": "o",
    "espráis": "espray",
    "noes": "no",
    "yoes": "yos",
    "volúmenes": "volumen",
    "albalaes": "albalá",
    "faralaes": "faralá",
    "clubes": "club",
    "países": "país",
    "jerséis": "jersey",
    "especímenes": "espécimen",
    "caracteres": "carácter",
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
    def __init__(self, parent):
        self.parent = parent
        self._unstresstab = str.maketrans("áéíóú", "aeiou")
        self._stresstab = str.maketrans("aeiou", "áéíóú")

    def unstress(self, word):
        return word.translate(self._unstresstab)

    def stress(self, word):
        return word.translate(self._stresstab)

    def get_lemma(self, word):
        word = word.lower()

        lemma = word

        if word in irregular_nouns:
            lemma = irregular_nouns[word]

        elif self.parent.has_word(word, "noun") or self.parent.has_word(word, "num"):
            lemma = word

        elif word in noplural_nouns:
            lemma = word


        # try dropping the s first and seeing if the result is a known word (catches irregulars like bordes/borde)
        elif len(word) > 2 and word.endswith("s") and self.parent.has_word(word[:-1], "noun"):
            lemma = word[:-1]

        # ratones -> ratón
        elif len(word) > 4 and word.endswith("ones") and self.parent.has_word(word[:-4]+"ón", "noun"):
            lemma = word[:-4] + "ón"

        # canciones, coleciones
        elif len(word) > 5 and word.endswith("iones"):
            lemma = word[:-5] + "ión"

        # profesores, doctores, actores
        elif len(word) > 4 and word.endswith("ores"):
            lemma = word[:-4] + "or"

        # lapices, narices
        elif len(word) > 3 and word.endswith("ces"):
            lemma = word[:-3] + "z"

        elif len(word) > 3 and word[-3:] in [ "éis", "áis", "óis", "úis" ]:
            lemma = word[:-3] + "y"

        elif len(word) > 3 and word[-3:] in [ "des", "jes", "les", "mes", "nes", "oes", "res", "ses", "xes", "yes", "íes" ]:
            lemma = word[:-2]
            if not self.parent.has_word(lemma, "noun") and self.parent.has_word(self.unstress(lemma), "noun"):
                lemma = self.unstress(lemma)

        elif len(word) > 2 and word[-2:] in [ "as", "bs", "cs", "ds", "es", "fs", "gs", "ks", "ls", "ms", "ns", "os", "ps", "rs", "ts", "vs", "ás", "ís", "ós", "ús" ]:
            lemma = word[:-1]

        # Check definitions for "feminine of word-o" and use word-o as lemma (mentiroso/a)
        masculine = self.parent.wordlist.get_masculine_noun(lemma)
        if masculine:
            lemma = masculine

        return lemma

    def make_plural(self, singular, gender="m"):
        if singular == "":
            return None

        if " " in singular:
            res = re.match("^(.+)( (?:de|a)l? .+)$", singular)  # match xxx (de|del|a|al) yyyy
            if res:
                pl = self.make_plural(res.group(1), gender)
                if not pl:
                    return None
                first = pl[0]
                second = res.group(2)
                return [first+second]
            else:
                words = singular.split(" ")
                if len(words) == 2:
                    pl = self.make_plural(words[0], gender)
                    if not pl:
                        return None
                    noun = pl[0]
                    adj = self.parent.adj.get_forms(words[1], gender)
                    if not adj:
                        #raise ValueError("No adjective forms for", words[1], gender)
                        return None

                    if gender == "m" and "mp" in adj:
                        return [noun + " " + adj["mp"]]
                    elif gender == "f" and "fp" in adj:
                        return [noun + " " + adj["fp"]]

        # ends in unstressed vowel or á, é, ó (casa: casas)
        if singular[-1] in "aeiouáéó":
            return [singular+"s"]

        # ends in í or ú (bambú: [bambús, bambúes])
        if singular[-1] in "íú":
            return [ singular+"s", singular+"es" ]

        # ends in a vowel + z (nariz: narices)
        if len(singular)>1 and singular[-2] in "aeiouáéó" and singular.endswith("z"):
            return [singular[:-1]+"ces"]

        # ends tz (hertz: hertz)
        if singular.endswith("tz"):
            return [singular]

        modsingle = re.sub("qu([ie])", r"k\1", singular)
        vowels = []
        for c in modsingle:
            if c in "aeiouáéíóú":
                vowels.append(c)

        # ends in s or x with more than 1 syllable, last syllable unstressed (saltamontes: saltamontes)
        if len(vowels) > 1 and singular[-1] in "sx":
            return [singular]

        # I can't find any places where this actually applies
        # ends in l, r, n, d, z, or j with 3 or more syllables, accented on third to last syllable
        if len(vowels) > 2 and singular[-1] in "lrndzj" and vowels[len(vowels)-2] in "áéíóú":
            return [singular]

        # ends in a stressed vowel + consonant, remove the stress and add -es (ademán: ademanes)
        if len(singular)>1 and singular[-2] in "áéíóú" and singular[-1] not in "aeiouáéíóú":
            return [ singular[:-2] + self.unstress(singular[-2:]) + "es" ]

        # ends in an unaccented vowel + y, l, r, n, d, j, s, x (color: coleres)
        if len(singular)>1 and singular[-2] in "aeiou" and singular[-1] in "ylrndjsx":
            # two or more vowels and ends with -n, add stress mark to plural  (desorden: desórdenes)
            if len(vowels) > 1 and singular[-1] == "n":
                res = re.match("^(.*)([aeiou])([^aeiou]*[aeiou][nl])$", modsingle)
                if res:
                    start = res.group(1)  # dólmen
                    vowel = res.group(2)
                    end = res.group(3)
                    modplural = start + self.stress(vowel) + end + "es"
                    plural = re.sub("k", "qu", modplural)
                    return [ plural ]
            return [ singular + "es" ]

        # ends in a vowel+ch (extremely few cases) (coach: coaches)
        if len(singular)>2 and singular.endswith("ch") and singular[-3] in "aeiou":
            return [ singular + "es" ]

        # this matches mostly loanwords and is usually wrong (confort: conforts)
        if len(singular)>1 and singular[-2] in "bcdfghjklmnpqrstvwxyz" and singular[-1] in "bcdfghjklmnpqrstvwxyz":
            return [ singular + "s" ]

        # this seems to match only loanwords
        # ends in a vowel + consonant other than l, r, n, d, z, j, s, or x (robot: robots)
        if len(singular)>1 and singular[-2] in "aeiou" and singular[-1] in "bcfghkmpqtvwy":
            return [ singular + "s" ]

        return None
