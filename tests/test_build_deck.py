from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms
from ..build_deck import DeckBuilder

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

def notest_filters():
    ignore_data = """\
# comment
#
- abuela {f}
- abuelo {m} :: loose tufts
"""

    wordlist_data = """\
abuela {n-meta} :: {{es-noun|m=abuelo}}
abuela {f} :: grandmother, female equivalent of "abuelo"
abuela {f} [colloquial] :: old woman
abuela {f} [Mexico] :: a kind of flying ant
abuelo {n-meta} :: {{es-noun|f=abuela}}
abuelo {m} :: grandfather
abuelo {m} [colloquial, endearing] :: an elderly person
abuelo {m} | tolano :: loose tufts of hair in the nape when one's hair is messed up
"""


    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)

    # Full definition without ignore list
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)
    assert deck.filter_gloss("abuela", "", "", "grandmother") == "grandmother"
    assert deck.filter_gloss("abuela", "", "", 'grandmother, female equivalent of "abuelo"') == "grandmother"

    usage = deck.get_usage("abuelo", "n")
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
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    assert deck.filter_gloss("abuela", "x", "", "grandmother") == "grandmother"
    assert deck.filter_gloss("abuela", "f", "", "grandmother") == None
    assert deck.filter_gloss("abuela", "f", "colloquial", "old woman") == None
    assert deck.filter_gloss("abuelo", "m", "", "loose tufts of hair") == None
    assert deck.filter_gloss("abuelo", "m", "", "grandfather") == "grandfather"

    usage = deck.get_usage("abuelo", "n")
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

    wordlist_data = """\
test {n-meta} :: x
test {n-forms} :: pl=tests
test {m} :: masculine
test {n-meta} :: x
test {n-forms} :: pl=tests
test {f} :: feminine
"""

    xwordlist_data = """\
_____
test
  forms: pl=tests
  pos: n
  form: m
  gloss: masculine
____
test
  forms: pl=tests
  pos: n
  form: f
  gloss: feminine
"""


    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)

    # Full definition without ignore list
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    usage = deck.get_usage("test", "n")
    print(usage)
    assert usage == [
            {
                'words': [{
                    'pos': 'n',
                    'senses': [
                        {'type': 'm', 'gloss': 'masculine', 'hint': ''},
                        {'type': 'f', 'gloss': 'feminine', 'hint': ''}],
                    'noun_type': 'm-f'
                }]
            }]


    # With ignore list
    ignore = DeckBuilder.load_ignore_data(ignore_data.splitlines())
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    usage = deck.get_usage("test", "n")
    print(usage)
    assert usage == [
            {
                'words': [{
                    'pos': 'n',
                    'senses': [
                        {'gloss': 'masculine', 'hint': ''}],
                    'noun_type': 'm'
                }]
            }]


#[{'ety': None, 'words': [{'pos': 'n', 'senses': [{'tag': 'm', 'gloss': 'masculine', 'hint': ''}], 'noun_type': 'm-f'}]}]

