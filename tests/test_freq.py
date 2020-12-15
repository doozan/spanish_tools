from enwiktionary_wordlist.wordlist import Wordlist
import pytest
import spanish_sentences

from freq import FrequencyList

sentences = spanish_sentences.sentences()

def test_simple():

    wordlist_data = """\
_____
protector
pos: n
  meta: {{es-noun|m|protectores|f=protectora|f2=protectriz}}
  forms: f=protectora; f=protectriz; fpl=protectoras; fpl=protectrices; pl=protectores
  g: m
  gloss: protector (someone who protects or guards)
pos: n
  meta: {{es-noun|m}}
  forms: pl=protectores
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


    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.wordlist.has_lemma("protectora", "n") == False

    assert freq.get_lemmas("protectores", "n") == ["protector"]
    assert freq.get_lemmas("protectoras", "n") == ["protector", "protectora"]
    assert freq.get_lemmas("notaword", "n") == ["notaword"]

    assert freq.get_ranked_pos("protectoras") == ["n"]

    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
60,protector,n,LITERAL; CLEAR,10:protector|10:protectores|10:protectriz|10:protectrices|10:protectora|10:protectoras
10,unknown,none,NOUSAGE; NODEF; NOSENT; COMMON,10:unknown\
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

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.get_ranked_pos("roja") == ["adj", "n"]

def test_filters():

    wordlist_data = """\
test {n-meta} :: x
test {m} :: test
test {adj-meta} :: x
test {adj} :: obsolete form of "test"
"""

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.filter_pos("test", ["n", "adj"]) == ["n"]
    assert freq.get_ranked_pos("test") == ["n"]

def test_lemma_filters():

    wordlist_data = """\
ir {v-meta} :: {{es-verb|-|ir|pres=voy|pret=fui|part=ido}} {{es-conj-ir|p=ir|combined=1|aux=ser}} {{es-conj-ir|p=ir|ref=yes|combined=1}}
ir {vi} :: to go (away from speaker and listener)
ir {vi} :: to come (towards or with the listener)
ir {v} [auxiliary] :: to be going to (near future), to go (+ a + infinitive)
ir {vr} :: to go away, to leave, to be off (see irse)
irse {v-meta} :: {{es-verb|-|ir|pres=voy|pret=fui|part=ido|ref=y}} {{es-conj-ir|p=ir|ref=1|combined=1}}
irse {v} | andarse; marcharse :: to go away, to leave, to depart, to go (when the destination is not essential; when something or someone is going somewhere else)
irse {v} :: to leak out (with liquids and gasses), to boil away, to go flat (gas in drinks)
"""

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.all_forms.get("vamos") == ['v|ir', 'v|irse']
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
20,ir,v,CLEAR,10:vamos|10:va\
"""


def test_diva():

    wordlist_data = """\
diva {n-meta} :: {{es-noun|f|m=divo}}
diva {f} :: diva
divo {adj-meta} :: {{es-adj|f=diva}}
divo {adj} :: star (famous)
divo {n-meta} :: {{es-noun|m|f=diva}}
divo {m} :: star, celeb\
"""

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.all_forms.get("diva") == ['n|divo', 'adj|divo']
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

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.all_forms.get("hijo") == ['n|hijo']
    assert freq.get_lemmas("hijo", "n") == ["hijo"]

    flist_data = """\
hijo 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,hijo,n,CLEAR,10:hijo\
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

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.all_forms.get("asco") == ['n|asco', 'n|asca']
    assert freq.get_lemmas("asco", "n") == ["asca", "asco"]
    assert freq.get_best_lemma("asco", ["asca", "asco"], "n") == "asco"

    flist_data = """\
asco 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,asco,n,CLEAR,10:asco\
"""

def test_bienes():

    wordlist_data = """\
bien {n-meta} :: {{es-noun|m|bienes}}
bien {m} :: good (as opposed to evil)
bienes {n-meta} :: {{es-noun|m-p}}
bienes {mp} :: goods (that which is produced, traded, bought or sold)
"""

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.all_forms.get("bienes") == ['n|bien', 'n|bienes']
    assert freq.get_lemmas("bienes", "n") == ["bien", "bienes"]
    assert freq.get_best_lemma("bienes", ["bien", "bienes"], "n") == "bienes"

    flist_data = """\
