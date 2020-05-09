class SpanishAdjectives:
    def __init__(self, parent):
        self.parent = parent
        self._unstresstab = str.maketrans("áéíóú", "aeiou")
        self._stresstab = str.maketrans("aeiou", "áéíóú")

    def unstress(self, word):
        return word.translate(self._unstresstab)

    def stress(self, word):
        return word.translate(self._stresstab)

    def get_lemma(self, word):
        if self.parent.has_word(word, "adj"):
            return word

        if word.endswith("s"):
            word = word[:-1]

        if self.parent.has_word(word, "adj"):
            return word

        if word.endswith("ale"):
            return word[:-1]

        if word.endswith("dora"):
            return word[:-1]

        if word.endswith("tora"):
            return word[:-1]

        if word.endswith("ista"):
            return word

        # Not a real rule, but good enough for stemming
        if word.endswith("a"):
            return word[:-1] + "o"

        return word

    def get_forms(self, singular, gender):
        if singular.endswith("dor") and gender == "m":
            return {"ms": singular, "mp": singular+"es", "fs": singular+"a", "fp":singular+"as"}

        if singular.endswith("dora") and gender == "f":
            stem = singular[:-1]
            return {"ms": stem, "mp": stem+"es", "fs": stem+"a", "fp":stem+"as"}

        if singular[-1] == "o" or (singular[-1] == "a" and gender == "f"):
            stem = singular[:-1]
            return {"ms": stem+"o", "mp": stem+"os", "fs": stem+"a", "fp":stem+"as"}

        if singular[-1] == "e" or singular.endswith("ista"):
            plural = singular+"s"
            return {"ms": singular, "mp":plural, "fs":singular, "fp":plural}

        if singular[-1] == "z":
            plural = singular[:-1]+"ces"
            return {"ms": singular, "mp":plural, "fs":singular, "fp":plural}

        if singular[-1] == "l" or singular[-2:] in [ "ar", "ón", "ún" ]:
            plural = singular[:-2] + self.unstress(singular[-2]) + singular[-1] + "es"
            return {"ms": singular, "mp":plural, "fs":singular, "fp":plural}

        if singular.endswith("or"):
            plural = singular+"es"
            return {"ms": singular, "mp":plural, "fs":singular, "fp":plural}

        if singular[-2:] in ["án", "és", "ín"]:
            stem = singular[:-2] + self.unstress(singular[-2]) + singular[-1]
            return {"ms": singular, "mp":stem+"es", "fs":stem+"a", "fp":stem+"as"}