def notest_shorten_gloss():

    item = { "m": { "": [ "def1", "def2" ] } }
    assert DeckBuilder.shorten_gloss(item, 1000) == { "m": { "": [ "def1", "def2" ] } }

    # No cutoff of number of items
    item = { "m": { "": [ "def1", "def2", "def3", "def4" ] } }
    assert DeckBuilder.shorten_gloss(item, 1000) == { "m": { "": [ "def1", "def2", "def3", "def4" ] } }

    # Only first two tags
    item = { "m": { "": [ "def1", "def2", "def3", "def4" ], "x": ["x1", "x2", "x3"], "y": ["y1", "y2", "y3"] } }
    assert DeckBuilder.shorten_gloss(item, 1000) == { "m": { "": [ "def1", "def2", "def3", "def4" ], "x": ["x1","x2","x3"] } }

    # Only the first part of speech
    item = { "m": { "": [ "def1", "def2", "def3", "def4" ] }, "v": { "": ["v1", "v2", "v3"] } }
    assert DeckBuilder.shorten_gloss(item, 1000) == { "m": { "": [ "def1", "def2", "def3", "def4" ] } }

    # m/f, mf, and m-f always include both m and f
    item = { "m/f": { "m": [ "def1", "def2" ], "f": ["def4"] } }
    assert DeckBuilder.shorten_gloss(item, 1000) == { "m/f": { "f": [ "def4" ], "m": [ "def1", "def2" ] } }
    item = { "mf": { "m": [ "def1", "def2" ], "f": ["def4"] } }
    assert DeckBuilder.shorten_gloss(item, 1000) == { "mf": { "f": [ "def4" ], "m": [ "def1", "def2" ] } }
    item = { "m-f": { "m": [ "def1", "def2" ], "f": ["def4"] } }
    assert DeckBuilder.shorten_gloss(item, 1000) == { "m-f": { "f": [ "def4" ], "m": [ "def1", "def2" ] } }

    # simple shortener
    item = { "m": { "": [ "def1", "def2", "def3", "def4" ] } }
    assert DeckBuilder.shorten_gloss(item, 23) == { "m": { "": [ "def1", "def2", "def3", "def4" ] } }

    item = { "m": { "": [ "def1", "def2", "def3", "def4" ] } }
    assert DeckBuilder.shorten_gloss(item, 22) == { "m": { "": [ "def1", "def2", "def3" ] } }

    item = { "m": { "": [ "def1", "def2", "def3", "def4" ] } }
    assert DeckBuilder.shorten_gloss(item, 16) == { "m": { "": [ "def1", "def2" ] } }

    item = { "m": { "": [ "def1", "def2", "def3", "def4" ] } }
    assert DeckBuilder.shorten_gloss(item, 10) == { "m": { "": [ "def1" ] } }


    item = { "m": { "": [ "def1", "def2" ], "a really long tag":[ "def3", "def4" ] } }
    assert DeckBuilder.shorten_gloss(item, 60) == {'m': {'': ['def1', 'def2'], 'a really long tag': ['def3', 'def4']}}

    item = { "m": { "": [ "(qualifier) a really long def1", "def2" ] } }
    assert DeckBuilder.shorten_gloss(item, 20) == {'m': {'': ['(qualifier) a really long def1']}}

    item = { "m": { "": [ "(intransitive, or transitive with con(of) or en(about)) to dream", "def2" ] } }
    assert DeckBuilder.shorten_gloss(item, 20) == {'m': {'': ['(intransitive, or transitive with con(of) or en(about)) to dream']}}

    item = { "m": { "": [ "a really long def1 (blah)", "def2" ] } }
    assert DeckBuilder.shorten_gloss(item, 20) == {'m': {'': ['a really long def1']}}

    item = { "m": { "": [ "a really, really, long def1 (blah)", "def2" ] } }
    assert DeckBuilder.shorten_gloss(item, 20) == {'m': {'': ['a really', 'def2']}}

    item = {'mf': {'': ['interpreter (one who interprets speech in another language)'], 'music, dance': ['performer']}}

    short = DeckBuilder.shorten_gloss(item, 200)
    assert short == {'mf': {'': ['interpreter (one who interprets speech in another language)'], 'music, dance': ['performer']}}

    short = DeckBuilder.shorten_gloss(item, 80)
    assert short == {'mf': {'': ['interpreter'], 'music, dance': ['performer']}}

    short = DeckBuilder.shorten_gloss(item, 20)
    assert short == {'mf': {'': ['interpreter']}}

    item = { "mf": { 'Mexico, derogatory': ['One who has a preference or infatuation for foreign (non-Mexican) culture, products or people'] }}
    short = DeckBuilder.shorten_gloss(item, 20)
    print(short)
    assert short == { "mf": { 'Mexico, derogatory': ['One who has a preference or infatuation for foreign (non-Mexican) culture'] }}

    item = {'adj': {'': ['popular'], 'politics, Spain': ['Pertaining to PP (Partido Popular)']}}
    assert DeckBuilder.shorten_gloss(item, 20) == {'adj': {'': ['popular'], 'politics, Spain': ['Pertaining to PP']}}

def test_usage():

    wordlist_data = """\
_____
rendir
pos: v
  meta: {{es-verb|rend|ir|pres=rindo}} {{es-conj-ir|r|nd|p=e-i|combined=1}}
  gloss: to conquer
    q: transitive
  gloss: to tire, exhaust
    q: transitive
  gloss: to yield, pay, submit, pass down
    q: ditransitive
  gloss: to vomit
    q: intransitive
  gloss: to make headway
    q: intransitive
  gloss: to surrender, give in, give up
    q: reflexive
  gloss: to be paid (homage or tribute)
    q: reflexive
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)

    # Full definition without ignore list
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    usage = deck.get_usage("rendir", "v")
    print(usage)
    assert usage == [{
        'words': [{
            'pos': 'v',
            'senses': [
                {'type': 't', 'gloss': 'to conquer', 'hint': ''},
                {'type': 't', 'gloss': 'to tire, exhaust'},
                {'tag': 'ditransitive', 'gloss': 'to yield, pay, submit, pass down'},
                {'type': 'i', 'gloss': 'to vomit'},
                {'type': 'i', 'gloss': 'to make headway'},
                {'type': 'r', 'gloss': 'to surrender, give in, give up', 'hint': ''},
                {'type': 'r', 'gloss': 'to be paid (homage or tribute)'}]}]}]

'''
    item = {'m/f': {'': ['retiree, pensioner (retired person)']}}
    assert DeckBuilder.format_def(item, hide_word="jubilado") == '<span class="pos n m_f mf">{mf} <span class="usage">retiree, pensioner (retired person)</span></span>'


    format_def = DeckBuilder.format_def

    item = { "m": { "tag": [ "def1", "def2" ] } }
    assert format_def(item) == """<span class="pos n m"> <span class="tag">[tag]:</span><span class="usage">def1 | def2</span></span>"""

    item = { "m": { "Peru": [ "def1", "def2" ] } }
    assert format_def(item) == """<span class="pos n m only-latin-america only-peru only-south-america peru"> <span class="tag">[Peru]:</span><span class="usage">def1 | def2</span></span>"""

    item = { "m": { "South America": [ "def1", "def2" ] } }
    assert format_def(item) == """<span class="pos n m only-latin-america only-south-america south-america"> <span class="tag">[South America]:</span><span class="usage">def1 | def2</span></span>"""

    item = {'f': {'': ['sewer, storm drain'], 'zoology': ['cloaca']}}
    assert format_def(item, hide_word='cloaca') == """<span class="pos n f"> <span class="usage">sewer, storm drain</span></span>"""
'''

def test_usage2():

    wordlist_data = """\
