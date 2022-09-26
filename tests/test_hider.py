from ..deckbuilder.hider import Hider

def test_get_hide_words():
    assert list(Hider.get_hide_words("bastón")) == ['bastón', 'baston']

def test_get_chunks():

    assert list(Hider.get_chunks("to test, blah; another (bigger) test")) == [('', 'to test'), (', ', 'blah'), ('; ', 'another'), (' (', 'bigger'), (') ', 'test')]
    assert list(Hider.get_chunks("blah")) == [('', 'blah')]

def test_obscured():
    obscured = Hider.obscure_syns
    o = Hider.obscure_gloss

    assert o("blah, test", "test") == "blah, ..."
    assert o('plural of "test"', "test") == 'plural of "test"'

    # if the first item can't be hidden, don't hide any following items
    assert o('test, test', "test") == 'test, test'
    assert o('blah, plural of "test" (blah)', "test") == 'blah, ... (blah)'
    assert o('blah, plural of "test"', "test") == 'blah, ...'

#    assert o('to be incumbent', "incumbir", hide_first=False) == 'to be incumbent'
#    assert o('to be incumbent', "incumbir", hide_first=True) == 'to be ...'

    assert o('test, blah', "test", hide_first=False) == 'test, blah'
    assert o('test, blah', "test", hide_first=True) == '..., blah'

    # hide_all overrides hide_first
    assert o('blah, test', "test") == 'blah, ...'
    assert o('test, test', "test") == 'test, test'
    assert o('test, test', "test", hide_first=False, hide_all=True) == '...'
    assert o('test, test', "test", hide_first=True, hide_all=True) == '...'

    assert o('to test, blah', "test", hide_first=False) == 'to test, blah'
    assert o('to test, blah', "test", hide_first=True) == '..., blah'
    assert o('to test, test', "test", hide_all=False) == 'to test, ...'
    assert o('to test, test', "test", hide_first=True, hide_all=True) == '...'

    assert o('slander, calumny, aspersion, libel, defamation', 'calumnia') == "slander, ..., aspersion, libel, defamation"
    assert o('similarity, similitude', "similitud") == 'similarity, ...'
    assert o('similarity, similitude', "similitud", True, True) == '...'

    assert o('baton (in a marching band)', 'bastón', hide_first=True) == "... (in a marching band)"

    assert o("to succor", "socorrer", hide_all=True) == "..."

    # < 4 characters should require an exact match
    assert list(obscured(["abc", "abz"], "abc")) == ['...', 'abz']
    assert list(obscured(["to be (essentially or identified as)"], "ser")) == ['to be (essentially or identified as)']

    # 4 characters allows distance 1
    assert list(obscured(["test, pest, test, testAB, testABC, teAB"], "test")) == ['..., ..., ..., ..., ..., teAB']

    # 5 word stems always match
    assert list(obscured(["fivertest, fiverpest, fivertestA, fiverteAB, fivertABC"], "fiverXYZABCD")) == ['...']

    # List
    assert list(obscured(["longtest", "longpest", "longtestABCD", "longteAB", "longtABC"], "longtest")) == ['...', '...', '...', '...', '...']

    # 8 allows distance 2
    assert list(obscured(["longtest, longpest, longtestA, longteAB, XongteAB"], "longtest")) == ['..., ..., ..., ..., XongteAB']
    assert list(obscured(["longtest", "longpest", "longtestABCD", "longteAB", "XongteAB"], "longtest")) == ['...', '...', '...', '...', 'XongteAB']

    # split words with spaces
    assert list(obscured(["test xxx", "xxx test"], "test")) == ['...', '...']
    assert list(obscured(["avarice"], "avaricia")) == ['...']

    assert list(obscured(["huerto"], "huerta")) == ['...']

    assert list(obscured(["inculpar"], "culpar")) == ['...']

    assert list(obscured(["escupidura", "escupida", "lapo"], "escupitajo")) == ['...', "...", "lapo"]

    tests = [
        ["blag", "blag"],
        ["blagx", "blag"],
        ["xblag", "blag"],
        ["ahbhchdh", "abcd"],  # h is always stripped
        ["action", "acción"],
        ["collocation", "colocación"],
        ["supposition", "suposición"],
        ["perturbing", "perturbador"],
        ["diffusion", "difusión"],
        ["perturbing", "perturbador"],
        ["adduce", "aducir"],
        ["supposition", "suposición"],
        ["gelid", "gélido"],
        ["col", "collado"],
    ]

    so = Hider.should_obscure

    for english, spanish in tests:
        print(english, spanish)
        assert any(so(english,w) for w in Hider.get_hide_words(spanish))
