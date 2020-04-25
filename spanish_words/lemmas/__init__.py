import spanish_words.lemmas.verbs
import spanish_words.lemmas.nouns
import spanish_words.lemmas.adjectives

class SpanishLemmas:
    def __init__(self, spanish_words, irregular_verbs):
        self.verbs = verbs.SpanishVerbs(spanish_words, irregular_verbs)
        self.nouns = nouns.SpanishNouns(spanish_words)

    def get_lemmas(self, word, pos):
        word = word.lower().strip()
        pos = pos.lower()

        if pos == "adj":
            return [ adjectives.get_base_adjective(word) ]

        if pos == "noun":
            return [ self.nouns.get_base_noun(word) ]

        elif pos == "verb":
            return self.verbs.reverse_conjugate(word)

        return [ word ]

    def get_lemma(self, word, pos):
        lemmas = self.get_lemmas(word,pos)

        if not len(lemmas):
            return word

        if len(lemmas) == 1:
            return lemmas[0]

        # remove dups
        lemmas = list(dict.fromkeys(lemmas)) # Requires cpython 3.6 or python 3.7
        return "|".join(lemmas)


