import os
import pytest
from pytest import fixture


from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms
from ..sentences import SpanishSentences

from ..freq import FrequencyList


@fixture
def sentences(request):
    filename = request.module.__file__
    test_dir, _ = os.path.split(filename)

    sentences = SpanishSentences(sentences="test_sentences.tsv", data_dir=test_dir)
    return sentences



def test_simple(sentences):

    wordlist_data = """\
_____
protector
pos: n
  meta: {{es-noun|m|f=+|f2=protectriz}}
  g: m
  gloss: protector (someone who protects or guards)
pos: n
  meta: {{es-noun|m}}
  g: m
  gloss: protector (a device or mechanism which is designed to protect)
_____
protectora
pos: n
  meta: {{es-noun|f|m=protector}}
  forms: m=protector; mpl=protectores; pl=protectoras
  g: f
  gloss: female equivalent of "protector"
pos: n
  meta: {{es-noun|f}}
  forms: pl=protectoras
  g: f
  gloss: animal shelter (an organization that provides temporary homes for stray pet animals)
    syn: protectora de animales
_____
protectriz
pos: n
  meta: {{es-noun|f|m=protector}}
  forms: m=protector; mpl=protectores; pl=protectrices
  g: f
  gloss: alternative form of "protectora"
    q: uncommon
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

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

#    assert freq.wordlist.has_lemma("protectora", "n") == False


    assert freq.get_resolved_poslemmas("protectores", "n") == ["n|protector"]
    assert freq.get_resolved_poslemmas("protectoras", "n") == ["n|protector"]
    assert freq.get_resolved_poslemmas("protectora", "n") == ["n|protector"]
    assert freq.get_resolved_poslemmas("notaword", "n") == []

    assert freq.get_preferred_lemmas("protectores", "n") == ["protector"]
    assert freq.get_preferred_lemmas("protectoras", "n") == ["protector"]
    assert freq.get_preferred_lemmas("protectora", "n") == ["protector"]
    assert freq.get_preferred_lemmas("notaword", "n") == []

    assert freq.get_ranked_pos("protectoras") == ["n"]

    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
60,protector,n,NOSENT,10:protector|10:protectora|10:protectoras|10:protectores|10:protectriz|10:protectrices
10,unknown,none,NOUSAGE; NODEF; NOSENT,10:unknown\
"""


def test_simple2(sentences):

    wordlist_data = """\
rojo {adj-meta} :: {{es-adj|f=roja}}
rojo {adj} :: red (colour)
rojo {n-meta} :: {{es-noun|m}}
rojo {m} :: red (colour)
rojo {m} [Costa Rica] :: a 1000 colón bill
rojo {m} [Spain, derogatory] :: a left-wing, especially communist
roja {n-meta} :: {{es-noun|f|m=rojo}}
roja {f} :: Red (Communist)
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    assert freq.get_ranked_pos("roja") == ["adj"]

def test_filters(sentences):

    wordlist_data = """\
test {n-meta} :: x
test {m} :: test
test {adj-meta} :: x
test {adj} :: obsolete form of "test"
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

#    assert freq.filter_pos("test", ["n", "adj"]) == ["n"]
    assert freq.get_ranked_pos("test") == ["n"]

def test_diva(sentences):

    wordlist_data = """\
_____
diva
pos: adj
  meta: {{head|es|adjective form}}
  gloss: adjective form of "divo"
pos: n
  meta: {{es-noun|f|m=divo}}
  g: f
  gloss: diva
_____
divo
pos: adj
  meta: {{es-adj}}
  gloss: star (famous)
pos: n
  meta: {{es-noun|m|f=diva}}
  g: m
  gloss: star, celeb
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    flist_data = """\
diva 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,divo,adj,NOSENT,10:diva\
"""


def test_preferred_lemmas(sentences):

    wordlist_data = """\
_____
diva
pos: n
  meta: {{es-noun|f}}
  g: f
  gloss: female equivalent of "divo"
_____
divo
pos: n
  meta: {{es-noun|m|f=diva}}
  g: m
  gloss: star, celeb
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

