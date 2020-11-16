from enwiktionary_wordlist import Wordlist
import spanish_sentences

from freq import FrequencyList

def test_simple():

    wordlist_data = """\
protector {noun-meta} :: x
protector {noun-forms} :: f=protectora; fpl=protectoras; pl=protectores
protector {m} :: protector (someone who protects or guards)
protector {noun-meta} :: x
protector {noun-forms} :: pl=protectores
protector {m} :: protector (a device or mechanism which is designed to protect)
protectora {noun-meta} :: x
protectora {noun-forms} :: m=protector; mpl=protectores; pl=protectoras
protectora {f} :: feminine noun of "protector"
protectora {noun-meta} :: x
protectora {noun-forms} :: pl=protectoras
protectora {f} | protectora de animales :: animal shelter (an organization that provides temporary homes for stray pet animals)
protectriz {noun-meta} :: x
protectriz {noun-forms} :: m=protector; mpl=protectores; pl=protectrices
protectriz {f} [uncommon] :: alternative form of "protectora"
"""

    flist_data = """\
protector 10
protectora 10
protectoras 10
protectores 10
protectriz 10
protectrices 10
unknown 10
"""

    sentences = None
    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = spanish_sentences.sentences()

    freq = FrequencyList(wordlist, sentences)

    assert freq.get_lemmas("protectores", "noun") == ["protector"]
    assert freq.get_lemmas("protectoras", "noun") == ["protector", "protectora"]
    assert freq.get_lemmas("notaword", "noun") == ["notaword"]

    assert freq.get_ranked_pos("protectoras") == ["noun"]

    assert "\n".join(freq.process(flist_data.splitlines(), None)) == """\
count,spanish,pos,flags,usage
60,protector,noun,NOSENT,10:protector|10:protectora|10:protectoras|10:protectores|10:protectrices|10:protectriz
10,unknown,none,NOUSAGE; NODEF; NOSENT; COMMON,10:unknown\
"""


def test_simple2():

    wordlist_data = """\
rojo {adj-meta} :: x
rojo {adj-forms} :: f=roja; fpl=rojas; pl=rojos
rojo {adj} :: red (colour)
rojo {noun-meta} :: x
rojo {noun-forms} :: pl=rojos
rojo {m} :: red (colour)
rojo {m} [Costa Rica] :: a 1000 colón bill
rojo {m} [Spain, derogatory] :: a left-wing, especially communist
roja {noun-meta} :: x
roja {noun-forms} :: m=rojo; mpl=rojos; pl=rojas
roja {f} :: Red (Communist)
"""

    sentences = None
    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = spanish_sentences.sentences()

    freq = FrequencyList(wordlist, sentences)

    assert freq.get_ranked_pos("roja") == ["adj", "noun"]

def test_filters():

    wordlist_data = """\
test {noun-meta} :: x
test {m} :: test
test {adj-meta} :: x
test {adj} :: obsolete form of "test"
"""

    sentences = None
    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = spanish_sentences.sentences()

    freq = FrequencyList(wordlist, sentences)

    assert freq.filter_pos("test", ["noun", "adj"]) == ["noun"]
    assert freq.get_ranked_pos("test") == ["noun"]

def test_lemma_filters():

    wordlist_data = """\
ir {verb-meta} :: x
ir {verb-forms} :: 1=irse; 1=ir; 10=va; 11=vamos
ir {vi} :: to go (away from speaker and listener)
ir {vi} :: to come (towards or with the listener)
ir {v} [auxiliary] :: to be going to (near future), to go (+ a + infinitive)
ir {vr} :: to go away, to leave, to be off (see irse)
irse {verb-meta} :: x
irse {verb-forms} :: 1=irse; 10=va; 11=vamos
irse {v} | andarse; marcharse :: to go away, to leave, to depart, to go (when the destination is not essential; when something or someone is going somewhere else)
irse {v} :: to leak out (with liquids and gasses), to boil away, to go flat (gas in drinks)
"""

    sentences = None
    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = spanish_sentences.sentences()

    freq = FrequencyList(wordlist, sentences)

    assert list(freq.wordlist.all_forms.get("vamos", {}).keys()) == ["verb"]
    assert freq.get_lemmas("vamos", "verb") == ["ir"]
    assert freq.get_lemmas("ir", "verb") == ["ir"]


    assert freq.include_word("vamos", "verb") == True
    assert freq.filter_pos("vamos", ["verb"]) == ["verb"]
#    assert len(freq.wordlist.get_words("vamos", "verb")) > 0
    assert freq.get_ranked_pos("vamos") == ["verb"]
    assert freq.get_lemmas("vamos", "verb") == ["ir"]

    flist_data = """\
vamos 10
va 10
"""
    assert "\n".join(freq.process(flist_data.splitlines(), None)) == """\
count,spanish,pos,flags,usage
20,ir,verb,CLEAR,10:vamos|10:va\
"""


