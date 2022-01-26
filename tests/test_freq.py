from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms
import pytest
from ..spanish_sentences import sentences as spanish_sentences

from ..freq import FrequencyList

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
protectoras
pos: n
  meta: {{head|es|noun plural form|g=f-p}}
  g: f-p
  gloss: inflection of "protector"
_____
protectores
pos: n
  meta: {{head|es|noun plural form|g=m-p}}
  g: m-p
  gloss: inflection of "protector"
_____
protectrices
pos: n
  meta: {{head|es|noun plural form|g=f-p}}
  g: f-p
  gloss: inflection of "protector"
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
    freq = FrequencyList(wordlist, allforms, sentences, [], "probabilitats.dat")

#    assert freq.wordlist.has_lemma("protectora", "n") == False

    assert freq.get_lemmas("protectores", "n") == ["protector"]
    assert freq.get_lemmas("protectoras", "n") == ["protector", "protectora"]
    assert freq.get_lemmas("notaword", "n") == ["notaword"]

    assert freq.get_ranked_pos("protectoras") == ["n"]

    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
60,protector,n,LITERAL,10:protector|10:protectores|10:protectriz|10:protectrices|10:protectora|10:protectoras
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
    freq = FrequencyList(wordlist, allforms, sentences)

    assert freq.get_ranked_pos("roja") == ["adj", "n"]

def test_filters():

    wordlist_data = """\
test {n-meta} :: x
test {m} :: test
test {adj-meta} :: x
test {adj} :: obsolete form of "test"
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences)

    assert freq.filter_pos("test", ["n", "adj"]) == ["n"]
    assert freq.get_ranked_pos("test") == ["n"]

def test_lemma_filters():

    wordlist_data = """\
_____
ir
pos: v
  meta: {{es-verb}} {{es-conj}} {{es-conj|irse}}
  gloss: to go (away from speaker and listener)
    q: intransitive
  gloss: to come (towards or with the listener)
    q: intransitive
  gloss: to be going to (near future), to go (+ a + infinitive)
    q: auxiliary
  gloss: to go away, to leave, to be off (see irse)
    q: reflexive
_____
irse
pos: v
  meta: {{es-verb}} {{es-conj}}
  gloss: to go away, to leave, to depart, to go (when the destination is not essential; when something or someone is going somewhere else)
    syn: andarse; marcharse
  gloss: to leak out (with liquids and gasses), to boil away, to go flat (gas in drinks)
  gloss: to overflow
  gloss: to go out (lights)
  gloss: to finish, to wear out, to disappear (e.g. money, paint, pains, mechanical parts)
  gloss: to die
  gloss: to break wind, to fart
    q: informal
  gloss: to wet/soil oneself (i.e., urinate or defecate in one's pants)
    q: informal
  gloss: to come, to cum, to ejaculate, to orgasm
    q: vulgar
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences)

    print(allforms.all_forms["nos vamos"])

    assert freq.all_forms.get_lemmas("vamos") == ['v|ir']
    assert freq.all_forms.get_lemmas("nos vamos") == ['v|ir', 'v|irse']
    assert freq.get_lemmas("vamos", "v") == ["ir"]
    assert freq.get_lemmas("ir", "v") == ["ir"]

    assert freq.include_word("vamos", "v") == True
    assert freq.filter_pos("vamos", ["v"]) == ["v"]
#    assert len(freq.wordlist.get_words("vamos", "v")) > 0
    assert freq.get_ranked_pos("vamos") == ["v"]
    assert freq.get_lemmas("vamos", "v") == ["ir"]

    flist_data = """\
vamos 10
va 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
20,ir,v,,10:vamos|10:va\
"""


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
    freq = FrequencyList(wordlist, allforms, sentences)

    assert freq.all_forms.get_lemmas("diva") ==  ['adj|divo', 'n|divo']
    assert freq.get_lemmas("diva", "n") == ["divo"]

    flist_data = """\
diva 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,divo,adj,NOSENT,10:diva\
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
    freq = FrequencyList(wordlist, allforms, sentences)

    assert freq.all_forms.get_lemmas("hijo") == ['n|hijo']
    assert freq.get_lemmas("hijo", "n") == ["hijo"]

    flist_data = """\