#    assert freq.is_primary_lemma(wordlist, "divo", "n") == True
#    assert freq.is_primary_lemma(wordlist, "diva", "n") == False

    assert freq.get_preferred_lemmas("diva", "n") == ["divo"]

    flist_data = """\
diva 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,divo,n,NOSENT,10:diva\
"""


def test_hijo(sentences):

    wordlist_data = """\
hija {n-meta} :: x
hija {n-forms} :: m=hijo; mpl=hijos; pl=hijas
hija {f} :: daughter; feminine noun of "hijo"
hijo {n-meta} :: x
hijo {n-forms} :: f=hija; fpl=hijas; pl=hijos
hijo {m} :: son
hijo {m} :: child (when the gender of the child is unknown)
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

#    assert freq.allforms.get_lemmas("hijo") == ['n|hijo']
#    assert freq.get_preferred_lemmas("hijo", "n") == ["hijo"]

    flist_data = """\
hijo 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,hijo,n,,10:hijo\
"""

def test_asco(sentences):

    wordlist_data = """\
asca {n-meta} :: x
asca {n-forms} :: pl=ascas
asca {m} [mycology] | teca :: ascus
asco {n-meta} :: x
asco {n-forms} :: pl=ascos
asco {m} :: disgust
asco {m} :: nausea
asco {n-meta} :: x
asco {n-forms} :: pl=ascos
asco {m} :: alternative form of "asca"
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

#    assert freq.allforms.get_lemmas("asco") == ['n|asca', 'n|asco']
#    assert freq.get_preferred_lemmas("asco", "n") == ["asca", "asco"]
#    assert freq.get_best_lemma("asco", ["asca", "asco"], "n") == "asco"

    flist_data = """\
asco 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,asco,n,,10:asco\
"""

def test_bienes(sentences):

    wordlist_data = """\
bien {n-meta} :: {{es-noun|m|bienes}}
bien {m} :: good (as opposed to evil)
bienes {n-meta} :: {{es-noun|m-p}}
bienes {mp} :: goods (that which is produced, traded, bought or sold)
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    assert freq.allforms.get_lemmas("bienes") == ['n|bien', 'n|bienes']
    assert freq.get_preferred_lemmas("bienes", "n") == ["bien", "bienes"]
#    assert freq.get_best_lemma("bienes", ["bien", "bienes"], "n") == "bienes"

    flist_data = """\
bienes 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,bienes,n,NOSENT,10:bienes\
"""

def test_rasguno(sentences):

    wordlist_data = """\
rasguñar {v-meta} :: {{es-verb}} {{es-conj}}
rasguñar {vt} | arañar; rascar :: to scratch
rasguño {n-meta} :: {{es-noun}}
rasguño {m} | arañazo :: scratch
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    assert freq.allforms.get_lemmas("rasguño") == ['n|rasguño', 'v|rasguñar']
    assert freq.get_ranked_pos("rasguño") == ["n", "v"]

    flist_data = """\
rasguño 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,rasguño,n,NOSENT,10:rasguño\
"""

def test_dios(sentences):

    wordlist_data = """\
_____
dios
pos: n
  meta: {{es-noun|m|dioses|f=diosa}}
  g: m
  gloss: god
_____
diosa
pos: n
  meta: {{es-noun|f|m=dios}}
  g: f
  gloss: goddess
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)



    assert freq.get_resolved_poslemmas("dios", "n") == ["n|dios"]
    assert freq.get_resolved_poslemmas("diosa", "n") == ["n|dios"]

    assert freq.get_preferred_lemmas("dioses", "n") == ["dios"]

#    print(list(allforms.all))
    assert freq.allforms.get_lemmas("diosas", "n") ==  ['n|dios', 'n|diosa']
    assert freq.get_preferred_lemmas("diosas", "n") == ["dios"]
    assert freq.get_preferred_lemmas("diosa", "n") == ["dios"]

#    assert freq.get_best_lemma("diosa", ["dios", "diosa"], "n") == "dios"

#    assert list(freq.allforms.get_lemmas("dios", {})) == ['n:dios:m']
#    assert list(freq.allforms.get_lemmas("dioses", {})) == ['n:dios:pl']
#    assert list(freq.allforms.get_lemmas("diosa", {})) == ["n:dios:f"]
#    assert list(freq.allforms.get_lemmas("diosas", {})) == ["n:diosa:pl"]

    flist_data = """\
