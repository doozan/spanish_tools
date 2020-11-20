from build_deck import DeckBuilder

def test_get_location_classes():
    get_location_classes = DeckBuilder.get_location_classes

    tests = {
        "Louisiana": [ "only-latin-america", "only-united-states", "louisiana", "only-louisiana" ],
        "Peru": [ "only-latin-america", "only-south-america", "only-peru", "peru" ],
        "slang, Mexico, Peru": [ "only-latin-america", "mexico", "peru" ],
        "slang, Mexico, Spain": [ "mexico", "spain" ],
        "slang, Mexico, test, Peru, blah, Panama": [ "only-latin-america", "mexico", "peru", "panama" ],
        "slang, Mexico, Latin America, Peru, blah, Panama": [ "only-latin-america", "mexico", "latin-america", "peru", "panama" ],
    }

    for tags, locations in tests.items():
        assert sorted(get_location_classes(tags)) == sorted(locations)

def test_format_def():
    format_def = DeckBuilder.format_def

    item = { "m": { "tag": [ "def1", "def2" ] } }
    assert format_def(item) == """<span class="pos noun m"> <span class="tag">[tag]:</span><span class="usage">def1; def2</span></span>"""

    item = { "m": { "Peru": [ "def1", "def2" ] } }
    assert format_def(item) == """<span class="pos noun m only-latin-america only-peru only-south-america peru"> <span class="tag">[Peru]:</span><span class="usage">def1; def2</span></span>"""

    item = { "m": { "South America": [ "def1", "def2" ] } }
    assert format_def(item) == """<span class="pos noun m only-latin-america only-south-america south-america"> <span class="tag">[South America]:</span><span class="usage">def1; def2</span></span>"""

def test_filters():
    ignore_data = """\
# comment
#
- abuela {f}
- abuelo {m} :: loose tufts
"""

    dictionary_data = """\
abuela {noun-meta} :: x
abuela {noun-forms} :: m=abuelo; mpl=abuelos; pl=abuelas
abuela {f} :: grandmother, female equivalent of "abuelo"
abuela {f} [colloquial] :: old woman
abuela {f} [Mexico] :: a kind of flying ant
abuelo {noun-meta} :: x
abuelo {noun-forms} :: f=abuela; fpl=abuelas; pl=abuelos
abuelo {m} :: grandfather
abuelo {m} [colloquial, endearing] :: an elderly person
abuelo {m} | tolano :: loose tufts of hair in the nape when one's hair is messed up
"""


    dictionary = DeckBuilder.load_dictionary_data(dictionary_data.splitlines())
    ignore = None
    sentences = None
    shortdefs = {}

    # Full definition without ignore list
    deck = DeckBuilder(dictionary, ignore, sentences, shortdefs)
    assert deck.filter_gloss("abuela", "", "", "grandmother") == "grandmother"
    assert deck.filter_gloss("abuela", "", "", 'grandmother, female equivalent of "abuelo"') == "grandmother"

    usage = deck.get_usage("abuelo", "noun")
    assert usage == {
        'm/f':
        {'f': ['grandmother'],
         'f, colloquial': ['old woman'],
         'f, Mexico': ['a kind of flying ant'],
         'm': ['grandfather', "loose tufts of hair in the nape when one's hair is messed up"],
         'm, colloquial, endearing': ['an elderly person']
        }}


    # With ignore list
    ignore = DeckBuilder.load_ignore_data(ignore_data.splitlines())
    deck = DeckBuilder(dictionary, ignore, sentences, shortdefs)

    assert deck.filter_gloss("abuela", "x", "", "grandmother") == "grandmother"
    assert deck.filter_gloss("abuela", "f", "", "grandmother") == None
    assert deck.filter_gloss("abuela", "f", "colloquial", "old woman") == None
    assert deck.filter_gloss("abuelo", "m", "", "loose tufts of hair") == None
    assert deck.filter_gloss("abuelo", "m", "", "grandfather") == "grandfather"

    usage = deck.get_usage("abuelo", "noun")
    assert usage == {
        'm/f':
        {
         '': ['grandfather'],
         'colloquial, endearing': ['an elderly person']
        }}


def test_filters2():
    ignore_data = """\
- test {f}
"""

    dictionary_data = """\
test {noun-meta} :: x
test {noun-forms} :: pl=tests
test {m} :: masculine
test {noun-meta} :: x
test {noun-forms} :: pl=tests
test {f} :: feminine
"""

    dictionary = DeckBuilder.load_dictionary_data(dictionary_data.splitlines())
    ignore = None
    sentences = None
    shortdefs = {}

    # Full definition without ignore list
    deck = DeckBuilder(dictionary, ignore, sentences, shortdefs)

    usage = deck.get_usage("test", "noun")
    print(usage)
    assert usage == {
        'm-f':
        {'f': ['feminine'],
         'm': ['masculine']
        }}


    # With ignore list
    ignore = DeckBuilder.load_ignore_data(ignore_data.splitlines())
    deck = DeckBuilder(dictionary, ignore, sentences, shortdefs)

    usage = deck.get_usage("test", "noun")
    assert usage == {
        'm':
        {
         '': ['masculine'],
        }}


