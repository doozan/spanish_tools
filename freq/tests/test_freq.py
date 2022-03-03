from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms
import pytest
from ...sentences import sentences as spanish_sentences

from ...freq import FrequencyList

sentences = spanish_sentences()

def test_simple():

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


def test_simple2():

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

def test_filters():

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

def test_diva():

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

    assert freq.all_forms.get_lemmas("diva") ==  ['adj|divo', 'n|diva', 'n|divo']
    assert freq.get_preferred_lemmas("diva", "n") == ["divo"]

    flist_data = """\
diva 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,divo,adj,NOSENT,10:diva\
"""


def test_preferred_lemmas():

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

    assert freq.is_primary_lemma(wordlist, "divo", "n") == True
    assert freq.is_primary_lemma(wordlist, "diva", "n") == False

    assert freq.get_preferred_lemmas("diva", "n") == ["divo"]

    flist_data = """\
diva 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,divo,n,NOSENT,10:diva\
"""


def test_hijo():

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

    assert freq.all_forms.get_lemmas("hijo") == ['n|hijo']
    assert freq.get_preferred_lemmas("hijo", "n") == ["hijo"]

    flist_data = """\
hijo 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,hijo,n,NOSENT,10:hijo\
"""

def test_asco():

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

    assert freq.all_forms.get_lemmas("asco") == ['n|asca', 'n|asco']
    assert freq.get_preferred_lemmas("asco", "n") == ["asca", "asco"]
#    assert freq.get_best_lemma("asco", ["asca", "asco"], "n") == "asco"

    flist_data = """\
asco 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,asco,n,NOSENT,10:asco\
"""

def test_bienes():

    wordlist_data = """\
bien {n-meta} :: {{es-noun|m|bienes}}
bien {m} :: good (as opposed to evil)
bienes {n-meta} :: {{es-noun|m-p}}
bienes {mp} :: goods (that which is produced, traded, bought or sold)
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    assert freq.all_forms.get_lemmas("bienes") == ['n|bien', 'n|bienes']
    assert freq.get_preferred_lemmas("bienes", "n") == ["bien", "bienes"]
#    assert freq.get_best_lemma("bienes", ["bien", "bienes"], "n") == "bienes"

    flist_data = """\
bienes 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,bienes,n,NOSENT,10:bienes\
"""

def test_rasguno():

    wordlist_data = """\
rasguñar {v-meta} :: {{es-verb}} {{es-conj}}
rasguñar {vt} | arañar; rascar :: to scratch
rasguño {n-meta} :: {{es-noun}}
rasguño {m} | arañazo :: scratch
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    assert freq.all_forms.get_lemmas("rasguño") == ['n|rasguño', 'v|rasguñar']
    assert freq.get_ranked_pos("rasguño") == ["n", "v"]

    flist_data = """\
rasguño 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,rasguño,n,NOSENT,10:rasguño\
"""

def test_dios():

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


    assert freq.is_primary_lemma(wordlist, "dios", "n") == True
    assert freq.is_primary_lemma(wordlist, "diosa", "n") == False

    assert freq.get_preferred_lemmas("dioses", "n") == ["dios"]

    print(list(allforms.all))
    assert freq.all_forms.get_lemmas("diosas", "n") ==  ['n|dios', 'n|diosa']
    assert freq.get_preferred_lemmas("diosas", "n") == ["dios"]
    assert freq.get_preferred_lemmas("diosa", "n") == ["dios"]

#    assert freq.get_best_lemma("diosa", ["dios", "diosa"], "n") == "dios"

#    assert list(freq.all_forms.get_lemmas("dios", {})) == ['n:dios:m']
#    assert list(freq.all_forms.get_lemmas("dioses", {})) == ['n:dios:pl']
#    assert list(freq.all_forms.get_lemmas("diosa", {})) == ["n:dios:f"]
#    assert list(freq.all_forms.get_lemmas("diosas", {})) == ["n:diosa:pl"]

    flist_data = """\
dios 10
dioses 10
diosa 10
diosas 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
40,dios,n,NOSENT,10:dios|10:dioses|10:diosa|10:diosas\
"""


def test_aquellos():

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


def test_vete():

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

def test_veros():

    wordlist_data = """\
ver {v-meta} :: {{es-verb}} {{es-conj}}
ver {v} :: x
vero {n-meta} :: {{es-noun|m}}
vero {m} [heraldry] :: vair
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    assert freq.get_ranked_pos("veros") == ["v", "n"]

def test_veras():

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
    assert freq.get_best_lemma("veras", ["vera", "veras"], "n") == "veras"

def test_microondas():

    wordlist_data = """\
microonda {n-meta} :: {{es-noun|f}}
microonda {n-forms} :: pl=microondas
microonda {f} :: microwave (electromagnetic wave)
microondas {n-meta} :: {{es-noun|m|microondas}}
microondas {n-forms} :: pl=microondas
microondas {m} | horno de microondas :: microwave oven, microwave
microondas {m} :: necklacing (execution by burning tyre)
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    lemmas = ["microonda", "microondas"]
    assert freq.get_preferred_lemmas("microondas", "n") == lemmas
    assert freq.get_best_lemma("microondas", lemmas, "n") == "microondas"

def test_hamburguesa():
    wordlist_data = """\
hamburgués {n-meta} :: {{es-noun|m|hamburgueses|f=hamburguesa|fpl=hamburguesas}}
hamburgués {n-forms} :: f=hamburguesa; fpl=hamburguesas; pl=hamburgueses
hamburgués {m} :: Hamburger, a person from Hamburg
hamburguesa {n-meta} :: {{es-noun|f}}
hamburguesa {n-forms} :: pl=hamburguesas
hamburguesa {f} :: hamburger
hamburguesa {f} :: female equivalent of "hamburgués"; Hamburger
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    lemmas = ['hamburguesa', 'hamburgués']
    assert freq.get_preferred_lemmas("hamburguesa", "n") == lemmas
    assert freq.get_best_lemma("hamburguesa", lemmas, "n") == "hamburguesa"


def test_piernas():
    wordlist_data = """\
pierna {n-meta} :: {{es-noun|f}}
pierna {n-forms} :: pl=piernas
pierna {f} | pata :: leg (lower limb of a human)
piernas {n-meta} :: {{es-noun|m|piernas}}
piernas {n-forms} :: pl=piernas
piernas {m} [dated] :: twit; idiot
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences, [], None)

    assert freq.get_preferred_lemmas("piernas", "n") == ['pierna']
   # assert freq.get_best_lemma("piernas", lemmas, "n") == "pierna"



def test_izquierdas():
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

    print(allforms.all_forms)

    assert freq.get_preferred_lemmas("izquierdas", "n") == ["izquierda"]
    assert freq.get_preferred_lemmas("izquierdo", "adj") == ["izquierdo"]
    assert freq.get_preferred_lemmas("izquierdos", "adj") == ["izquierdo"]
    assert freq.get_preferred_lemmas("izquierdas", "adj") == ["izquierdo"]
    assert freq.get_ranked_pos("izquierda") == ['n', 'adj']
    assert freq.get_ranked_pos("izquierdas") == ['n', 'adj']

    flist_data = """\
izquierda 34629
izquierdo 8150
izquierdas 436
izquierdos 234
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
35065,izquierda,n,NOSENT,34629:izquierda|436:izquierdas
8384,izquierdo,adj,NOSENT,8150:izquierdo|234:izquierdos\
"""