hijo 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,hijo,n,,10:hijo\
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
    freq = FrequencyList(wordlist, allforms, sentences)

    assert freq.all_forms.get_lemmas("asco") == ['n|asco', 'n|asca']
    assert freq.get_lemmas("asco", "n") == ["asca", "asco"]
    assert freq.get_best_lemma("asco", ["asca", "asco"], "n") == "asco"

    flist_data = """\
asco 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,asco,n,,10:asco\
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
    freq = FrequencyList(wordlist, allforms, sentences)

    assert freq.all_forms.get_lemmas("bienes") == ['n|bien', 'n|bienes']
    assert freq.get_lemmas("bienes", "n") == ["bien", "bienes"]
    assert freq.get_best_lemma("bienes", ["bien", "bienes"], "n") == "bienes"

    flist_data = """\
bienes 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,bienes,n,,10:bienes\
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
    freq = FrequencyList(wordlist, allforms, sentences)

    assert freq.all_forms.get_lemmas("rasguño") == ['v|rasguñar', 'n|rasguño']
    assert freq.get_ranked_pos("rasguño") == ["n", "v"]

    flist_data = """\
rasguño 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,rasguño,n,,10:rasguño\
"""

def test_dios():

    wordlist_data = """\
dios {n-meta} :: {{es-noun|m|dioses|f=diosa}}
dios {n-forms} :: f=diosa; fpl=diosas; pl=dioses
dios {m} :: god
diosa {n-meta} :: {{es-noun|f|m=dios}}
diosa {n-forms} :: m=dios; mpl=dios; pl=diosas
diosa {f} :: goddess
diosa {n-meta} :: {{es-noun|f}}
diosa {n-forms} :: pl=diosas
diosa {f} [biochemistry] :: diose
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences)

    assert freq.get_lemmas("dioses", "n") == ["dios"]
    assert freq.get_lemmas("diosas", "n") == ["dios", "diosa"]
    assert freq.get_lemmas("diosa", "n") == ["dios", "diosa"]

    assert freq.get_best_lemma("diosa", ["dios", "diosa"], "n") == "dios"

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
40,dios,n,,10:dios|10:dioses|10:diosa|10:diosas\
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
    freq = FrequencyList(wordlist, allforms, sentences)

    assert freq.get_lemmas("aquellos", "pron") == ['aquellos', 'aquél']

    assert freq.get_best_lemma("aquellos", ['aquellos', 'aquél'], "pron") == "aquél"

    flist_data = """\
aquellos 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,aquél,pron,PRONOUN; LITERAL,10:aquellos\
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
    freq = FrequencyList(wordlist, allforms, sentences)

    assert freq.get_lemmas("vete", "v") == ['ir', 'ver', 'vetar']

    assert freq.get_best_lemma("vete", ['ir', 'ver', 'vetar'], "v") == "ir"

def test_veros():

    wordlist_data = """\
ver {v-meta} :: {{es-verb}} {{es-conj}}
ver {v} :: x
vero {n-meta} :: {{es-noun|m}}
vero {m} [heraldry] :: vair
"""

    wordlist = Wordlist(wordlist_data.splitlines())
    allforms = AllForms.from_wordlist(wordlist)
    freq = FrequencyList(wordlist, allforms, sentences)

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
    freq = FrequencyList(wordlist, allforms, sentences)

    assert freq.get_lemmas("veras", "n") == ["vera", "veras"]
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
    freq = FrequencyList(wordlist, allforms, sentences)

    lemmas = ["microonda", "microondas"]
    assert freq.get_lemmas("microondas", "n") == lemmas
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
    freq = FrequencyList(wordlist, allforms, sentences)

    lemmas = ['hamburguesa', 'hamburgués']
    assert freq.get_lemmas("hamburguesa", "n") == lemmas
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
    freq = FrequencyList(wordlist, allforms, sentences)

    lemmas = ['pierna', 'piernas']
    assert freq.get_lemmas("piernas", "n") == lemmas
    assert freq.get_best_lemma("piernas", lemmas, "n") == "pierna"



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
    freq = FrequencyList(wordlist, allforms, sentences)

    print(allforms.all_forms)

    assert freq.get_lemmas("izquierdas", "n") == ["izquierda"]
    assert freq.get_lemmas("izquierdo", "adj") == ["izquierdo"]
    assert freq.get_lemmas("izquierdos", "adj") == ["izquierdo"]
    assert freq.get_lemmas("izquierdas", "adj") == ["izquierdo"]
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
35065,izquierda,n,,34629:izquierda|436:izquierdas
8384,izquierdo,adj,,8150:izquierdo|234:izquierdos\
"""