def test_diva():

    wordlist_data = """\
diva {noun-meta} :: x
diva {noun-forms} :: m=divo; mpl=divos; pl=divas
diva {f} :: diva
divo {adj-meta} :: x
divo {adj-forms} :: f=diva; fpl=divas; pl=divos
divo {adj} :: star (famous)
divo {noun-meta} :: x
divo {noun-forms} :: f=diva; fpl=divas; pl=divos
divo {m} :: star, celeb\
"""

    sentences = None
    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = spanish_sentences.sentences()

    freq = FrequencyList(wordlist, sentences)

    assert list(freq.wordlist.all_forms.get("diva", {}).keys()) == ["noun", "adj"]
    assert freq.get_lemmas("diva", "noun") == ["divo"]

    flist_data = """\
diva 10
"""
    assert "\n".join(freq.process(flist_data.splitlines(), None)) == """\
count,spanish,pos,flags,usage
10,divo,noun,NOSENT,10:diva\
"""


def test_hijo():

    wordlist_data = """\
hija {noun-meta} :: x
hija {noun-forms} :: m=hijo; mpl=hijos; pl=hijas
hija {f} :: daughter; feminine noun of "hijo"
hijo {noun-meta} :: x
hijo {noun-forms} :: f=hija; fpl=hijas; pl=hijos
hijo {m} :: son
hijo {m} :: child (when the gender of the child is unknown)
"""

    sentences = None
    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = spanish_sentences.sentences()

    freq = FrequencyList(wordlist, sentences)

    assert list(freq.wordlist.all_forms.get("hijo", {}).keys()) == ["noun"]
    assert freq.get_lemmas("hijo", "noun") == ["hijo"]

    flist_data = """\
hijo 10
"""
    assert "\n".join(freq.process(flist_data.splitlines(), None)) == """\
count,spanish,pos,flags,usage
10,hijo,noun,CLEAR,10:hijo\
"""

def test_asco():

    wordlist_data = """\
asca {noun-meta} :: x
asca {noun-forms} :: pl=ascas
asca {m} [mycology] | teca :: ascus
asco {noun-meta} :: x
asco {noun-forms} :: pl=ascos
asco {m} :: disgust
asco {m} :: nausea
asco {noun-meta} :: x
asco {noun-forms} :: pl=ascos
asco {m} :: alternative form of "asca"
"""

    sentences = None
    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = spanish_sentences.sentences()

    freq = FrequencyList(wordlist, sentences)

    assert list(freq.wordlist.all_forms.get("asco", {}).keys()) == ["noun"]
    assert freq.get_lemmas("asco", "noun") == ["asca", "asco"]
    assert freq.get_best_lemma("asco", ["asca", "asco"], "noun") == "asco"

    flist_data = """\
asco 10
"""
    assert "\n".join(freq.process(flist_data.splitlines(), None)) == """\
count,spanish,pos,flags,usage
10,asco,noun,CLEAR,10:asco\
"""

def test_bienes():

    wordlist_data = """\
bien {noun-meta} :: x
bien {noun-forms} :: pl=bienes
bien {m} :: good (as opposed to evil)
bienes {noun-meta} :: x
bienes {mp} :: goods (that which is produced, traded, bought or sold)
"""

    sentences = None
    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = spanish_sentences.sentences()

    freq = FrequencyList(wordlist, sentences)

    assert list(freq.wordlist.all_forms.get("bienes", {}).keys()) == ["noun"]
    assert freq.get_lemmas("bienes", "noun") == ["bien", "bienes"]
    assert freq.get_best_lemma("bienes", ["bien", "bienes"], "noun") == "bienes"

    flist_data = """\
bienes 10
"""
    assert "\n".join(freq.process(flist_data.splitlines(), None)) == """\
count,spanish,pos,flags,usage
10,bienes,noun,LITERAL; CLEAR,10:bienes\
"""

def test_rasguno():

    wordlist_data = """\
rasguñar {verb-meta} :: x
rasguñar {verb-forms} :: 7=rasguño
rasguñar {vt} | arañar; rascar :: to scratch
rasguño {noun-meta} :: x
rasguño {noun-forms} :: pl=rasguños
rasguño {m} | arañazo :: scratch
"""

    sentences = None
    wordlist = Wordlist(wordlist_data.splitlines())
    sentences = spanish_sentences.sentences()

    freq = FrequencyList(wordlist, sentences)

    assert list(freq.wordlist.all_forms.get("rasguño", {}).keys()) == ["verb", "noun"]
    assert freq.get_ranked_pos("rasguño") == ["verb", "noun"]

    flist_data = """\
rasguño 10
"""
    assert "\n".join(freq.process(flist_data.splitlines(), None)) == """\
count,spanish,pos,flags,usage
10,rasguñar,verb,CLEAR,10:rasguño\
"""