dios 10
dioses 10
diosa 10
diosas 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
40,dios,n,LITERAL,10:dios|10:dioses|10:diosa|10:diosas\
"""


def test_aquellos(sentences):

    wordlist_data = """\
aquél {pron-meta} :: {{head|es|pronoun|demonstrative, feminine|aquélla|neuter|aquello|masculine plural|aquéllos|feminine plural|aquéllas|g=m}}
aquél {pron-forms} :: demonstrative_feminine=aquélla; feminine_plural=aquéllas; masculine_plural=aquéllos; neuter=aquello
aquél {pron} [demonstrative] :: that one (far from speaker and listener)
aquéllos {pron-meta} :: {{head|es|pronoun|demonstrative|g=m-p}}
aquéllos {pron} :: plural of "aquél"; those ones (far from speaker and listener)
aquel {pron-meta} :: {{head|es|pronoun|g=m|feminine|aquella|neutrum|aquello|masculine plural|aquellos|neutrum plural|aquellos|feminine plural|aquellas}}
aquel {pron-forms} :: feminine=aquella; feminine_plural=aquellas; masculine_plural=aquellos; neutrum=aquello; neutrum_plural=aquellos
aquel {pron} [demonstrative] :: alternative spelling of "aquél"
aquellos {pron-meta} :: {{head|es|pronoun|demonstrative|g=m-p}}
aquellos {pron} :: alternative spelling of "aquéllos"; those ones (over there; implying some distance). The unaccented form can function as a pronoun if it can be unambiguously deduced as such from context.
aquellos {pron-meta} :: {{head|es|pronoun|g=n-p}}
aquellos {pron} :: Those ones. (over there; implying some distance)
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    assert freq.get_preferred_lemmas("aquellos", "pron") == ['aquél']

#    assert freq.get_best_lemma("aquellos", ['aquellos', 'aquél'], "pron") == "aquél"

    flist_data = """\
aquellos 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,aquél,pron,PRONOUN; NOSENT,10:aquellos\
"""


def test_vete(sentences):

    wordlist_data = """\
ir {v-meta} :: {{es-verb}} {{es-conj}} {{es-conj|irse}}
ir {v} :: x
ver {v-meta} :: {{es-verb}} {{es-conj}}
ver {v} :: x
verse {v-meta} :: {{es-verb}} {{es-conj}}
verse {v} :: x
vetar {v-meta} :: {{es-verb}} {{es-conj}}
vetar {v} :: x
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    assert freq.get_preferred_lemmas("vete", "v") == ['ir', 'ver', 'verse', 'vetar']

    assert freq.get_best_lemma({}, "vete", ['ir', 'ver', 'verse', 'vetar'], "v") == "ir"

def test_veros(sentences):

    wordlist_data = """\
ver {v-meta} :: {{es-verb}} {{es-conj}}
ver {v} :: x
vero {n-meta} :: {{es-noun|m}}
vero {m} [heraldry] :: vair
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    assert freq.get_ranked_pos("veros") == ["v"]

    flist_data = """\
veros 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,ver,v,,10:veros\
"""

def test_veras(sentences):

    wordlist_data = """\
vera {n-meta} :: {{es-noun|f}}
vera {n-forms} :: pl=veras
vera {f} [poetic] | lado :: side, face
vera {n-meta} :: {{es-noun|f}}
vera {n-forms} :: pl=veras
vera {f} :: verawood (Bulnesia arborea)
veras {n-meta} :: {{es-noun|f-p}}
veras {fp} :: truth; reality
veras {fp} :: serious things
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    assert freq.get_preferred_lemmas("veras", "n") == ["vera", "veras"]
#    assert freq.get_best_lemma("veras", ["vera", "veras"], "n") == "veras"

    flist_data = """\
