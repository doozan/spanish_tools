from spanish_words.nouns import SpanishNouns
import pytest

noun = None

def test_init(spanish):
    global noun
    noun = SpanishNouns(spanish)

def test_get_lemma():
    get_lemma = noun.get_lemma

    assert get_lemma("casas") == "casa"

    assert get_lemma("notaword") == "notaword"

    assert get_lemma("casas") == "casa"
    assert get_lemma("narices") == "nariz"

    assert get_lemma("piernas") == "pierna"

    assert get_lemma("dos") == "dos"
    assert get_lemma("autobús") == "autobús"
    assert get_lemma("cubrebocas") == "cubrebocas"
    assert get_lemma("gas") == "gas"

    assert get_lemma("mentirosas") == "mentiroso"

    assert get_lemma("espráis") == "espray"

    assert get_lemma("bordes") == "borde"
    assert get_lemma("tardes") == "tarde"

    assert get_lemma("meses") == "mes"

    assert get_lemma("escocés") == "escocés"
    assert get_lemma("ratones") == "ratón"

    assert get_lemma("órdenes") == "orden"

def test_get_lemma():
    make_plural = noun.make_plural

    assert make_plural("acuerdo de paz", "m") == ["acuerdos de paz"]
    assert make_plural("asesino a sueldo", "m") == ["asesinos a sueldo"]

    assert make_plural("aire fresco", "m") == ["aires frescos"]

    assert make_plural("casa", "f") == ["casas"]
    assert make_plural("menú", "m") == ["menús", "menúes"]
    assert make_plural("disfraz", "m") == ["disfraces"]
    assert make_plural("hertz", "m") == ["hertz"]
    assert make_plural("saltamontes", "m") == ["saltamontes"]
    assert make_plural("ademán", "m") == ["ademanes"]
    assert make_plural("desorden", "m") == ["desórdenes"]
    assert make_plural("color", "m") == ["colores"]
    assert make_plural("coach", "m") == ["coaches"]
    assert make_plural("confort", "m") == ["conforts"]
    assert make_plural("robot", "m") == ["robots"]