_____
guía
pos: n
  meta: {{es-noun|mf}}
  g: mf
  usage: The noun guía is like several other Spanish nouns with a human referent and ending in a.\\nThe masculine articles and adjectives are used when the referent is male or unknown.
  etymology: Probably from the verb guiar. Cf. also French "guide" (Old French "guie"), Italian "guida".
  gloss: guide (person)
pos: n
  meta: {{es-noun|f}}
  g: f
  etymology: Probably from the verb guiar. Cf. also French "guide" (Old French "guie"), Italian "guida".
  gloss: guidebook
  gloss: directory
  gloss: cocket
pos: v
  meta: {{head|es|verb form}}
  etymology: Probably from the verb guiar. Cf. also French "guide" (Old French "guie"), Italian "guida".
  gloss: inflection of "guiar"
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)

    # Full definition without ignore list
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    usage = deck.get_usage("guía", "n")
    print(usage)
    assert usage == [{
        'ety': 'Probably from the verb guiar. Cf. also French "guide" (Old French "guie"), Italian "guida".',
        'words': [{
            'pos': 'n',
            'noun_type': 'mf',
            'note': 'The noun guía is like several other Spanish nouns with a human referent and ending in a.\\nThe masculine articles and adjectives are used when the referent is male or unknown.',
            'senses': [
                {'gloss': 'guide (person)', 'hint': ''}],
            }, {
            'pos': 'n',
            'noun_type': 'f',
            'senses': [
                {'gloss': 'guidebook'},
                {'gloss': 'directory'},
                {'gloss': 'cocket'}],
            }]
        }]

    print(deck.format_usage(usage))
    assert deck.format_usage(usage) == """\
<div class="etymology etymology_0 solo_etymology">
<span class="pos n mf"><span class="pos_tag pos_tag_primary">mf</span><span class="gloss">guide (person)</span><span class="footnote_link usage_link">1</span></span>
<span class="pos n hint mf"><span class="pos_tag pos_tag_primary">mf</span><span class="gloss">guide (person)</span><span class="footnote_link usage_link">1</span></span>
<span class="pos n f"><span class="pos_tag pos_tag_primary">f</span><span class="gloss">guidebook</span></span>
<span class="pos n f"><span class="pos_tag pos_tag_primary">f</span><span class="gloss">directory</span></span>
<span class="pos n f"><span class="pos_tag pos_tag_primary">f</span><span class="gloss">cocket</span></span>
</div>
<span id="footnote_1" class="footnote usage_footnote solo_footnote"><span class="footnote_id">1</span><span class="footnote_data">The noun guía is like several other Spanish nouns with a human referent and ending in a.<br>The masculine articles and adjectives are used when the referent is male or unknown.</span></span>
<span id="footnote_a" class="footnote ety_footnote solo_footnote"><span class="footnote_id">a</span><span class="footnote_data">Probably from the verb guiar. Cf. also French "guide" (Old French "guie"), Italian "guida".</span></span>
"""

def test_usage_reo():

    wordlist_data = """\
_____
rea
pos: n
  meta: {{es-noun|f|m=reo}}
  g: f
  gloss: female equivalent of "reo"
_____
reo
pos: n
  meta: {{es-noun|m|f=rea}}
  g: m
  etymology: Borrowed from Latin "reus" (“accused”). Compare réu .
  gloss: defendant (as in a trial)
  gloss: delinquent
pos: adj
  meta: {{es-adj}}
  etymology: Borrowed from Latin "reus" (“accused”). Compare réu .
  gloss: accused of a crime
  gloss: found guilty of a crime
pos: n
  meta: {{es-noun|m}}
  g: m
  etymology: Uncertain; probably from Celto-Latin "rhēdo", redo.
  gloss: sea trout
    q: zoology
pos: n
  meta: {{es-noun|m}}
  g: m
  etymology: Borrowed from Catalan "reu".
  gloss: turn (in a game)
    syn: vez; turno
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)

    # Full definition without ignore list
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    usage = deck.get_usage("reo", "n")
    print(usage)
    assert usage == [{
        'ety': 'Borrowed from Latin "reus" (“accused”). Compare réu .',
        'words': [{
            'pos': 'n',
            'senses': [
                {'gloss': 'defendant (as in a trial)', 'hint': ''},
                {'gloss': 'delinquent', 'hint': ''}
                ],
            'noun_type': 'm/f'
            }, {
            'pos': 'adj',
            'senses': [
                {'gloss': 'accused of a crime'},
                {'gloss': 'found guilty of a crime'}
                ]
            }]
            }, {
            'ety': 'Uncertain; probably from Celto-Latin "rhēdo", redo.',
            'words': [{
                'pos': 'n',
                'senses': [
                    {'tag': 'zoology', 'gloss': 'sea trout'}],
                'noun_type': 'm'
                }]
            }, {
            'ety': 'Borrowed from Catalan "reu".',
            'words': [{
                'pos': 'n',
                'senses': [
                    {'gloss': 'turn (in a game)'}],
                'noun_type': 'm'
                }]
            }]

    print(deck.format_usage(usage))
    assert deck.format_usage(usage) == """\