veras 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,veras,n,,10:veras\
"""

def test_microondas(sentences):

    wordlist_data = """\
_____
microonda
pos: n
  meta: {{es-noun|f}}
  g: f
  etymology: Translation of English microwave; micro- + onda ("wave"). The plural, microondas, is also an independent masculine noun meaning "microwave".
  gloss: microwave (electromagnetic wave)
_____
microondas
pos: n
  meta: {{es-noun|m}}
  g: m
  etymology: Originally the plural of microonda; now also an independent masculine noun. See microonda.
  gloss: microwave oven, microwave
    syn: horno de microondas
  gloss: necklacing (execution by burning tyre)
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    lemmas = ["microonda", "microondas"]
    assert freq.get_preferred_lemmas("microondas", "n") == lemmas
#    assert freq.get_best_lemma("microondas", lemmas, "n") == "microondas"

    flist_data = """\
microondas 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,microondas,n,NOSENT,10:microondas\
"""




def test_hamburguesa(sentences):
    wordlist_data = """\
_____
hamburguesa
pos: n
  meta: {{es-noun|f}}
  g: f
  gloss: hamburger
pos: n
  meta: {{es-noun|f}}
  g: f
  gloss: female equivalent of "hamburgués"; Hamburger
_____
hamburgués
pos: adj
  meta: {{es-adj}}
  etymology: Hamburgo + -és.
  gloss: of Hamburg; Hamburger
    q: relational
pos: n
  meta: {{es-noun|m|f=+}}
  g: m
  etymology: Hamburgo + -és.
  gloss: Hamburger, a person from Hamburg
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    lemmas = ['hamburguesa', 'hamburgués']
    assert freq.get_preferred_lemmas("hamburguesa", "n") == lemmas
#    assert freq.get_best_lemma("hamburguesa", lemmas, "n") == "hamburguesa"

    flist_data = """\
hamburgués 10
hamburguesa 10
hamburguesas 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
20,hamburguesa,n,,10:hamburguesa|10:hamburguesas
10,hamburgués,n,,10:hamburgués\
"""

def test_piernas(sentences):
    wordlist_data = """\
_____
pierna
pos: n
  meta: {{es-noun|f}}
  g: f
  etymology: From Latin "perna". Compare Portuguese "perna".
  gloss: leg (lower limb of a human)
    syn: pata
_____
piernas
pos: n
  meta: {{head|es|noun form|g=f-p}}
  g: f-p
  gloss: plural of "pierna"
pos: n
  meta: {{es-noun|m}}
  g: m
  gloss: twit; idiot
    q: dated
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    assert freq.get_preferred_lemmas("piernas", "n") == ['pierna']
   # assert freq.get_best_lemma("piernas", lemmas, "n") == "pierna"

    flist_data = """\
pierna 10
piernas 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
20,pierna,n,,10:pierna|10:piernas\
"""


def test_izquierdas(sentences):
    wordlist_data = """\
_____
izquierda
pos: adj
  meta: {{head|es|adjective form|g=f-s}}
  g: f-s
  gloss: adjective form of "izquierdo"
pos: n
  meta: {{es-noun|f|-}}
  g: f
  gloss: left (side, direction)
  gloss: left
    q: politics
_____
izquierdas
pos: adj
  meta: {{head|es|adjective form}}
  gloss: adjective form of "izquierdo"
pos: n
  meta: {{head|es|noun form|g=f-p}}
  g: f-p
  gloss: plural of "izquierda"
_____
izquierdo
pos: adj
  meta: {{es-adj}}
  gloss: left; on the left side or toward the left; the opposite of right
    syn: siniestro
  gloss: left-handed
  gloss: crooked
_____
izquierdos
pos: adj
  meta: {{head|es|adjective form|g=m-p}}
  g: m-p
  gloss: plural of "izquierdo"
_____
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    assert freq.get_preferred_lemmas("izquierdas", "n") == ["izquierda"]
    assert freq.get_preferred_lemmas("izquierdo", "adj") == ["izquierdo"]
    assert freq.get_preferred_lemmas("izquierdos", "adj") == ["izquierdo"]
    assert freq.get_preferred_lemmas("izquierdas", "adj") == ["izquierdo"]
#    assert freq.get_ranked_pos("izquierda") == ['n', 'adj']
#    assert freq.get_ranked_pos("izquierdas") == ['n', 'adj']

    flist_data = """\