bienes 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,bienes,n,CLEAR,10:bienes\
"""

def test_rasguno():

    wordlist_data = """\
rasguñar {v-meta} :: {{es-verb|rasguñ|ar}} {{es-conj-ar|rasguñ|combined=1}}
rasguñar {vt} | arañar; rascar :: to scratch
rasguño {n-meta} :: {{es-noun}}
rasguño {m} | arañazo :: scratch
"""

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.all_forms.get("rasguño") == ['v|rasguñar', 'n|rasguño']
    assert freq.get_ranked_pos("rasguño") == ["v", "n"]

    flist_data = """\
rasguño 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,rasguñar,v,CLEAR,10:rasguño\
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

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.get_lemmas("dioses", "n") == ["dios"]
    assert freq.get_lemmas("diosas", "n") == ["dios", "diosa"]
    assert freq.get_lemmas("diosa", "n") == ["dios", "diosa"]

    assert freq.get_best_lemma("diosa", ["dios", "diosa"], "n") == "dios"

#    assert list(freq.all_forms.get("dios", {})) == ['n:dios:m']
#    assert list(freq.all_forms.get("dioses", {})) == ['n:dios:pl']
#    assert list(freq.all_forms.get("diosa", {})) == ["n:dios:f"]
#    assert list(freq.all_forms.get("diosas", {})) == ["n:diosa:pl"]

    flist_data = """\
dios 10
dioses 10
diosa 10
diosas 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
40,dios,n,CLEAR,10:dios|10:dioses|10:diosa|10:diosas\
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

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.get_lemmas("aquellos", "pron") == ['aquellos', 'aquél']

    assert freq.get_best_lemma("aquellos", ['aquellos', 'aquél'], "pron") == "aquél"

#    assert list(freq.all_forms.get("dios", {})) == ['n:dios:m']
#    assert list(freq.all_forms.get("dioses", {})) == ['n:dios:pl']
#    assert list(freq.all_forms.get("diosa", {})) == ["n:dios:f"]
#    assert list(freq.all_forms.get("diosas", {})) == ["n:diosa:pl"]

    flist_data = """\
aquellos 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,aquél,pron,PRONOUN; LITERAL; COMMON,10:aquellos\
"""


def test_vete():

    wordlist_data = """\
ir {v-meta} :: {{es-verb|-|ir|pres=voy|pret=fui|part=ido}} {{es-conj-ir|p=ir|combined=1|aux=ser}} {{es-conj-ir|p=ir|ref=yes|combined=1}}
ir {v} :: x
ver {v-meta} :: {{es-verb|v|er|pres=veo|pret=vi|part=visto}} {{es-conj-er|p=ver|combined=1}}
ver {v} :: x
verse {v-meta} :: {{es-verb|v|er|pres=veo|pret=vi|part=visto|ref=y}} {{es-conj-er|p=ver|ref=1|combined=1}}
verse {v} :: x
vetar {v-meta} :: {{es-verb|vet|ar}} {{es-conj-ar|vet|combined=1}}
vetar {v} :: x
"""

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.get_lemmas("vete", "v") == ['ir', 'ver', 'vetar']

    assert freq.get_best_lemma("vete", ['ir', 'ver', 'vetar'], "v") == "ir"

def test_veros():

    wordlist_data = """\
ver {v-meta} :: {{es-verb|v|er|pres=veo|pret=vi|part=visto}} {{es-conj-er|p=ver|combined=1}}
ver {v} :: x
vero {n-meta} :: {{es-noun|m}}
vero {m} [heraldry] :: vair
"""

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

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

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

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

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

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

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

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

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    lemmas = ['pierna', 'piernas']
    assert freq.get_lemmas("piernas", "n") == lemmas
    assert freq.get_best_lemma("piernas", lemmas, "n") == "pierna"