<div class="etymology etymology_0">
<span class="pos n mf"><span class="pos_tag pos_tag_primary">m/f</span><span class="gloss">defendant (as in a trial)</span><span class="footnote_link ety_link">a</span></span>
<span class="pos n hint mf"><span class="pos_tag pos_tag_primary">m/f</span><span class="gloss">defendant (as in a trial)</span><span class="footnote_link ety_link">a</span></span>
<span class="pos n mf"><span class="pos_tag pos_tag_primary">m/f</span><span class="gloss">delinquent</span><span class="footnote_link ety_link">a</span></span>
<span class="pos n hint mf"><span class="pos_tag pos_tag_primary">m/f</span><span class="gloss">delinquent</span><span class="footnote_link ety_link">a</span></span>
<span class="pos adj"><span class="pos_tag">adj</span><span class="gloss">accused of a crime</span><span class="footnote_link ety_link">a</span></span>
<span class="pos adj"><span class="pos_tag">adj</span><span class="gloss">found guilty of a crime</span><span class="footnote_link ety_link">a</span></span>
</div>
<div class="etymology etymology_1">
<span class="pos n m"><span class="pos_tag pos_tag_primary">m</span><span class="qualifier">zoology</span><span class="gloss">sea trout</span><span class="footnote_link ety_link">b</span></span>
</div>
<div class="etymology etymology_2">
<span class="pos n m"><span class="pos_tag pos_tag_primary">m</span><span class="gloss">turn (in a game)</span><span class="footnote_link ety_link">c</span></span>
</div>
<span id="footnote_a" class="footnote ety_footnote"><span class="footnote_id">a</span><span class="footnote_data">Borrowed from Latin "reus" (“accused”). Compare réu .</span></span>
<span id="footnote_b" class="footnote ety_footnote"><span class="footnote_id">b</span><span class="footnote_data">Uncertain; probably from Celto-Latin "rhēdo", redo.</span></span>
<span id="footnote_c" class="footnote ety_footnote"><span class="footnote_id">c</span><span class="footnote_data">Borrowed from Catalan "reu".</span></span>
"""

def test_obscured():
    obscured = DeckBuilder.obscure_list
    o = DeckBuilder.obscure_gloss

    assert o("this is a test", "test") == "this is a ..."
    assert o('plural of "blah"', "test") == 'plural of "blah"'
    assert o('plural of "blah" (blah)', "test") == '... (blah)'
    assert o('blah, plural of "blah"', "test") == 'blah, ...'

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

    # < 4 characters should require an exact match
    assert list(obscured(["abc", "abz"], "abc")) == ['...', 'abz']
    assert list(obscured(["to be (essentially or identified as)"], "ser")) == ['to be (essentially or identified as)']

    # 4 characters allows distance 1
    assert list(obscured(["test, pest, test1, test12, test123"], "test")) == ['..., ..., ..., test12, test123']
    assert list(obscured(["test", "pest", "test1", "test12", "test123"], "test")) == ['...', '...', '...', 'test12', 'test123']

    # 8+ allows distance 2
    assert list(obscured(["testtest, testpest, testtest1, testtest12, testtest123"], "testtest")) == ['..., ..., ..., ..., testtest123']
    assert list(obscured(["testtest", "testpest", "testtest1", "testtest12", "testtest123"], "testtest")) == ['...', '...', '...', '...', 'testtest123']

    # split words with spaces
    assert list(obscured(["test 123", "123 test"], "test")) == ['... 123', '123 ...']
    assert list(obscured(["avarice"], "avaricia")) == ['...']


def test_group_ety():

    wordlist_data = """\
_____
rea
pos: n
  meta: {{es-noun|f|m=reo}}
  g: f
  gloss: female equivalent of "reo"
_____
reo
pos: n
  meta: {{es-noun|m|f=rea}}
  g: m
  etymology: Borrowed from Latin "reus" (“accused”). Compare réu .
  gloss: defendant (as in a trial)
  gloss: delinquent
pos: adj
  meta: {{es-adj}}
  etymology: Borrowed from Latin "reus" (“accused”). Compare réu .
  gloss: accused of a crime
  gloss: found guilty of a crime
pos: n
  meta: {{es-noun|m}}
  g: m
  etymology: Uncertain; probably from Celto-Latin "rhēdo", redo.
  gloss: sea trout
    q: zoology