izquierda 34629
izquierdo 8150
izquierdas 436
izquierdos 234
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
35065,izquierda,n,,34629:izquierda|436:izquierdas
8384,izquierdo,adj,NOSENT,8150:izquierdo|234:izquierdos\
"""


def test_get_resolved_poslemmas(sentences):
    data="""\
_____
test1
pos: n
  g: m
  gloss: test
_____
test2
pos: n
  gloss: alternate form of "test1"
_____
test3
pos: n
  gloss: alternate form of "test2"
_____
test4
pos: n
  gloss: misspelling of "test3"
_____
test5
pos: n
  gloss: alternative form of "test6"
_____
test6
pos: n
  gloss: alternative form of "test5"
_____
test7
pos: n
  gloss: alternative form of "test-none"
_____
test8
pos: n
  gloss: alternative form of "test4"
_____
test9
pos: n
  gloss: alternative form of "test8"
"""

    wordlist = Wordlist(data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)


    assert freq.get_resolved_poslemmas("test1", "n") == ["n|test1"]
    assert freq.get_resolved_poslemmas("test2", "n") == ["n|test1"]
    assert freq.get_resolved_poslemmas("test3", "n") == ["n|test1"]
    assert freq.get_resolved_poslemmas("test4", "n") == ["n|test1"]
    assert freq.get_resolved_poslemmas("test5", "n") == []
    assert freq.get_resolved_poslemmas("test6", "n") == []
    assert freq.get_resolved_poslemmas("test7", "n") == []
    assert freq.get_resolved_poslemmas("test8", "n") == ['n|test1']
    assert freq.get_resolved_poslemmas("test9", "n") == []
    assert freq.get_resolved_poslemmas("test9", "n", max_depth=4) == ['n|test1']



def test_alt_of_form(sentences):

    # test resolving a misspelled, missing, form
    # paises -> países -> país

    data="""\
_____
país
pos: n
  meta: {{es-noun|m|países}}
  g: m
  etymology: Borrowed from French "pays", from Old French "païs", from Malayalam "pagensis", from Latin "pāgus" (“country”). Compare Sicilian "pajisi", Italian "paese".
  gloss: country (the territory of a nation)
  gloss: country, land (a set region of land having particular human occupation or agreed limits)
_____
paises
pos: n
  meta: {{head|es|misspelling}}
  gloss: misspelling of "países"
"""

    wordlist = Wordlist(data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)

    print("\n".join(allforms.all_csv))
    assert "\n".join(allforms.all_csv) == """\
paises,n,países
país,n,país
países,n,país\
"""


    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    flist_data = """\
país 10
países 10
paises 10
"""

    print("\n".join(freq.process(flist_data.splitlines())))

    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
30,país,n,,10:país|10:países|10:paises\
"""


