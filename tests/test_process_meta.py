import process_meta

def test_make_plural():
    make_plural = process_meta.make_plural
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

def test_get_adjective_forms():
    get_adjective_forms = process_meta.get_adjective_forms
    assert get_adjective_forms("girador", "m") == {'ms': 'girador', 'mp': 'giradores', 'fs': 'giradora', 'fp': 'giradoras'}
    assert get_adjective_forms("batidora", "f") == {'ms': 'batidor', 'mp': 'batidores', 'fs': 'batidora', 'fp': 'batidoras'}
    assert get_adjective_forms("alta", "f") == {'ms': 'alto', 'mp': 'altos', 'fs': 'alta', 'fp': 'altas'}
    assert get_adjective_forms("optimista", "m") == {'ms': 'optimista', 'mp': 'optimistas', 'fs': 'optimista', 'fp': 'optimistas'}
    assert get_adjective_forms("eficaz", "m") == {'ms': 'eficaz', 'mp': 'eficaces', 'fs': 'eficaz', 'fp': 'eficaces'}
    assert get_adjective_forms("amoral", "m") == {'ms': 'amoral', 'mp': 'amorales', 'fs': 'amoral', 'fp': 'amorales'}
    assert get_adjective_forms("columnar", "m") == {'ms': 'columnar', 'mp': 'columnares', 'fs': 'columnar', 'fp': 'columnares'}
    assert get_adjective_forms("mandón", "m") == {'ms': 'mandón', 'mp': 'mandones', 'fs': 'mandón', 'fp': 'mandones'}
    assert get_adjective_forms("común", "m") == {'ms': 'común', 'mp': 'comunes', 'fs': 'común', 'fp': 'comunes'}
    assert get_adjective_forms("jafán", "m") == {'ms': 'jafán', 'mp': 'jafanes', 'fs': 'jafana', 'fp': 'jafanas'}
    assert get_adjective_forms("cortés", "m") == {'ms': 'cortés', 'mp': 'corteses', 'fs': 'cortesa', 'fp': 'cortesas'}
    assert get_adjective_forms("calorín", "m") == {'ms': 'calorín', 'mp': 'calorines', 'fs': 'calorina', 'fp': 'calorinas'}

    assert get_adjective_forms("fresco", "m") ==  {'fp': 'frescas', 'fs': 'fresca', 'mp': 'frescos', 'ms': 'fresco'}


