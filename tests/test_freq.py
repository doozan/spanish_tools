from enwiktionary_wordlist.wordlist import Wordlist
import pytest
import spanish_sentences

from freq import FrequencyList

sentences = spanish_sentences.sentences()

def test_simple():

    wordlist_data = """\
_____
protector
pos: noun
  meta: {{es-noun|m|protectores|f=protectora|f2=protectriz}}
  forms: f=protectora; f=protectriz; fpl=protectoras; fpl=protectrices; pl=protectores
  form: m
  gloss: protector (someone who protects or guards)
pos: noun
  meta: {{es-noun|m}}
  forms: pl=protectores
  form: m
  gloss: protector (a device or mechanism which is designed to protect)
_____
protectora
pos: noun
  meta: {{es-noun|f|m=protector}}
  forms: m=protector; mpl=protectores; pl=protectoras
  form: f
  gloss: female equivalent of "protector"
pos: noun
  meta: {{es-noun|f}}
  forms: pl=protectoras
  form: f
  gloss: animal shelter (an organization that provides temporary homes for stray pet animals)
    syn: protectora de animales
_____
protectoras
pos: noun
  meta: {{head|es|noun plural form|g=f-p}}
  form: f-p
  gloss: inflection of "protector"
_____
protectores
pos: noun
  meta: {{head|es|noun plural form|g=m-p}}
  form: m-p
  gloss: inflection of "protector"
_____
protectrices
pos: noun
  meta: {{head|es|noun plural form|g=f-p}}
  form: f-p
  gloss: inflection of "protector"
_____
protectriz
pos: noun
  meta: {{es-noun|f|m=protector}}
  forms: m=protector; mpl=protectores; pl=protectrices
  form: f
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

    assert freq.get_lemmas("protectores", "noun") == ["protector"]
    assert freq.get_lemmas("protectoras", "noun") == ["protector", "protectora"]
    assert freq.get_lemmas("notaword", "noun") == ["notaword"]

    assert freq.get_ranked_pos("protectoras") == ["noun"]

    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
60,protector,noun,LITERAL; CLEAR,10:protector|10:protectores|10:protectriz|10:protectrices|10:protectora|10:protectoras
10,unknown,none,NOUSAGE; NODEF; NOSENT; COMMON,10:unknown\
"""


def test_xsimple2():

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

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.get_ranked_pos("roja") == ["adj", "noun"]

def test_filters():

    wordlist_data = """\
test {noun-meta} :: x
test {m} :: test
test {adj-meta} :: x
test {adj} :: obsolete form of "test"
"""

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

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

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.all_forms.get("vamos") == ['verb|ir', 'verb|irse']
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
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
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

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.all_forms.get("diva") == ['noun|divo', 'adj|divo']
    assert freq.get_lemmas("diva", "noun") == ["divo"]

    flist_data = """\
diva 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,divo,adj,NOSENT,10:diva\
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

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.all_forms.get("hijo") == ['noun|hijo']
    assert freq.get_lemmas("hijo", "noun") == ["hijo"]

    flist_data = """\
hijo 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
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

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.all_forms.get("asco") == ['noun|asco', 'noun|asca']
    assert freq.get_lemmas("asco", "noun") == ["asca", "asco"]
    assert freq.get_best_lemma("asco", ["asca", "asco"], "noun") == "asco"

    flist_data = """\
asco 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
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

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.all_forms.get("bienes") == ['noun|bien', 'noun|bienes']
    assert freq.get_lemmas("bienes", "noun") == ["bien", "bienes"]
    assert freq.get_best_lemma("bienes", ["bien", "bienes"], "noun") == "bienes"

    flist_data = """\
bienes 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,bienes,noun,CLEAR,10:bienes\
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

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.all_forms.get("rasguño") == ['verb|rasguñar', 'noun|rasguño']
    assert freq.get_ranked_pos("rasguño") == ["verb", "noun"]

    flist_data = """\
rasguño 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,rasguñar,verb,CLEAR,10:rasguño\
"""

def test_dios():

    wordlist_data = """\
dios {noun-meta} :: {{es-noun|m|dioses|f=diosa}}
dios {noun-forms} :: f=diosa; fpl=diosas; pl=dioses
dios {m} :: god
diosa {noun-meta} :: {{es-noun|f|m=dios}}
diosa {noun-forms} :: m=dios; mpl=dios; pl=diosas
diosa {f} :: goddess
diosa {noun-meta} :: {{es-noun|f}}
diosa {noun-forms} :: pl=diosas
diosa {f} [biochemistry] :: diose
"""

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.get_lemmas("dioses", "noun") == ["dios"]
    assert freq.get_lemmas("diosas", "noun") == ["dios", "diosa"]
    assert freq.get_lemmas("diosa", "noun") == ["dios", "diosa"]

    assert freq.get_best_lemma("diosa", ["dios", "diosa"], "noun") == "dios"