def test_rare_lemma(sentences):

    # rare lemmas should be ignored
    # ratas -> rata not rato

    data="""\
_____
rata
pos: n
  meta: {{es-noun|f|m=rato}}
  g: f
  etymology: From VL "rattus" (“rat”), of gem origin. It is not known how the noun made the jump to a feminine noun.
  gloss: rat (a medium-sized rodent belonging to the genus Rattus)
_____
ratas
pos: n
  meta: {{head|es|noun form|g=f-p}}
  g: f-p
  gloss: plural of "rata"
_____
rato
pos: n
  meta: {{es-noun|m}}
  g: m
  etymology: From Latin "raptus".
  gloss: a while, bit (a short period of time)
  gloss: time
pos: n
  meta: {{es-noun|m|f=rata}}
  g: m
  etymology: From rata, this from Proto-Germanic "*rattaz".
  gloss: male rat
    q: archaic
_____
ratos
pos: n
  meta: {{head|es|noun form|g=m-p}}
  g: m-p
  gloss: plural of "rato"
"""

    wordlist = Wordlist(data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)

    print("\n".join(allforms.all_csv))
    assert "\n".join(allforms.all_csv) == """\
rata,n,rata,rato
ratas,n,rata,rato
rato,n,rato
ratos,n,rato\
"""

    freq = FrequencyList(wordlist, allforms, sentences, [], None, debug_word="ratos")

    rata = next(wordlist.get_words("rata", "n"))
    rato1 = list(wordlist.get_words("rato", "n"))[0]
    rato2 = list(wordlist.get_words("rato", "n"))[1]

    assert freq.is_lemma(rata) == True
    assert freq.is_lemma(rato1) == True
    # Archaic words aren't lemmas
    assert freq.is_lemma(rato2) == False

    assert freq.get_preferred_lemmas("ratas") == [rata]

    flist_data = """\
rata 10
ratas 15
rato 20
ratos 20
"""

    res = list(freq.process(flist_data.splitlines()))
    print("\n".join(res))

    assert "\n".join(res) == """\
count,spanish,pos,flags,usage
40,rato,n,,20:rato|20:ratos
25,rata,n,,15:ratas|10:rata\
"""



def test_rare_lemma_compact_wordlist(sentences):

    # rare lemmas should be ignored
    # ratas -> rata not rato

    data="""\
_____
rata
pos: n
  meta: {{es-noun|f|m=rato}}
  g: f
  etymology: From VL "rattus" (“rat”), of gem origin. It is not known how the noun made the jump to a feminine noun.
  gloss: rat (a medium-sized rodent belonging to the genus Rattus)
_____
rato
pos: n
  meta: {{es-noun|m}}
  g: m
  etymology: From Latin "raptus".
  gloss: a while, bit (a short period of time)
  gloss: time
pos: n
  meta: {{es-noun|m|f=rata}}
  g: m
  etymology: From rata, this from Proto-Germanic "*rattaz".
  gloss: male rat
    q: archaic
"""

    wordlist = Wordlist(data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)

    print("\n".join(allforms.all_csv))
    assert "\n".join(allforms.all_csv) == """\
rata,n,rata,rato
ratas,n,rata,rato
rato,n,rato
ratos,n,rato\
"""

    freq = FrequencyList(wordlist, allforms, sentences, [], None, debug_word="ratas")

    rata = next(wordlist.get_words("rata", "n"))
    rato1 = list(wordlist.get_words("rato", "n"))[0]
    rato2 = list(wordlist.get_words("rato", "n"))[1]

    assert freq.is_lemma(rata) == True
    assert freq.is_lemma(rato1) == True
    # Archaic words aren't lemmas
    assert freq.is_lemma(rato2) == False

    assert freq.get_preferred_lemmas("ratas") == [rata]

    flist_data = """\
rata 10
ratas 15
rato 20
ratos 20
"""

    res = list(freq.process(flist_data.splitlines()))
    print("\n".join(res))

    assert "\n".join(res) == """\
count,spanish,pos,flags,usage
40,rato,n,,20:rato|20:ratos
25,rata,n,,15:ratas|10:rata\
"""



def test_resolution(sentences):

    wordlist_data = """\
_____
ésto
pos: pron
  meta: {{head|es|misspelling}}
  gloss: misspelling of "esto"
_____
esto
pos: pron
  meta: {{head|es|pronoun form}}
  etymology: From Latin "istud", from iste.
  gloss: singular of "éste"
_____
éste
pos: pron
  meta: {{head|es|pronoun|g=m|demonstrative, feminine|ésta|neuter|esto|masculine plural|éstos|feminine plural|éstas|neuter plural|estos}}
  g: m
  etymology: From Latin "iste".
  gloss: this one
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None, debug_word="ésto")


    w1 = next(wordlist.get_words("ésto", "pron"))
    w2 = next(wordlist.get_words("esto", "pron"))
    w3 = next(wordlist.get_words("éste", "pron"))

    assert freq.get_resolved_lemmas(w3, None, None) == [w3]
    assert freq.get_resolved_lemmas(w2, None, None) == [w3]
    assert freq.get_resolved_lemmas(w1, None, None) == [w3]


def test_roses(sentences):

    # roses should resolve to ros and not (ros, ro)
    # even though ro -> ros, ros -> roses (double plural)

    wordlist_data = """\
