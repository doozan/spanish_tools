import re
from Levenshtein import distance as fuzzy_distance

class Hider():

    @staticmethod
    def get_chunks(text):
        # Yields separator, chunk
        separator = ""
        for x, chunk in enumerate(re.split(r"(\s*[,;:()/]\s*)", text)):
            if x % 2 == 0:
                yield separator, chunk
            else:
                separator = chunk

    @classmethod
    def obscure_gloss(cls, gloss, hide_word, hide_first=False, hide_all=False, english=True):

        if hide_all:
            hide_first = True

        res = []
        hidden = []
        first = True
        all_hidden = hide_first
        for separator, chunk in cls.get_chunks(gloss):
            if separator:
                res.append(separator)
            if not chunk:
                continue
            if not first or hide_first:
                if any(cls.should_obscure(word, hide_word) for word in chunk.split()):
                    hidden.append(len(res))
                else:
                    all_hidden = False
            res.append(chunk)
            first = False

        # If we shouldn't hide everything, don't hide the first item
        print(hidden, all_hidden, hide_all)
        if all_hidden:
            if hide_all:
                return "..."
            del hidden[0]

        for x in hidden:
            res[x] = "..."

        return "".join(res)

    @classmethod
    def should_obscure(cls, text, hide_word):
        m = re.match(r'\w*(?P<form>apocopic form|diminutive|ellipsis|clipping|superlative|plural) of "(?P<word>.*?)"', text)
        if m:
            if m.group("form") in ["ellipsis", "clipping"]:
                return True
            text = group("word")

        hide_words = set(cls.get_hide_words(hide_word))
        print(text, hide_words)
        for text_word in text.split():
            if any(cls.words_match(text_word, word) for word in hide_words):
                return True

        return False


    alt_endings = {
        "ancia": ["ance", "ancy"],
        "mente": ["ly"],
        "mento": ["ment"],
        "encia": ["ence", "ency"],
        "adora": ["ing"],
        "ante": ["ant"],
        "ario": ["ary"],
        "ente": ["ent"],
        "ador": ["ing"],
        "ante": ["ant"],
        "cion": ["tion"],
        "ente": ["ent"],
        "ista": ["ist"],
        "ura": ["ure"],
        "ano": ["an"],
        "ana": ["an"],
        "ico": ["ic", "ical"],
        "ica": ["ic", "ical"],
        "ivo": ["ive"],
        "io": ["y"],
        "ia": ["y"],
        "ar": ["a"],
        "er": ["e"],
        "ir": ["i"],
    }
    _unstresstab = str.maketrans("áéíóúüñ", "aeiouun")
    @classmethod
    def unstress(cls, text):
        return text.translate(cls._unstresstab)

    @classmethod
    def anglicise(cls, word):
        for k,endings in cls.alt_endings.items():
            if word.endswith(k):
                base = word[:-1*len(k)]
                return [base+new_ending for new_ending in endings]

        return []

    ignore_spanish_words = ["por", "para", "los", "las", "les", "mis", "tus", "sus", "del",
            "como", "que", "una", "uno", "con"]

    @classmethod
    def get_hide_words(cls, hide_word):
        hide_word = hide_word.replace("-", " ")
        for word in hide_word.split():
            if word in cls.ignore_spanish_words:
                continue
            yield word

            norm_word = cls.normalize(word)
            if norm_word != word:
                yield norm_word

            for word in cls.anglicise(norm_word):
                yield word

    three_letter_english = ["ago","all","and","any","are","bad","bed","big","bit","boy","but","buy","bye",
            "can","car","cut","dad","day","did","die","eat","far","for","fun","get","got","had","has",
            "her","hey","him","his","hit","hot","how","law","let","lie","lot","man","men","met","new",
            "not","now","off","one","our","out","put","say","see","set","she","sit","six","ten","the",
            "too","try","two","was","way","who","why","yet","you"]


    @classmethod
    def normalize(cls, word):
        word = word.lower()
        word = word.translate(cls._unstresstab)
        word = re.sub(r"\W", "", word)
        word = word.replace("h", "")
        word = word.replace("ff", "f")
        word = word.replace("dd", "d")
        word = word.replace("ss", "s")
        word = word.replace("aa", "a")
        word = word.replace("ee", "e")
        word = word.replace("oo", "o")
        word = word.replace("ii", "i")
        return word

    @classmethod
    def words_match(cls, word, hide_word):
        print("XX", word, hide_word)
        word = cls.normalize(word)

        print(word, hide_word)

        l = min(len(word), len(hide_word))
        if l<=2:
            return False

        if l==3 and word in cls.three_letter_english:
            return False
        distance = int(l/4) if l >= 4 else 0
        words = [word[:l]]

        # fix for matching blah to xblah (xbla doesn't match, but xblah does even though it's longer)
        if l < len(word) and len(word) - distance <= l:
            words.append(word)

        hide_words = [hide_word[:l]]

        # fix for matching xblah to blah (xbla doesn't match, but xblah does even though it's longer)
        if l < len(hide_word) and len(hide_word) - distance <= l:
            hide_words.append(hide_word)

        for w in words:
            for hw in hide_words:

                print(w, hw, l)

                # If the stem matches, let it count as a match
                if l > 5 and w[:5] == hw[:5]:
                    return True

                if fuzzy_distance(w, hw) <= distance:
                    return True

        return False


    @classmethod
    def obscure_syns(cls, items, hide_word):
        for item in items:
            yield cls.obscure_gloss(item, hide_word, hide_all=True, hide_first=True, english=False)
