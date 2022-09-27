from ..deckbuilder.hider import Hider

def test_get_hide_words():
    assert list(Hider.get_hide_words("bastón")) == ['bastón', 'baston']

def test_get_chunks():

    assert list(Hider.get_chunks("to test, blah; another (bigger) test")) == [('', 'to test'), (', ', 'blah'), ('; ', 'another'), (' (', 'bigger'), (') ', 'test')]
    assert list(Hider.get_chunks("blah")) == [('', 'blah')]

def test_obscured():
    o = Hider.obscure

    assert o("blah, test", "test") == "blah, ..."
    assert o('plural of "test"', "test") == '...'

    assert o('test, test', "test") == '...'
    assert o('blah, plural of "test" (blah)', "test") == 'blah, ... (blah)'
    assert o('blah, plural of "test"', "test") == 'blah, ...'

    assert o('to be incumbent', "incumbir") == '...'

    assert o('test, blah', "test") == '..., blah'

    assert o('to test, test', "test") == '...'

    assert o('slander, calumny, aspersion, libel, defamation', 'calumnia') == "slander, ..., aspersion, libel, defamation"
    assert o('similarity, similitude', "similitud") == '...'

    assert o('baton (in a marching band)', 'bastón') == "... (in a marching band)"

    assert o("to succor", "socorrer") == "..."

    # < 4 characters should require an exact match
    assert o("abc, abz", "abc") == '..., abz'

    # 4 characters allows distance 1
    assert o("test, pest, test, testAB, testABC, teAB", "test") == '..., ..., ..., ..., ..., teAB'

    # 5 word stems always match
    assert o("fiver, fivertest, fiverpest, fivertestA, fiverteAB, fivertABC", "fiverXYZABCD") == '...'

    # List
    assert o("longtest, longpest, longtestABCD, longteAB, longtABC", "longtest") == '...'

    # 8 allows distance 2
    assert o("longtest, longpest, longtestA, longteAB, XongteAB", "longtest") == '..., ..., ..., ..., XongteAB'

    assert o("avarice", "avaricia") == '...'
    assert o("huerto", "huerta") == '...'
    assert o("inculpar", "culpar") == '...'

    assert o("escupidura, escupida, lapo", "escupitajo") == '..., ..., lapo'

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