_____
ro
pos: n
  meta: {{es-noun|f}}
  g: f
  gloss: rho; the Greek letter Ρ, ρ
    syn: rho
_____
ros
pos: n
  meta: {{es-noun|m}}
  g: m
  etymology: Named after Antonio Ros de Olano, a Spanish general who introduced the hat into the Spanish army
  gloss: A type of military hat, similar to a shako
pos: n
  meta: {{head|es|noun form|g=m-p}}
  g: m-p
  gloss: plural of "ro"
_____
roses
pos: n
  meta: {{head|es|noun form|g=m-p}}
  g: m-p
  gloss: plural of "ros"
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None, debug_word="roses")

    ro = next(wordlist.get_words("ro", "n"))
    ros1 = list(wordlist.get_words("ros", "n"))[0]
    ros2 = list(wordlist.get_words("ros", "n"))[1]
    roses = next(wordlist.get_words("roses", "n"))

    claims = freq.get_claimed_lemmas("roses", "n")
    assert claims == [(ros1, ['pl']), (ros2, ['pl'])]
    filtered = freq.filter_verified_claims("roses", claims)
    assert filtered == [ (ros1, ['pl']) ]

    assert freq.get_declaring_lemmas("roses", "n") == [ros1]

    assert freq.get_preferred_lemmas("roses") == [ros1]
    assert freq.get_resolved_lemmas(roses, None, None) == [ros1]


def test_nos(sentences):

    # roses should resolve to ros and not (ros, ro)
    # even though ro -> ros, ros -> roses (double plural)

    wordlist_data = """\
_____
no
pos: adv
  meta: {{es-adv}}
  gloss: no
pos: n
  meta: {{es-noun|m|noes}}
  g: m
  etymology: From Old Spanish "non", from Latin "nōn" (compare Catalan "no", Galician "non", French "non", Italian "no", Portuguese "não", Romanian "nu").
  gloss: no
pos: n
  meta: {{es-noun|m}}
  g: m
  etymology: Contracted form of Latin "numero", ablative singular of numerus (“number”).
  gloss: abbreviation of "número"; no.
_____
nos
pos: n
  meta: {{head|es|noun form|g=m-p}}
  g: m-p
  gloss: plural of "no"
pos: pron
  meta: {{head|es|pronoun|object pronoun}}
  gloss: inflection of "nosotros": to us, for us
  gloss: inflection of "nosotros": us
  gloss: inflection of "nosotros": ourselves; each other
    q: reflexive
  gloss: first person; I (singular, cf. vos)
    q: archaic, formal
_____
nosotros
pos: pron
  meta: {{head|es|pronoun|g=m-p|feminine plural|nosotras}}
  g: m-p
  gloss: we (masculine plural)
  gloss: inflection of "nosotros"
    q: disjunctive
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None, debug_word="nos")

#    w1 = next(wordlist.get_words("nos", "n"))
    w2 = list(wordlist.get_words("no", "n"))
    w3 = list(wordlist.get_words("nosotros", "pron"))

    assert freq.is_lemma(w3[0]) == True

#    for lemma in freq.get_resolved_lemmas(w2):
#        print(lemma.word, lemma.pos)
#    assert freq.get_resolved_lemmas(w2) == [w1]

    res = freq.get_preferred_lemmas("nos")
    for lemma in res:
        print(lemma.word, lemma.pos)

    assert res == w2 + w3


def test_paises(sentences):

    # paises -> países -> país

    wordlist_data = """\
_____
paises
pos: n
  meta: {{head|es|misspelling}}
  gloss: misspelling of "países"