#    assert list(freq.all_forms.get("dios", {})) == ['noun:dios:m']
#    assert list(freq.all_forms.get("dioses", {})) == ['noun:dios:pl']
#    assert list(freq.all_forms.get("diosa", {})) == ["noun:dios:f"]
#    assert list(freq.all_forms.get("diosas", {})) == ["noun:diosa:pl"]

    flist_data = """\
dios 10
dioses 10
diosa 10
diosas 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
40,dios,noun,CLEAR,10:dios|10:dioses|10:diosa|10:diosas\
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

#    assert list(freq.all_forms.get("dios", {})) == ['noun:dios:m']
#    assert list(freq.all_forms.get("dioses", {})) == ['noun:dios:pl']
#    assert list(freq.all_forms.get("diosa", {})) == ["noun:dios:f"]
#    assert list(freq.all_forms.get("diosas", {})) == ["noun:diosa:pl"]

    flist_data = """\
aquellos 10
"""
    assert "\n".join(freq.process(flist_data.splitlines())) == """\
count,spanish,pos,flags,usage
10,aquél,pron,PRONOUN; LITERAL; COMMON,10:aquellos\
"""


def test_vete():

    wordlist_data = """\
ir {verb-meta} :: x
ir {verb-forms} :: imp_i2s_acc_2=vete; imp_i2s_dat_2=vete
ir {v} :: x
ver {verb-meta} :: x
ver {verb-forms} :: imp_i2s_acc_2=vete; imp_i2s_dat_2=vete
ver {v} :: x
verse {verb-meta} :: x
verse {verb-forms} ::  63=vete; imp_i2s_acc_2=vete; imp_i2s_dat_2=vete
verse {v} :: x
vetar {verb-meta} :: x
vetar {verb-forms} ::  38=vete; 41=vete; 65=vete; 70=vete
vetar {v} :: x
"""

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.get_lemmas("vete", "verb") == ['ir', 'ver', 'vetar']

    assert freq.get_best_lemma("vete", ['ir', 'ver', 'vetar'], "verb") == "ir"

def test_veros():

    wordlist_data = """\
ver {verb-meta} :: x
ver {verb-forms} :: inf_acc_5=veros; inf_dat_5=veros
ver {v} :: x
vero {noun-meta} :: {{es-noun|m}}
vero {noun-forms} :: pl=veros
vero {m} [heraldry] :: vair
"""

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.get_ranked_pos("veros") == ["verb", "noun"]

def test_veras():

    wordlist_data = """\
vera {noun-meta} :: {{es-noun|f}}
vera {noun-forms} :: pl=veras
vera {f} [poetic] | lado :: side, face
vera {noun-meta} :: {{es-noun|f}}
vera {noun-forms} :: pl=veras
vera {f} :: verawood (Bulnesia arborea)
veras {noun-meta} :: {{es-noun|f-p}}
veras {fp} :: truth; reality
veras {fp} :: serious things
"""

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    assert freq.get_lemmas("veras", "noun") == ["vera", "veras"]
    assert freq.get_best_lemma("veras", ["vera", "veras"], "noun") == "veras"

def test_microondas():

    wordlist_data = """\
microonda {noun-meta} :: {{es-noun|f}}
microonda {noun-forms} :: pl=microondas
microonda {f} :: microwave (electromagnetic wave)
microondas {noun-meta} :: {{es-noun|m|microondas}}
microondas {noun-forms} :: pl=microondas
microondas {m} | horno de microondas :: microwave oven, microwave
microondas {m} :: necklacing (execution by burning tyre)
"""

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    lemmas = ["microonda", "microondas"]
    assert freq.get_lemmas("microondas", "noun") == lemmas
    assert freq.get_best_lemma("microondas", lemmas, "noun") == "microondas"

def test_hamburguesa():
    wordlist_data = """\
hamburgués {noun-meta} :: {{es-noun|m|hamburgueses|f=hamburguesa|fpl=hamburguesas}}
hamburgués {noun-forms} :: f=hamburguesa; fpl=hamburguesas; pl=hamburgueses
hamburgués {m} :: Hamburger, a person from Hamburg
hamburguesa {noun-meta} :: {{es-noun|f}}
hamburguesa {noun-forms} :: pl=hamburguesas
hamburguesa {f} :: hamburger
hamburguesa {f} :: female equivalent of "hamburgués"; Hamburger
"""

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    lemmas = ['hamburguesa', 'hamburgués']
    assert freq.get_lemmas("hamburguesa", "noun") == lemmas
    assert freq.get_best_lemma("hamburguesa", lemmas, "noun") == "hamburguesa"


def test_piernas():
    wordlist_data = """\
pierna {noun-meta} :: {{es-noun|f}}
pierna {noun-forms} :: pl=piernas
pierna {f} | pata :: leg (lower limb of a human)
piernas {noun-meta} :: {{es-noun|m|piernas}}
piernas {noun-forms} :: pl=piernas
piernas {m} [dated] :: twit; idiot
"""

    freq = FrequencyList(wordlist_data.splitlines(), None, sentences)

    lemmas = ['pierna', 'piernas']
    assert freq.get_lemmas("piernas", "noun") == lemmas
    assert freq.get_best_lemma("piernas", lemmas, "noun") == "pierna"


