from spanish_words.nouns import SpanishNouns
import pytest

noun = None

def test_init(spanish):
    global noun
    noun = SpanishNouns(spanish)

def test_get_lemma():
    get_lemma = noun.old_get_lemma

    assert get_lemma("casas") == "casa"

    assert get_lemma("notaword") == "notaword"

    assert get_lemma("casas") == "casa"
    assert get_lemma("narices") == "nariz"

    assert get_lemma("piernas") == "pierna"

#    assert get_lemma("dos") == "dos"
#    assert get_lemma("autobús") == "autobús"
#    assert get_lemma("cubrebocas") == "cubrebocas"
#    assert get_lemma("gas") == "gas"

#    assert get_lemma("mentirosas") == "mentiroso"

#    assert get_lemma("espráis") == "espray"

#    assert get_lemma("bordes") == "borde"
#    assert get_lemma("tardes") == "tarde"

#    assert get_lemma("meses") == "mes"

#    assert get_lemma("escocés") == "escocés"
#    assert get_lemma("ratones") == "ratón"

#    assert get_lemma("órdenes") == "orden"

def test_make_singular():
    make_singular = noun.make_singular
    assert make_singular("acuerdos de paz") == ['acuerdo de paz', 'acuerdos de paz']
    assert make_singular("asesinos a sueldo") == ['asesino a sueldo', 'asesinos a sueldo']

#    assert make_singular("aires frescos") == ["aire fresco"]

    assert make_singular("casas") == ["casa", "casas"]
    assert make_singular("menúes") == ["menúe", "menú", "menúes"]
    assert make_singular("disfraces") == ["disfrace", "disfraz", "disfraces", "disfrác"]
    assert make_singular("hertz") == ["hertz"]
    assert make_singular("saltamontes") == ["saltamonte", "saltamontes"]
    assert make_singular("ademanes") == ['ademane', 'ademanes', 'ademán', 'ademan']
    assert make_singular("desórdenes") == ['desórdene', 'desórdenes', 'desórdén', 'desorden', 'desórden']
    assert make_singular("colores") == ['colore', 'colores', 'colór', 'color']
    assert make_singular("coaches") ==  ['coache', 'coaches', 'coach']
    assert make_singular("conforts") == ['conforts', 'confort']
    assert make_singular("robots") == ['robots', 'robot']

    assert make_singular("canciones") ==  ['cancione', 'canciones', 'canción', 'cancion']

    assert make_singular("notaword") == ['notaword']


    assert "nariz" in make_singular("narices")
    assert "pierna" in make_singular("piernas")

    assert "autobús" in make_singular("autobús")
    assert "cubrebocas" in make_singular("cubrebocas")
#    assert "gas" in make_singular("gas")

    assert "espray" in make_singular("espráis")

    assert "borde" in make_singular("bordes")
    assert "tarde" in make_singular("tardes")

    assert "mes" in make_singular("meses")

    assert "escocés" in make_singular("escocés")
    assert "ratón" in make_singular("ratones")

    assert "orden" in make_singular("órdenes")