pos: n
  meta: {{es-noun|m}}
  g: m
  etymology: Borrowed from Catalan "reu".
  gloss: turn (in a game)
    syn: vez; turno
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)
    assert len(allforms.all_forms) == 4

    # Full definition without ignore list
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    words = deck.get_word_objs("reo", "n", False)
    assert len(words) == 3
    defs = [ sense.gloss for word in words for sense in word.senses ]
    assert defs == ['defendant (as in a trial)', 'delinquent', 'sea trout', 'turn (in a game)']

    words = deck.get_word_objs("reo", "adj", False)
    assert len(words) == 1
    defs = [ sense.gloss for word in words for sense in word.senses ]
    assert defs == ['accused of a crime', 'found guilty of a crime']

    words = deck.get_word_objs("reo", "n", True)
    assert len(words) == 4
    defs = [ sense.gloss for word in words for sense in word.senses ]
    assert defs == ['defendant (as in a trial)', 'delinquent', 'sea trout', 'turn (in a game)', 'accused of a crime', 'found guilty of a crime']

    etys = list(deck.group_ety(words))
    assert len(etys) == 3
    ety_texts = [ ety[0].etymology for ety in etys ]
    assert ety_texts == [
        'Borrowed from Latin "reus" (“accused”). Compare réu .',
        'Uncertain; probably from Celto-Latin "rhēdo", redo.',
        'Borrowed from Catalan "reu".'
        ]

    dump = []
    for ety in etys:
        dump.append(ety[0].etymology)
        for word in ety:
            dump.append(f"  {word.word},{word.pos}")
            for sense in word.senses:
                dump.append(f"    {sense.gloss}")
    assert dump == [
        'Borrowed from Latin "reus" (“accused”). Compare réu .',
        '  reo,n',
        '    defendant (as in a trial)',
        '    delinquent',
        '  reo,adj',
        '    accused of a crime',
        '    found guilty of a crime',
        'Uncertain; probably from Celto-Latin "rhēdo", redo.',
        '  reo,n',
        '    sea trout',
        'Borrowed from Catalan "reu".',
        '  reo,n',
        '    turn (in a game)'
        ]

def test_process_noun_mf():

    wordlist_data = """\
_____
gringa
pos: n
  meta: {{es-noun|f}}
  g: f
  gloss: female equivalent of "gringo"
  gloss: a type of taco
    q: Mexico
_____
gringas
pos: n
  meta: {{head|es|noun form|g=f-p}}
  g: f-p
  gloss: plural of "gringa"
_____
gringo
pos: n
  meta: {{es-noun|m|f=gringa}}
  g: m
  etymology: Possibly from griego (“Greek”), particularly from the phrase hablar en griego (“to speak Greek”), with a similar connotation to the English phrase it's all Greek to me
  gloss: a foreigner whose native language is not Spanish
    q: sometimes derogatory, Latin America
    syn: gabacho; guiri
  gloss: an American (a person from the United States), particularly a white American
    q: sometimes derogatory, Latin America
_____
gringos
pos: n
  meta: {{head|es|noun form|g=m-p}}
  g: m-p
  gloss: plural of "gringo"
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)
    assert len(allforms.all_forms) == 4

    # Full definition without ignore list
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    words = deck.get_word_objs("gringo", "n", False)
    assert len(words) == 1

    words = deck.get_word_objs("gringa", "n", False)
    assert len(words) == 1

    words = deck.get_word_objs("gringo", "n", True)
    assert len(words) == 1

    etys = list(deck.group_ety(words))
    assert len(etys) == 1

    words = etys[0]
    assert len(words) == 1

    nouns = deck.process_nouns(words)

    data = []
    for k,v in nouns.items():
        data.append(k)
        for w in v:
            if k == "m/f":
                ws = w
                for w in ws:
                    data.append(f"    {w.word} {w.pos} {w.genders} {w.forms}")

                data.append(f"    --")
            else:
                data.append(f"    {w.word} {w.pos} {w.genders} {w.forms}")

    data = "\n".join(data)
    print(data)
    assert data == """m/f
    gringo n m {'pl': ['gringos'], 'f': ['gringa'], 'fpl': ['gringas']}
    gringa n f {'pl': ['gringas']}
    --"""


def test_process_noun_mf_m():

    wordlist_data = """\
_____
miembra
pos: n
  meta: {{es-noun|f}}
  g: f
  usage: The Real Academia Española advises against the use of miembra
  gloss: female equivalent of "miembro"
_____
miembras
pos: n
  meta: {{head|es|noun form|g=f-p}}
  g: f-p
  gloss: plural of "miembra"
_____
miembro
pos: n
  meta: {{es-noun|m|f=miembra}}
  g: m
  etymology: From Latin "membrum". Cognate with Asturian "miembru", Galician "membro".
  gloss: member (one who belongs to a group)
    syn: integrante; socio
pos: n
  meta: {{es-noun|m}}
  g: m
  etymology: From Latin "membrum". Cognate with Asturian "miembru", Galician "membro".
  gloss: limb (a major appendage of a person or animal)
    q: anatomy
    syn: extremidad
  gloss: penis
    syn: See Thesaurus:pene.
