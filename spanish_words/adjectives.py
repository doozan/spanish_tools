class SpanishAdjectives:
    def __init__(self, parent):
        self.parent = parent

    def get_lemma(self, word):
        if self.parent.has_word(word, "adj"):
            return word

        if word.endswith("s"):
            word = word[:-1]

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