_____
país
pos: n
  meta: {{es-noun|m|países}}
  g: m
  etymology: Borrowed from French "pays", from Old French "païs", from Malayalam "pagensis", from Latin "pāgus" (“country”). Compare Sicilian "pajisi", Italian "paese".
  gloss: country (the territory of a nation)
  gloss: country, land (a set region of land having particular human occupation or agreed limits)
_____
países
pos: n
  meta: {{head|es|noun form|g=m-p}}
  g: m-p
  gloss: plural of "país"
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None, debug_word="nos")

    assert allforms.get_lemmas("paises") == ['n|países']

    w1 = next(wordlist.get_words("paises", "n"))
    w2 = next(wordlist.get_words("país", "n"))
    w3 = next(wordlist.get_words("países", "n"))

    assert freq.is_lemma(w1) == False
    assert freq.is_lemma(w2) == True
    assert freq.is_lemma(w3) == False

    assert freq.get_preferred_lemmas("paises") == [w2]

def test_paises2(sentences):

    # paises -> países -> país
    # even when países is not included in dictionary

    wordlist_data = """\
_____
paises
pos: n
  meta: {{head|es|misspelling}}
  gloss: misspelling of "países"
_____
país
pos: n
  meta: {{es-noun|m|países}}
  g: m
  etymology: Borrowed from French "pays", from Old French "païs", from Malayalam "pagensis", from Latin "pāgus" (“country”). Compare Sicilian "pajisi", Italian "paese".
  gloss: country (the territory of a nation)
  gloss: country, land (a set region of land having particular human occupation or agreed limits)
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None, debug_word="nos")

    assert allforms.get_lemmas("paises") == ['n|países']

    w1 = next(wordlist.get_words("paises", "n"))
    w2 = next(wordlist.get_words("país", "n"))

    assert freq.is_lemma(w1) == False
    assert freq.is_lemma(w2) == True

    assert freq.get_preferred_lemmas("paises") == [w2]

def test_facto(sentences):

    # facto should resolve to "de facto" even though it changes from particle to adverb

    wordlist_data = """\
_____
de facto
pos: adv
  meta: {{es-adv}}
  gloss: truly
  gloss: indeed
  gloss: in fact
_____
facto
pos: n
  meta: {{head|es|noun}}
  etymology: Borrowed from Latin "factum". Compare the inherited doublet hecho.
  gloss: fact (something which is real)
    q: archaic
pos: particle
  meta: {{head|es|particle}}
  etymology: Borrowed from Latin "factum". Compare the inherited doublet hecho.
  gloss: only used in "de facto"
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None, debug_word="facto")


    w1 = next(wordlist.get_words("facto", "particle"))
    w2 = next(wordlist.get_words("de facto", "adv"))

    assert freq.is_lemma(w1) == False
    assert freq.is_lemma(w2) == True

#    assert freq.get_resolved_lemmas(w1, "facto") == [w2]
    assert freq.get_preferred_lemmas("facto") == [w2]



def test_llantas(sentences):

    # llantas should resolve to llanta and not follow the obsolete
    # llanta to planta

    wordlist_data = """\
_____
llanta
pos: n
  meta: {{es-noun|f}}
  g: f
  gloss: tyre rim, wheelrim
pos: n
  meta: {{es-noun|f}}
  g: f
  gloss: obsolete form of "planta"
_____
llantas
pos: n
  meta: {{head|es|noun form|g=f-p}}
  g: f-p
  gloss: plural of "llanta"
_____
planta
pos: n
  meta: {{es-noun|f}}
  g: f
form lla
  gloss: plant (organism of the kingdom Plantae)
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None, debug_word="llantas")

    w1 = next(wordlist.get_words("llantas", "n"))
    w2 = next(wordlist.get_words("llanta", "n"))

    assert freq.is_lemma(w1) == False
    assert freq.is_lemma(w2) == True

#    assert freq.get_preferred_lemmas("llanta") == [w2]
    assert freq.get_preferred_lemmas("llantas") == [w2]
