from build_deck import DeckBuilder


def test_get_location_classes():
    get_location_classes = build_deck.get_location_classes

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

def test_init_data():
    init_data = build_deck.init_data

    init_data("es-en.txt", "sentences.tsv", "../spanish_data", "../spanish_custom")

def test_format_def():
    format_def = build_deck.format_def

    item = { "m": { "tag": [ "def1", "def2" ] } }
    assert format_def(item) == """<span class="pos noun m"> <span class="tag">[tag]:</span><span class="usage">['def1', 'def2']</span></span>"""

    item = { "m": { "Peru": [ "def1", "def2" ] } }
    assert format_def(item) == """<span class="pos noun m only-latin-america only-peru only-south-america peru"> <span class="tag">[Peru]:</span><span class="usage">['def1', 'def2']</span></span>"""

    item = { "m": { "South America": [ "def1", "def2" ] } }
    assert format_def(item) == """<span class="pos noun m only-latin-america only-south-america south-america"> <span class="tag">[South America]:</span><span class="usage">['def1', 'def2']</span></span>"""



def test_filters():
    ignore_data = """\
# comment
#
- abuela {f}
- abuelo {m} :: loose tufts
"""

    dictionary_data = """\
abuela {noun-forms} :: m=abuelo; mpl=abuelos; pl=abuelas
abuela {f} :: grandmother, female equivalent of "abuelo"
abuela {f} [colloquial] :: old woman
abuela {f} [Mexico] :: a kind of flying ant
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
test {noun-forms} :: pl=tests
test {m} :: masculine
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