_____
miembros
pos: n
  meta: {{head|es|noun form|g=m-p}}
  g: m-p
  gloss: plural of "miembro"
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    words = deck.get_word_objs("miembro", "n", True)
    assert len(words) == 2

    etys = list(deck.group_ety(words))
    assert len(etys) == 1

    words = etys[0]
    assert len(words) == 2

    nouns = deck.process_nouns(words)
    data = []
    for k,v in nouns.items():
        data.append(k)
        for w in v:
            if k == "m/f":
                ws = w
                for w in ws:
                    data.append(f"    {w.word} {w.pos} {w.genders} {w.forms}")

                data.append(f"    --")
            else:
                data.append(f"    {w.word} {w.pos} {w.genders} {w.forms}")

    data = "\n".join(data)
    print(data)
#    assert data == """\
#m/f
#    miembro n m {'pl': ['miembros'], 'f': ['miembra'], 'fpl': ['miembras']}
#    --
#m
#    miembro n m {'pl': ['miembros']}\
##"""


    assert data == """\
m/f
    miembro n m {'pl': ['miembros'], 'f': ['miembra'], 'fpl': ['miembras']}
    miembra n f {'pl': ['miembras']}
    --
m
    miembro n m {'pl': ['miembros']}\
"""

def test_process_noun_m_f():

    wordlist_data = """\
_____
cometa
pos: n
  meta: {{es-noun|m}}
  g: m
  etymology: From Latin "comēta", from Ancient Greek "κομήτης" (“longhaired”), referring to the tail of a comet, from κόμη (“hair”).
  gloss: comet
    q: astronomy
pos: n
  meta: {{es-noun|f}}
  g: f
  etymology: From Latin "comēta", from Ancient Greek "κομήτης" (“longhaired”), referring to the tail of a comet, from κόμη (“hair”).
  gloss: kite
    syn: papalote; barrilete; piscucha; papalota; volantín
pos: v
  meta: {{head|es|verb form}}
  gloss: inflection of "cometer"
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    words = deck.get_word_objs("cometa", "n", True)
    assert len(words) == 2

    etys = list(deck.group_ety(words))
    assert len(etys) == 1

    words = etys[0]
    assert len(words) == 2

    nouns = deck.process_nouns(words)
    data = []
    for k,v in nouns.items():
        data.append(k)
        for w in v:
            if k == "m/f":
                ws = w
                for w in ws:
                    data.append(f"    {w.word} {w.pos} {w.genders} {w.forms}")

                data.append(f"    --")
            else:
                data.append(f"    {w.word} {w.pos} {w.genders} {w.forms}")

    data = "\n".join(data)
    print(data)
    assert data == """\
m-f
    cometa n m {'pl': ['cometas']}
    cometa n f {'pl': ['cometas']}\
"""

def test_process_noun_f_el():

    wordlist_data = """\
_____
ave
pos: n
  meta: {{es-noun|f}}
  g: f
  usage: * The feminine noun ave is like other feminine nouns starting with a stressed a sound in that it takes the definite article el (normally reserved for masculine nouns) in t
  etymology: From Latin "avis, avem", from Proto-Italic "*awis" (“bird”), from Proto-Indo-European "*h₂éwis".
  gloss: bird
    syn: pájaro
  gloss: fowl, poultry
    q: Chile
pos: interj
  meta: {{head|es|interjection}}
  etymology: From Old Spanish "ave", from Latin "avē" (“hello, hail”).
  gloss: hello, hail
    q: used when coming into a house
pos: n
  meta: {{es-noun|f}}
  g: f
  etymology: From the acronym AVE (Alta Velocidad Española), meaning high-speed train (written mostly all caps).
  gloss: train
    q: Spain
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    words = deck.get_word_objs("ave", "n", True)
    assert len(words) == 3

    etys = list(deck.group_ety(words))
    assert len(etys) == 3

    words = etys[0]
    assert len(words) == 1

    nouns = deck.process_nouns(words)
    assert list(nouns.keys()) == ["f-el"]


def test_usage_verb_reflexive():

    wordlist_data = """\
_____
tornar
pos: v
  meta: {{es-verb}} {{es-conj}}
  etymology: From Latin "tornāre", present active infinitive of tornō. Cognate with English "turn".
  gloss: to return
    q: transitive
    syn: devolver
  gloss: to come back
    q: intransitive
    syn: regresar; retornar; volver
  gloss: to put back
    q: transitive
  gloss: to change
    q: transitive
  gloss: to do again (+ a + infinitive)
    q: intransitive
  gloss: to revive (to recover from a state of unconsciousness)
    q: intransitive
  gloss: to become (e.g. change in a characteristic, nature of something or status)
    q: reflexive
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    words = deck.get_word_objs("tornar", "v", True)
    assert len(words) == 1

    print(deck.get_usage("tornar", "v"))
    assert deck.get_usage("tornar", "v") == [{
        'ety': 'From Latin "tornāre", present active infinitive of tornō. Cognate with English "turn".',
        'words': [{
            'pos': 'v',
            'senses': [
                {'type': 't', 'gloss': 'to return', 'hint': ''},
                {'type': 'i', 'gloss': 'to come back'},
                {'type': 't', 'gloss': 'to put back'},
                {'type': 't', 'gloss': 'to change'},
                {'type': 'i', 'gloss': 'to do again (+ a + infinitive)'},
                {'type': 'i', 'gloss': 'to revive (to recover from a state of unconsciousness)'},
                {'type': 'r', 'gloss': 'to become (e.g. change in a characteristic, nature of something or status)', 'hint': 'to become'}
                ]
            }]
        }]

def test_get_usage_m_f():

    wordlist_data = """\
