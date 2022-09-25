import re
from Levenshtein import distance as fuzzy_distance

class Hider():

    @staticmethod
    def get_chunks(text):
        # Yields separator, chunk
        separator = ""
        for x, chunk in enumerate(re.split(text, "([,;:()])")):
            if x % 2 == 0:
                yield separator, chunk
            else:
                separator = chunk

    @classmethod
    def obscure_gloss(cls, gloss, hide_word, hide_first=False, hide_all=False, english=True):
        old = cls.old_obscure_gloss(gloss, hide_word, hide_first, hide_all, english)
        new = cls.new_obscure_gloss(gloss, hide_word, hide_first, hide_all, english)

        if old != new:
            print(hide_word, ":", gloss)
            print(hide_word, ":", old)
            print(hide_word, ":", new)

        return old

    @classmethod
    def new_obscure_gloss(cls, gloss, hide_word, hide_first=False, hide_all=False, english=True):
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
                if cls.new_should_obscure(chunk, hide_word):
                    hidden.append(len(res))
                else:
                    all_hidden = False
            res.append(chunk)

        # If we shouldn't hide everything, don't hide the first item
        if all_hidden and not hide_all:
            del hidden[0]

        for x in hidden:
            res[x] = "..."

        return "".join(res)

    @classmethod
    def should_obscure(text, hide_words):
        m = re.match(r'\W*(?P<form>apocopic form|diminutive|ellipsis|clipping|superlative|plural) of "', text)
        if m:
            return m.group("form") in ["ellipsis", "clipping"]

        for text_word in text.split():
            if any(cls.words_match(text_word, hide_word) for hide_word in hide_words):
                return True

        return False


    @classmethod
    def old_obscure_gloss(cls, gloss, hide_word, hide_first=False, hide_all=False, english=True):

        def is_first_word(data):
            if all(w.strip().lower() in ["", "a", "an", "to", "be", "of", "in"] for w in data):
                return True
            return False

        if hide_all:
            hide_first = True

        hide_words = cls.get_hide_words(hide_word, english)

        m = re.match(r'(?P<pre>.*?)(?P<form>apocopic form|diminutive|ellipsis|clipping|superlative|plural) of "(?P<word>.*?)"(?P<post>.*)', gloss)
        if m:
            if not (hide_all or m.group("pre") or m.group("post")):
                return gloss

            new_gloss = []
            if m.group("pre"):
                new_gloss.append(cls.obscure_gloss(m.group("pre"), hide_word, hide_all=True))

            new_gloss.append(m.group("form"))
            new_gloss.append(' of "')
            if m.group("form") in ["ellipsis", "clipping"]:
                new_gloss.append("...")
            else:
                new_gloss.append(cls.obscure_gloss(m.group("word"), hide_word, hide_all=True))
            new_gloss.append('"')

            if m.group("post"):
                new_gloss.append(cls.obscure_gloss(m.group("post"), hide_word, hide_all=True))

            # This isn't perfect, if a gloss for blah is 'blah; diminutive of "blah"' it will
            # be fully obscured to '...; diminutive of "..."'

        data = []
        splits = iter(re.split(r'(\W+)', gloss))
        all_hidden = True
        for word in splits:
            sep = next(splits, None)
            if not word and sep:
                data.append(sep)
                continue

            if any(h for h in hide_words if cls.should_obscure(word, h)) and (hide_first or not is_first_word(data)):
                data.append("...")
            else:
                data.append(word)
                if all_hidden and word.lower() not in ["a", "an", "to"]:
                    all_hidden = False

            if sep:
                data.append(sep)

        if hide_all or not all_hidden:
            gloss = "".join(data)

        return gloss

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
        "ía": ["y"],
        "ia": ["y"],
    }
    _unstresstab = str.maketrans("áéíóú", "aeiou")
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

    @classmethod
    def get_hide_words(cls, hide_word, english):
        if not english:
            return [hide_word]

        hide_word = cls.unstress(hide_word)
        if hide_word[-2:] in ["ar", "er", "ir", "ír"]:
            hide_word = hide_word[:-1]

        hide_words = [hide_word]
        hide_words += cls.anglicise(hide_word)
        return list(map(cls.unstress, hide_words))

    three_letter_english = ["ago","all","and","any","are","bad","bed","big","bit","boy","but","buy","bye",
            "can","car","cut","dad","day","did","die","eat","far","for","fun","get","got","had","has",
            "her","hey","him","his","hit","hot","how","law","let","lie","lot","man","men","met","new",
            "not","now","off","one","our","out","put","say","see","set","she","sit","six","ten","the",
            "too","try","two","was","way","who","why","yet","you"]

    _unstresstab = str.maketrans("áéíóú", "aeiou")

    @classmethod
    def normalize(cls, word):
        word = word.translate(cls._unstresstab)
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
    def new_should_obscure(cls, word, hide_word):
        word = cls.normalize(word)
        hide_word = cls.normalize(hide_word)

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
                if fuzzy_distance(w, hw) <= distance:
                    return True

        return False



    @classmethod
    def should_obscure(cls, word, hide_word):
        word = cls.normalize(word)
        hide_word = cls.normalize(hide_word)

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
                if fuzzy_distance(w, hw) <= distance:
                    return True

        return False

    @classmethod
    def obscure_syns(cls, items, hide_word):
        for item in items:
            yield cls.obscure_gloss(item, hide_word, hide_all=True, hide_first=True, english=False)