def test_shorten_defs():

    item = { "m": { "": [ "def1", "def2" ] } }
    assert DeckBuilder.shorten_defs(item, 1000) == { "m": { "": [ "def1", "def2" ] } }

    # No cutoff of number of items
    item = { "m": { "": [ "def1", "def2", "def3", "def4" ] } }
    assert DeckBuilder.shorten_defs(item, 1000) == { "m": { "": [ "def1", "def2", "def3", "def4" ] } }

    # Only first two tags
    item = { "m": { "": [ "def1", "def2", "def3", "def4" ], "x": ["x1", "x2", "x3"], "y": ["y1", "y2", "y3"] } }
    assert DeckBuilder.shorten_defs(item, 1000) == { "m": { "": [ "def1", "def2", "def3", "def4" ], "x": ["x1","x2","x3"] } }

    # Only the first part of speech
    item = { "m": { "": [ "def1", "def2", "def3", "def4" ] }, "v": { "": ["v1", "v2", "v3"] } }
    assert DeckBuilder.shorten_defs(item, 1000) == { "m": { "": [ "def1", "def2", "def3", "def4" ] } }

    # m/f, mf, and m-f always include both m and f
    item = { "m/f": { "m": [ "def1", "def2" ], "f": ["def4"] } }
    assert DeckBuilder.shorten_defs(item, 1000) == { "m/f": { "f": [ "def4" ], "m": [ "def1", "def2" ] } }
    item = { "mf": { "m": [ "def1", "def2" ], "f": ["def4"] } }
    assert DeckBuilder.shorten_defs(item, 1000) == { "mf": { "f": [ "def4" ], "m": [ "def1", "def2" ] } }
    item = { "m-f": { "m": [ "def1", "def2" ], "f": ["def4"] } }
    assert DeckBuilder.shorten_defs(item, 1000) == { "m-f": { "f": [ "def4" ], "m": [ "def1", "def2" ] } }

    # simple shortener
    item = { "m": { "": [ "def1", "def2", "def3", "def4" ] } }
    assert DeckBuilder.shorten_defs(item, 23) == { "m": { "": [ "def1", "def2", "def3", "def4" ] } }

    item = { "m": { "": [ "def1", "def2", "def3", "def4" ] } }
    assert DeckBuilder.shorten_defs(item, 22) == { "m": { "": [ "def1", "def2", "def3" ] } }

    item = { "m": { "": [ "def1", "def2", "def3", "def4" ] } }
    assert DeckBuilder.shorten_defs(item, 16) == { "m": { "": [ "def1", "def2" ] } }

    item = { "m": { "": [ "def1", "def2", "def3", "def4" ] } }
    assert DeckBuilder.shorten_defs(item, 10) == { "m": { "": [ "def1" ] } }


    item = { "m": { "": [ "def1", "def2" ], "a really long tag":[ "def3", "def4" ] } }
    assert DeckBuilder.shorten_defs(item, 60) == {'m': {'': ['def1', 'def2'], 'a really long tag': ['def3', 'def4']}}

    item = { "m": { "": [ "(qualifier) a really long def1", "def2" ] } }
    assert DeckBuilder.shorten_defs(item, 20) == {'m': {'': ['(qualifier) a really long def1']}}

    item = { "m": { "": [ "a really long def1 (blah)", "def2" ] } }
    assert DeckBuilder.shorten_defs(item, 20) == {'m': {'': ['a really long def1']}}

    item = { "m": { "": [ "a really, really, long def1 (blah)", "def2" ] } }
    assert DeckBuilder.shorten_defs(item, 20) == {'m': {'': ['a really', 'def2']}}

def test_format_def():

    dictionary_data = """\
rendir {verb-meta} :: {{es-verb|rend|ir|pres=rindo}} {{es-conj-ir|r|nd|p=e-i|combined=1}}
rendir {vt} :: to conquer
rendir {vt} :: to tire, exhaust
rendir {v} [ditransitive] :: to yield, pay, submit, pass down
rendir {vi} :: to vomit
rendir {vi} :: to make headway
rendir {vr} :: to surrender, give in, give up
rendir {vr} :: to be paid (homage or tribute)
"""

    dictionary = DeckBuilder.load_dictionary_data(dictionary_data.splitlines())
    ignore = None
    sentences = None
    shortdefs = {}

    # Full definition without ignore list
    deck = DeckBuilder(dictionary, ignore, sentences, shortdefs)

    usage = deck.get_usage("rendir", "verb")
    print(usage)
    assert usage == {
          'v': {'ditransitive': ['to yield, pay, submit, pass down']},
          'vi': {'': ['to vomit', 'to make headway']},
          'vr': {'': ['to surrender, give in, give up',
                      'to be paid (homage or tribute)']},
          'vt': {'': ['to conquer', 'to tire, exhaust']}}