_____
cólera
pos: n
  meta: {{es-noun|f}}
  g: f
  etymology: From Latin "cholera", from Ancient Greek "χολέρα", from χολή (“bile”).
  gloss: anger
    syn: rabia
pos: n
  meta: {{es-noun|m}}
  g: m
  etymology: From Latin "cholera", from Ancient Greek "χολέρα", from χολή (“bile”).
  gloss: cholera
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    words = deck.get_word_objs("cólera", "n", True)
    assert len(words) == 2


    assert deck.get_usage("cólera", "n") == [{
        'ety': 'From Latin "cholera", from Ancient Greek "χολέρα", from χολή (“bile”).',
        'words': [{
            'pos': 'n',
            'noun_type': 'm-f',
            'senses': [{
                'type': 'f', 'gloss': 'anger', 'hint': ''},{
                'type': 'm', 'gloss': 'cholera', 'hint': ''}],
             }]
        }]

def test_usage_mf():

    wordlist_data = """\
_____
morena
pos: n
  meta: {{es-noun|f}}
  g: f
  etymology: See moreno. Ultimately related to English "Moor".
  gloss: female equivalent of "moreno"
pos: adj
  meta: {{head|es|adjective form}}
  etymology: See moreno. Ultimately related to English "Moor".
  gloss: adjective form of "moreno"
pos: n
  meta: {{es-noun|f}}
  g: f
  etymology: from Latin "muraena" (“sea eel, lamprey”), from Ancient Greek "σμυραινα", from σμυρος (“sea eel”).
  gloss: moray
    q: zoology
_____
morenas
pos: adj
  meta: {{head|es|adjective form}}
  gloss: adjective form of "moreno"
pos: n
  meta: {{head|es|noun form|g=f-p}}
  g: f-p
  gloss: inflection of "morena"
_____
moreno
pos: adj
  meta: {{es-adj}}
  etymology: From moro + -eno.
  gloss: dark colored
  gloss: dark-skinned, tan
  gloss: dark-haired
pos: n
  meta: {{es-noun|m|f=morena}}
  g: m
  etymology: From moro + -eno.
  gloss: a dark-skinned or tan person
  gloss: a person with dark-hair
_____
morenos
pos: adj
  meta: {{head|es|adjective form}}
  gloss: adjective form of "moreno"
pos: n
  meta: {{head|es|noun form|g=m-p}}
  g: m-p
  gloss: inflection of "moreno"
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    words = deck.get_word_objs("moreno", "n", True)
    assert len(words) == 2

    assert deck.get_usage("moreno", "n") == [{
        'ety': 'From moro + -eno.',
        'words': [{
            'pos': 'n',
            'noun_type': 'm/f',
            'senses': [{
                'gloss': 'a dark-skinned or tan person', 'hint': ''}, {
                'gloss': 'a person with dark-hair', 'hint': ''}],
            }, {
            'pos': 'adj',
            'senses': [{
                'gloss': 'dark colored'}, {
                'gloss': 'dark-skinned, tan'}, {
                'gloss': 'dark-haired'}]}]}]



def test_shortdef_venado():

    wordlist_data = """\
_____
venado
pos: n
  meta: {{es-noun|m}}
  g: m
  etymology: From Latin "vēnātus" (whence English venison).
  gloss: deer, stag
    q: Latin America
    syn: ciervo
  gloss: venison
  gloss: cuckold, deceived husband or partner
    q: colloquial
    syn: cornudo
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    assert deck.get_usage("venado", "n") == [{
        'ety': 'From Latin "vēnātus" (whence English venison).',
        'words': [{
            'pos': 'n',
            'noun_type': 'm',
            'senses': [
                {'tag': 'Latin America', 'gloss': 'deer, stag', 'hint': ''},
                {'gloss': 'venison', 'hint': ''},
                {'tag': 'colloquial', 'gloss': 'cuckold, deceived husband or partner'}],
            }]
        }]


