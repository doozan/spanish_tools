import build_deck


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

