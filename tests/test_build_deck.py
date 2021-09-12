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

def test_get_verb_type_and_tag():
    f = DeckBuilder.get_verb_type_and_tag
    assert f('reflexive, colloquial, El Salvador') == ("r", "colloquial, El Salvador")
    assert f('colloquial, reflexive, El Salvador') == ("r", "colloquial, El Salvador")
    assert f('transitive, or reflexive') == ("tr", "")
    assert f('transitive or reflexive') == ("tr", "")
    assert f('transitive and reflexive') == ("tr", "")
    assert f('transitive, and reflexive') == ("tr", "")
    assert f('transitive, also reflexive') == ("tr", "")
    assert f('transitive, reflexive or non-reflexive') == ("tr", "non-reflexive")
    assert f('transitive, also takes a reflexive pronoun') == ("tp", "")
    assert f('figuratively, transitive, also takes a reflexive pronoun') == ("tp", "figuratively")

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

def test_shorten_gloss():

    short = DeckBuilder.shorten_gloss
    assert short("A wrestler whose in-ring persona embodies heroic or virtuous traits. Contrast with rudo (Spanish) or heel (English)", 60) \
            == "A wrestler whose in-ring persona embodies heroic or virtuous traits. Contrast with rudo (Spanish) or heel"

    assert short("def1, def2", 100) == "def1, def2"
    assert short("def1, def2", 5) == "def1"

    assert short("(qualifier) def1", 100) == "(qualifier) def1"
    assert short("(qualifier) def1", 5) == "(qualifier) def1"

    assert short("def1 (gloss)", 100) == "def1 (gloss)"
    assert short("def1 (gloss)", 5) == "def1"

    assert short("def1 (blah) still here", 100) == "def1 (blah) still here"
    assert short("def1 (blah) still here", 5) == "def1 (blah) still here"

    assert short("def1 (blah), not here", 5) == "def1 (blah)"

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
<span id="footnote_1" class="footnote usage_footnote"><span class="footnote_id">1</span><span class="footnote_data">The noun guía is like several other Spanish nouns with a human referent and ending in a.<br>The masculine articles and adjectives are used when the referent is male or unknown.</span></span>
<span id="footnote_a" class="footnote ety_footnote general_footnote"><span class="footnote_id">a</span><span class="footnote_data">Probably from the verb guiar. Cf. also French &quot;guide&quot; (Old French &quot;guie&quot;), Italian &quot;guida&quot;.</span></span>
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
                    {'gloss': 'turn (in a game)', 'syns': ['vez','turno']}],
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
<span class="pos n m"><span class="pos_tag pos_tag_primary">m</span><span class="gloss">turn (in a game)</span><span class="footnote_link ety_link">c</span><span class="synonyms">vez, turno</span></span>
</div>
<span id="footnote_a" class="footnote ety_footnote"><span class="footnote_id">a</span><span class="footnote_data">Borrowed from Latin &quot;reus&quot; (“accused”). Compare réu .</span></span>
<span id="footnote_b" class="footnote ety_footnote"><span class="footnote_id">b</span><span class="footnote_data">Uncertain; probably from Celto-Latin &quot;rhēdo&quot;, redo.</span></span>
<span id="footnote_c" class="footnote ety_footnote"><span class="footnote_id">c</span><span class="footnote_data">Borrowed from Catalan &quot;reu&quot;.</span></span>
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

    assert o('slander, calumny, aspersion, libel, defamation', 'calumnia') == "slander, ..., aspersion, libel, defamation"
    assert o('similarity, similitude', "similitud") == 'similarity, ...'
    assert o('similarity, similitude', "similitud", True, True) == 'similarity, ...'

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

    words = deck.get_word_objs("reo", "n")
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

    words = deck.get_word_objs("gringo", "n")
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

    words = deck.get_word_objs("miembro", "n")
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

    words = deck.get_word_objs("cometa", "n")
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

    words = deck.get_word_objs("ave", "n")
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

    words = deck.get_word_objs("tornar", "v")
    assert len(words) == 1

    print(deck.get_usage("tornar", "v"))
    assert deck.get_usage("tornar", "v") == [{
        'ety': 'From Latin "tornāre", present active infinitive of tornō. Cognate with English "turn".',
        'words': [{
            'pos': 'v',
            'senses': [
                {'type': 't', 'gloss': 'to return', 'hint': '', 'syns': ['devolver']},
                {'type': 'i', 'gloss': 'to come back', 'syns': ['regresar', 'retornar', 'volver']},
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

    words = deck.get_word_objs("cólera", "n")
    assert len(words) == 2


    assert deck.get_usage("cólera", "n") == [{
        'ety': 'From Latin "cholera", from Ancient Greek "χολέρα", from χολή (“bile”).',
        'words': [{
            'pos': 'n',
            'noun_type': 'm-f',
            'senses': [{
                'type': 'f', 'gloss': 'anger', 'hint': '', 'syns': ['rabia']},{
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

    words = deck.get_word_objs("moreno", "n")
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
                {'tag': 'Latin America', 'gloss': 'deer, stag', 'hint': '', 'syns': ['ciervo'] },
                {'gloss': 'venison', 'hint': ''},
                {'tag': 'colloquial', 'gloss': 'cuckold, deceived husband or partner', 'syns': ['cornudo'] }],
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
    print(usage)
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
                'gloss': 'to shelter, to protect',
                'syns': ['resguardar']
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
<span class="pos v"><span class="pos_tag pos_tag_primary">v</span><span class="gloss">to shelter, to protect</span><span class="synonyms">resguardar</span></span>
<span class="pos v reflexive"><span class="pos_tag pos_tag_primary">vr</span><span class="gloss">to bundle up</span></span>
</div>
<span id="footnote_a" class="footnote ety_footnote general_footnote"><span class="footnote_id">a</span><span class="footnote_data">Most likely from Late Latin &quot;apricāre&quot;, from Latin &quot;aprīcārī&quot;, present active infinitive of aprīcor (“warm in the sun”), from aprīcus (“sunny”)</span></span>
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
<span id="footnote_a" class="footnote ety_footnote general_footnote"><span class="footnote_id">a</span><span class="footnote_data">llorar + -ón</span></span>
"""


def test_caudal():

    wordlist_data = """\
_____
caudal
pos: n
  meta: {{es-noun|m}}
  g: m
  etymology: From Old Spanish "cabdal", from Latin "capitālis". Doublet of capital. Cognate with English "chattel", cattle and capital.
  gloss: flow
  gloss: volume
  gloss: funds
pos: adj
  meta: {{es-adj}}
  etymology: Borrowed from Latin "caudālis".
  gloss: caudal
_____
caudales
pos: adj
  meta: {{head|es|adjective form|g=m-p|g2=f-p}}
  g: m-p; f-p
  gloss: plural of "caudal"
pos: n
  meta: {{head|es|noun form|g=m-p}}
  g: m-p
  gloss: plural of "caudal"
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    usage = deck.get_usage("caudal", "n")
    print(usage)
    assert usage == [{
        'ety': 'From Old Spanish "cabdal", from Latin "capitālis". Doublet of capital. Cognate with English "chattel", cattle and capital.',
        'words': [{
            'pos': 'n',
            'noun_type': 'm',
            'senses': [
                {'gloss': 'flow', 'hint': ''},
                {'gloss': 'volume', 'hint': ''},
                {'gloss': 'funds'}],
            }]
            }, {
            'ety': 'Borrowed from Latin "caudālis".',
            'words': [{
                'pos': 'adj',
                'senses': [{'gloss': 'caudal'}]}]}]

    print("\n\n")
    print(deck.format_usage(usage))
    assert deck.format_usage(usage) == """\
<div class="etymology etymology_0">
<span class="pos n m"><span class="pos_tag pos_tag_primary">m</span><span class="gloss">flow</span><span class="footnote_link ety_link">a</span></span>
<span class="pos n hint m"><span class="pos_tag pos_tag_primary">m</span><span class="gloss">flow</span><span class="footnote_link ety_link">a</span></span>
<span class="pos n m"><span class="pos_tag pos_tag_primary">m</span><span class="gloss">volume</span><span class="footnote_link ety_link">a</span></span>
<span class="pos n hint m"><span class="pos_tag pos_tag_primary">m</span><span class="gloss">volume</span><span class="footnote_link ety_link">a</span></span>
<span class="pos n m"><span class="pos_tag pos_tag_primary">m</span><span class="gloss">funds</span><span class="footnote_link ety_link">a</span></span>
</div>
<div class="etymology etymology_1">
<span class="pos adj"><span class="pos_tag">adj</span><span class="gloss">caudal</span><span class="footnote_link ety_link">b</span></span>
</div>
<span id="footnote_a" class="footnote ety_footnote"><span class="footnote_id">a</span><span class="footnote_data">From Old Spanish &quot;cabdal&quot;, from Latin &quot;capitālis&quot;. Doublet of capital. Cognate with English &quot;chattel&quot;, cattle and capital.</span></span>
<span id="footnote_b" class="footnote ety_footnote"><span class="footnote_id">b</span><span class="footnote_data">Borrowed from Latin &quot;caudālis&quot;.</span></span>
"""

def test_similtud():

    wordlist_data = """\
_____
similitud
pos: n
  meta: {{es-noun|f}}
  g: f
  etymology: From Latin "similitūdō" (“likeness, similarity”).
  gloss: similarity, similitude
  syn: test1; Thesaurus:test2
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    usage = deck.get_usage("similitud", "n")
    print(usage)
    assert usage == [{
        'ety': 'From Latin "similitūdō" (“likeness, similarity”).',
        'words': [{
            'pos': 'n', 'senses': [
                {'gloss': 'similarity, similitude', 'hint': 'similarity, ...', 'syns': ['test1', 'Thesaurus:test2']}],
            'noun_type': 'f'}]}]

    print("\n\n")
    print(deck.format_usage(usage))
    assert deck.format_usage(usage) == """\
<div class="etymology etymology_0 solo_etymology">
<span class="pos n f"><span class="pos_tag pos_tag_primary">f</span><span class="gloss">similarity, similitude</span><span class="synonyms">test1, test2</span></span>
<span class="pos n hint f"><span class="pos_tag pos_tag_primary">f</span><span class="gloss">similarity, ...</span><span class="synonyms">test1, test2</span></span>
</div>
<span id="footnote_a" class="footnote ety_footnote general_footnote"><span class="footnote_id">a</span><span class="footnote_data">From Latin &quot;similitūdō&quot; (“likeness, similarity”).</span></span>
"""


def test_demente():

    wordlist_data = """\
_____
demente
pos: adj
  meta: {{es-adj}}
  etymology: Borrowed from Latin "demens, dementem".
  gloss: crazy, insane
    syn: loco; trastornado
  gloss: demented
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = None
    ignore = []
    allforms = AllForms.from_wordlist(wordlist)
    deck = DeckBuilder(wordlist, sentences, ignore, allforms)

    usage = deck.get_usage("demente", "adj")
    print(usage)
    assert usage == [{
        'ety': 'Borrowed from Latin "demens, dementem".',
        'words': [{
            'pos': 'adj',
            'senses': [
                {'gloss': 'crazy, insane', 'syns': ['loco', 'trastornado'], 'hint': ''},
                {'gloss': 'demented', 'hint': '...'}]}]}]

