from ..deckbuilder.hider import Hider

def test_obscured():
    obscured = Hider.obscure_syns
    o = Hider.obscure_gloss

    assert o("this is a test", "test") == "this is a ..."
    assert o('plural of "test"', "test") == 'plural of "test"'
    assert o('plural of "test" (blah)', "test") == 'plural of "..." (blah)'
    assert o('blah, plural of "test"', "test") == 'blah, plural of "..."'

#    assert o('to be incumbent', "incumbir", hide_first=False) == 'to be incumbent'
#    assert o('to be incumbent', "incumbir", hide_first=True) == 'to be ...'

    assert o('test, blah', "test", hide_first=False) == 'test, blah'
    assert o('test, blah', "test", hide_first=True) == '..., blah'

    # hide_all overrides hide_first
    assert o('test, test', "test") == 'test, ...'
    assert o('test, test', "test", hide_first=False, hide_all=True) == '..., ...'
    assert o('test, test', "test", hide_first=True, hide_all=True) == '..., ...'

    assert o('to test, blah', "test", hide_first=False) == 'to test, blah'
    assert o('to test, blah', "test", hide_first=True) == 'to ..., blah'
    assert o('to test, test', "test", hide_all=False) == 'to test, ...'
    assert o('to test, test', "test", hide_first=True, hide_all=True) == 'to ..., ...'

    assert o('slander, calumny, aspersion, libel, defamation', 'calumnia') == "slander, ..., aspersion, libel, defamation"
    assert o('similarity, similitude', "similitud") == 'similarity, ...'
    assert o('similarity, similitude', "similitud", True, True) == 'similarity, ...'

    assert o('baton (in a marching band)', 'bastón', hide_first=True) == "... (in a marching band)"

    # < 4 characters should require an exact match
    assert list(obscured(["abc", "abz"], "abc")) == ['...', 'abz']
    assert list(obscured(["to be (essentially or identified as)"], "ser")) == ['to be (essentially or identified as)']

    # 4 characters allows distance 1
    assert list(obscured(["test, pest, test, test12, test123, te12"], "test")) == ['..., ..., ..., ..., ..., te12']

    # 8 allows distance 2
    assert list(obscured(["testtest, testpest, testtest1, testte12, testt123"], "testtest")) == ['..., ..., ..., ..., testt123']
    assert list(obscured(["testtest", "testpest", "testtest1234", "testte12", "testt123"], "testtest")) == ['...', '...', '...', '...', 'testt123']

    # split words with spaces
    assert list(obscured(["test 123", "123 test"], "test")) == ['... 123', '123 ...']
    assert list(obscured(["avarice"], "avaricia")) == ['...']

    assert list(obscured(["huerto"], "huerta")) == ['...']

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
        assert any(so(english,w) for w in Hider.get_hide_words(spanish, True))



