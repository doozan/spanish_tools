import re

class SpanishNouns:
    def __init__(self):
        self._unstresstab = str.maketrans("áéíóú", "aeiou")
        self._stresstab = str.maketrans("aeiou", "áéíóú")

    def unstress(self, word):
        return word.translate(self._unstresstab)

    def stress(self, word):
        return word.translate(self._stresstab)

    def make_singular(self, plural):
        if not plural:
            return []
        if len(plural) < 2:
            return [plural]
        match = []

        if " " in plural:
            res = re.match("^(.+)( (?:de|a)l? .+)$", plural)  # match xxx (de|del|a|al) yyyy
            if res:
                pl = self.make_singular(res.group(1))
                second = res.group(2)
                if not pl:
                    return None
                for first in pl:
                    match.append(first+second)
                return match
            else:
                words = plural.split(" ")
                if len(words) == 2:
                    pl = self.make_singular(words[0], gender)
                    if not pl:
                        return []
                    noun = pl[0]
                    adj = get_adjective_forms(words[1], gender)
                    if not adj:
                        #raise ValueError("No adjective forms for", words[1], gender)
                        return []

                    if gender == "m" and "mp" in adj:
                        return [noun + " " + adj["mp"]]
                    elif gender == "f" and "fp" in adj:
                        return [noun + " " + adj["fp"]]
                else:
                    return [plural]

        # ends in unstressed vowel or á, é, ó + s (casas: casa)
        if plural[-2] in "aeiouáéó" and plural[-1] == "s":
            match.append(plural[:-1])

        # ends in í or ú (bambús, bambúes => bambú)
        if len(plural)>= 3 and plural[-3] in "íú" and plural.endswith("es"):
            match.append(plural[:-2])
        if len(plural)>=2 and plural[-2] in "íú" and plural[-1] == "s":
            match.append(plural[:-1])

        # -[vowel]ces -> -z
        # ends in a vowel + z (nariz: narices)
        if len(plural)>=4 and plural[-4] in "aeiouáéó" and plural.endswith("ces"):
            match.append(plural[:-3]+"z")

        # ends tz (hertz: hertz)
        if plural.endswith("tz"):
            match.append(plural)

        modsingle = re.sub("qu([ie])", r"k\1", plural)
        vowels = []
        for c in modsingle:
            if c in "aeiouáéíóú":
                vowels.append(c)

#        if len(word)>4 and word[-4:] in ["esis", "isis", "osis", "dica"]:
#            return [word]
#
#        if word.endswith("grafía"
#
#        "grafía", "logía")):


        # ends in s or x with more than 1 syllable, last syllable unstressed (saltamontes: saltamontes)
        if len(vowels) > 1 and plural[-1] in "sx":
            match.append(plural)

        # I can't find any places where this actually applies
        # ends in l, r, n, d, z, or j with 3 or more syllables, accented on third to last syllable
        if len(vowels) > 2 and plural[-1] in "lrndzj" and vowels[len(vowels)-2] in "áéíóú":
            match.append(plural)

        # ends in a stressed vowel + consonant, remove the stress and add -es (ademán: ademanes)
        if len(plural)>=4 and plural[-4] in "aeiou" and plural[-3] not in "aeiouáéíóú" and plural.endswith("es"):
            match.append(plural[:-4] + self.stress(plural[-4] + plural[-3]))

        # ends -[aeiou]nes and has a stress mark on the third from last vowel
        # strip the stress mark and the -es
        res = re.match("^(.*)([áéíóú])([^aeiou]*[aeiou][n])es$", modsingle)
        if res:
            modplural = res.group(1) + self.unstress(res.group(2)) + res.group(3)
            clean = re.sub("k", "qu", modplural)
            match.append(clean)

        if len(plural)>=4 and plural[-4] in "aeiou" and plural[-3] in "ylrndjsx" and plural.endswith("es"):
            match.append(plural[:-2])


        # ends in a vowel+ches (extremely few cases) (coach: coaches)
        if len(plural)>=5 and plural[-5] in "aeiou" and plural.endswith("ches"):
            match.append(plural[:-2])

        # ends with two consonants +s
        # this matches mostly loanwords and is usually wrong (confort: conforts)
        if len(plural)>=3 and plural[-3] in "bcdfghjklmnpqrstvwxyz" and plural[-2] in "bcdfghjklmnpqrstvwxyz" and plural[-1] == "s":
            match.append(plural[:-1])

        # this seems to match only loanwords
        # ends in a vowel + consonant other than l, r, n, d, z, j, s, or x (robot: robots)
        if len(plural)>=3 and plural[-3] in "aeiou" and plural[-2] in "bcfghkmpqtvwy" and plural[-1] == "s":
            match.append(plural[:-1])

        # pretty much only applies to espráis, jerséis and noráis
        elif len(plural)>=3 and plural[-3:] in [ "éis", "áis" ]:
            match.append(plural[:-3] + self.unstress(plural[-3]) + "y")

        if len(match):
            return match
        else:
            return [ plural ]