def test_abrigar():

    wordlist_data = """\
_____
abrigar
pos: v
  meta: {{es-verb}} {{es-conj}}
  etymology: Most likely from Late Latin "apricāre", from Latin "aprīcārī", present active infinitive of aprīcor (“warm in the sun”), from aprīcus (“sunny”)
  gloss: to wrap up (to put on abundant clothing)
    q: transitive, reflexive
  gloss: to cover
  gloss: to shelter, to protect
    syn: resguardar
  gloss: to bundle up
    q: reflexive
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    #assert deck.get_shortdef("abrigar", "v") == {'vtr': {'': ['to wrap up (to put on abundant clothing)']}, 'v': {'': ['to cover']}}

    usage = deck.get_usage("abrigar", "v")
    assert usage == [{
        'ety': 'Most likely from Late Latin "apricāre", from Latin "aprīcārī", present active infinitive of aprīcor (“warm in the sun”), from aprīcus (“sunny”)',
        'words': [{
            'pos': 'v',
            'senses': [{
                'type': 'tr',
                'gloss': 'to wrap up (to put on abundant clothing)',
                'hint': '',
                },{
                'gloss': 'to cover',
                'hint': '',
                }, {
                'gloss': 'to shelter, to protect'
                }, {
                'type': 'r',
                'gloss': 'to bundle up'
                }]
            }]
        }]

    print(deck.format_usage(usage))
    assert deck.format_usage(usage) == """\
<div class="etymology etymology_0 solo_etymology">
<span class="pos v"><span class="pos_tag pos_tag_primary">vtr</span><span class="gloss">to wrap up (to put on abundant clothing)</span></span>
<span class="pos v hint"><span class="pos_tag pos_tag_primary">vtr</span><span class="gloss">to wrap up (to put on abundant clothing)</span></span>
<span class="pos v"><span class="pos_tag pos_tag_primary">v</span><span class="gloss">to cover</span></span>
<span class="pos v hint"><span class="pos_tag pos_tag_primary">v</span><span class="gloss">to cover</span></span>
<span class="pos v"><span class="pos_tag pos_tag_primary">v</span><span class="gloss">to shelter, to protect</span></span>
<span class="pos v reflexive"><span class="pos_tag pos_tag_primary">vr</span><span class="gloss">to bundle up</span></span>
</div>
<span id="footnote_a" class="footnote ety_footnote solo_footnote"><span class="footnote_id">a</span><span class="footnote_data">Most likely from Late Latin "apricāre", from Latin "aprīcārī", present active infinitive of aprīcor (“warm in the sun”), from aprīcus (“sunny”)</span></span>
"""


def test_llorona():

    wordlist_data = """\
_____
llorona
pos: n
  meta: {{es-noun|f}}
  g: f
  gloss: weeping woman (from the Latin American folkloric legend La Llorona)
    q: folklore
  gloss: banshee (in general, by extension of the legend)
    q: informal
  gloss: female equivalent of "llorón"
_____
lloronas
pos: n
  meta: {{head|es|noun form|g=f-p}}
  g: f-p
  gloss: plural of "llorona"
_____
llorón
pos: n
  meta: {{es-noun|m|f=+}}
  g: m
  etymology: llorar + -ón
  gloss: crybaby, whiner
pos: adj
  meta: {{es-adj}}
  etymology: llorar + -ón
  gloss: sniveling, weeping, whiny
_____
llorones
pos: n
  meta: {{head|es|noun form|g=m-p}}
  g: m-p
  gloss: plural of "llorón"
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    usage = deck.get_usage("llorón", "n")
    print(usage)
    assert usage == [{
        'ety': 'llorar + -ón',
        'words': [{
            'pos': 'n',
            'noun_type': 'm/f',
            'senses': [
                {'type': 'm', 'gloss': 'crybaby, whiner', 'hint': ''},
                {'type': 'f', 'tag': 'folklore', 'gloss': 'weeping woman (from the Latin American folkloric legend La Llorona)', 'hint': 'weeping woman'},
                {'type': 'f', 'tag': 'informal', 'gloss': 'banshee (in general, by extension of the legend)'}],
            }, {
            'pos': 'adj',
            'senses': [
                {'gloss': 'sniveling, weeping, whiny'}]}]}]


    print("\n\n")
    print(deck.format_usage(usage))
    assert deck.format_usage(usage) == """\
<div class="etymology etymology_0 solo_etymology">
<span class="pos n m"><span class="pos_tag pos_tag_primary">m/f</span><span class="qualifier">m</span><span class="gloss">crybaby, whiner</span></span>
<span class="pos n hint m"><span class="pos_tag pos_tag_primary">m/f</span><span class="gloss">crybaby, whiner</span></span>
<span class="pos n f"><span class="pos_tag pos_tag_primary">m/f</span><span class="qualifier">f, folklore</span><span class="gloss">weeping woman (from the Latin American folkloric legend La Llorona)</span></span>
<span class="pos n hint f"><span class="pos_tag pos_tag_primary">m/f</span><span class="qualifier">folklore</span><span class="gloss">weeping woman</span></span>
<span class="pos n f"><span class="pos_tag pos_tag_primary">m/f</span><span class="qualifier">f, informal</span><span class="gloss">banshee (in general, by extension of the legend)</span></span>
<span class="pos adj"><span class="pos_tag">adj</span><span class="gloss">sniveling, weeping, whiny</span></span>
</div>
<span id="footnote_a" class="footnote ety_footnote solo_footnote"><span class="footnote_id">a</span><span class="footnote_data">llorar + -ón</span></span>
"""
