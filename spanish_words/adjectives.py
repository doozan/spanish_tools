class SpanishAdjectives:
    def __init__(self):
        self._unstresstab = str.maketrans("áéíóú", "aeiou")
        self._stresstab = str.maketrans("aeiou", "áéíóú")

    def unstress(self, word):
        return word.translate(self._unstresstab)

    def stress(self, word):
        return word.translate(self._stresstab)

    def get_lemma(self, word):

        if len(word) < 2:
            return [word]

        match = []

        if word.endswith("ores"):
            match.append(word[:-2])

        elif word.endswith("oras"):
            match.append(word[:-2])

        elif word.endswith("ora"):
            match.append(word[:-1])

        elif word.endswith("ares"):
            match.append(word[:-2])

        elif word.endswith("ales"):
            match.append(word[:-2])

        elif word[-4:] in ["ones", "unes"]:
            match.append(word[:-4] + self.stress(word[-4]) + word[-3])

        elif word.endswith("ces"):
            match.append(word[:-3]+"z")

        elif word.endswith("istas"):
            match.append(word[:-1])

        elif word.endswith("ista"):
            match.append(word)

        # ends [aei]-nes, the vowel sometimes needs to be stressed
        elif len(word)>=4 and word[-4] in "aei" and word.endswith("nes"):
            match.append(word[:-2])
            #print(word)
            # TODO: Only stress if there are no already-stressed vowels in the word
            match.append(word[:-4] + self.stress(word[-4] + word[-3]))

        # at this point we're just guessing and returning a list of possible matches to be checked against
        # the wordlist.  Return with/without -s and try changing -a to -o
        elif word.endswith("s"):
            match.append(word[:-1])
            if word[-2] == "a":
                match.append(word[:-2]+"o")
            match.append(word)

        elif word.endswith("a"):
            match.append(word[:-1]+"o")
            match.append(word)

        else:
            match.append(word)

        return match
