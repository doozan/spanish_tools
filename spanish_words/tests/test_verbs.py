from spanish_words.verbs import SpanishVerbs

verb = None

def test_init():
    global verb
    verb = SpanishVerbs(None)

def test_get_score():
    # prefer the infinitive
    assert verb.get_score({'verb': 'ver', 'form': 1}) > verb.get_score({'verb': 'ver', 'form': 10})

    # ve, both imperative but ir wins for being irregular
    assert verb.get_score({'verb': 'ir', 'form': 63}) > verb.get_score({'verb': 'ver', 'form': 63})

    # comido, prefer past participle over irregular indicative
    assert verb.get_score({'verb': 'comer', 'form': 3}) > verb.get_score({'verb': 'comedir', 'form': 7})


def test_get_endings():
    assert verb.get_endings("-er", "") == {'er': [1], 'iendo': [2], 'ido': [3], 'ida': [4], 'idos': [5], 'idas': [6], 'o': [7], 'es': [8], 'és': [9], 'e': [10, 63], 'emos': [11], 'éis': [12], 'en': [13], 'ía': [14, 16], 'ías': [15], 'íamos': [17], 'íais': [18], 'ían': [19], 'í': [20], 'iste': [21], 'ió': [22], 'imos': [23], 'isteis': [24], 'ieron': [25], 'eré': [26], 'erás': [27], 'erá': [28], 'eremos': [29], 'eréis': [30], 'erán': [31], 'ería': [32, 34], 'erías': [33], 'eríamos': [35], 'eríais': [36], 'erían': [37], 'a': [38, 41, 65, 70], 'as': [39, 69], 'ás': [40], 'amos': [42, 66, 71], 'áis': [43, 72], 'an': [44, 68, 73], 'iera': [45, 47], 'ieras': [46], 'iéramos': [48], 'ierais': [49], 'ieran': [50], 'iese': [51, 53], 'ieses': [52], 'iésemos': [54], 'ieseis': [55], 'iesen': [56], 'iere': [57, 59], 'ieres': [58], 'iéremos': [60], 'iereis': [61], 'ieren': [62], 'é': [64], 'ed': [67]}
    assert verb.get_endings("-er", "atardecer") == {'cer': [1], 'ciendo': [2], 'cido': [3], 'cida': [4], 'cidos': [5], 'cidas': [6], 'zco': [7], 'ces': [8], None: [9, 40, 64], 'ce': [10, 63], 'cemos': [11], 'céis': [12], 'cen': [13], 'cía': [14, 16], 'cías': [15], 'cíamos': [17], 'cíais': [18], 'cían': [19], 'cí': [20], 'ciste': [21], 'ció': [22], 'cimos': [23], 'cisteis': [24], 'cieron': [25], 'ceré': [26], 'cerás': [27], 'cerá': [28], 'ceremos': [29], 'ceréis': [30], 'cerán': [31], 'cería': [32, 34], 'cerías': [33], 'ceríamos': [35], 'ceríais': [36], 'cerían': [37], 'zca': [38, 41, 65, 70], 'zcas': [39, 69], 'zcamos': [42, 66, 71], 'zcáis': [43, 72], 'zcan': [44, 68, 73], 'ciera': [45, 47], 'cieras': [46], 'ciéramos': [48], 'cierais': [49], 'cieran': [50], 'ciese': [51, 53], 'cieses': [52], 'ciésemos': [54], 'cieseis': [55], 'ciesen': [56], 'ciere': [57, 59], 'cieres': [58], 'ciéremos': [60], 'ciereis': [61], 'cieren': [62], 'ced': [67]}

def test_get_inflection_id():
    assert verb.get_inflection_id({'mood': 'gerund'}) == 2
    assert verb.get_inflection_id({'mood': 'indicative', 'tense': 'present', 'pers': 3, 'number': 's'}) == 10
    assert verb.get_inflection_id({'pers': 3, 'mood': 'indicative', 'tense': 'present', 'number': 's'}) == 10


def xtest_reverse_conjugate():
    assert verb.reverse_conjugate("podría") == [{'verb': 'poder', 'form': 32}, {'verb': 'poder', 'form': 34}, {'verb': 'podrir', 'form': 14}, {'verb': 'podrir', 'form': 16}]
    assert verb.reverse_conjugate("comido") == [{'verb': 'comedir', 'form': 7}, {'verb': 'comer', 'form': 3}]
    assert verb.reverse_conjugate("volaste") == [{'verb': 'volar', 'form': 21}]


def xtest_select_best():
    v = verb.reverse_conjugate("podría")
    res = verb.select_best(v)
    assert len(res) == 1 and res[0]['verb'] == 'poder'

    v = []
    assert verb.select_best(v) == []

    v = [{'verb': 'volar', 'form': 21}]
    assert verb.select_best(v) == [{'verb': 'volar', 'form': 21}]

    # comido
    #v = [{'verb': 'comedir', 'form': 7}, {'verb': 'comer', 'form': 3}]
    v = verb.reverse_conjugate("comido")
    res = verb.select_best(v)
    assert len(res) == 1 and res[0]['verb'] == 'comer'

    #v = [{'verb': 'ir', 'form': 63}, {'verb': 'ver', 'form': 10}, {'verb': 'ver', 'form': 63}]
    v = verb.reverse_conjugate("ve")
    res = verb.select_best(v)
    assert len(res) == 1 and res[0]['verb'] == 'ir'

    v = verb.reverse_conjugate("sé")
    res = verb.select_best(v)
    assert len(res) == 1 and res[0]['verb'] == 'ser'

    v = verb.reverse_conjugate("haciendo")
    res = verb.select_best(v)
    assert len(res) == 1 and res[0]['verb'] == 'hacer'

    v = verb.reverse_conjugate("vete")
    res = verb.select_best(v)
    assert len(res) == 1 and res[0]['verb'] == 'ir'

    v = verb.reverse_conjugate("vengan")
    res = verb.select_best(v)
    assert len(res) == 1 and res[0]['verb'] == 'venir'

    v = verb.reverse_conjugate("volaste")
    res = verb.select_best(v)
    assert len(res) == 1 and res[0]['verb'] == 'volar'

    v = verb.reverse_conjugate("temes")
    res = verb.select_best(v)
    assert len(res) == 1 and res[0]['verb'] == 'temar'

#    v = verb.reverse_conjugate("viste")
#    res = verb.select_best(v)
#    assert len(res) == 1 and res[0]['verb'] == 'ver'


def test_is_irregular():
    assert verb.is_irregular(None, 7) == False
    assert verb.is_irregular("", 7) == False
    assert verb.is_irregular("notaword", 7) == False

    assert verb.is_irregular("tener", 7) == True
    assert verb.is_irregular("tener", 1) == False

    assert verb.is_irregular("hablar", 7) == False

def test_conjugate():
    assert verb.conjugate("hablar") == {1: ['hablar'], 2: ['hablando'], 3: ['hablado'], 4: ['hablada'], 5: ['hablados'], 6: ['habladas'], 7: ['hablo'], 8: ['hablas'], 9: ['hablás'], 10: ['habla'], 11: ['hablamos'], 12: ['habláis'], 13: ['hablan'], 14: ['hablaba'], 15: ['hablabas'], 16: ['hablaba'], 17: ['hablábamos'], 18: ['hablabais'], 19: ['hablaban'], 20: ['hablé'], 21: ['hablaste'], 22: ['habló'], 23: ['hablamos'], 24: ['hablasteis'], 25: ['hablaron'], 26: ['hablaré'], 27: ['hablarás'], 28: ['hablará'], 29: ['hablaremos'], 30: ['hablaréis'], 31: ['hablarán'], 32: ['hablaría'], 33: ['hablarías'], 34: ['hablaría'], 35: ['hablaríamos'], 36: ['hablaríais'], 37: ['hablarían'], 38: ['hable'], 39: ['hables'], 40: ['hablés'], 41: ['hable'], 42: ['hablemos'], 43: ['habléis'], 44: ['hablen'], 45: ['hablara'], 46: ['hablaras'], 47: ['hablara'], 48: ['habláramos'], 49: ['hablarais'], 50: ['hablaran'], 51: ['hablase'], 52: ['hablases'], 53: ['hablase'], 54: ['hablásemos'], 55: ['hablaseis'], 56: ['hablasen'], 57: ['hablare'], 58: ['hablares'], 59: ['hablare'], 60: ['habláremos'], 61: ['hablareis'], 62: ['hablaren'], 63: ['habla'], 64: ['hablá'], 65: ['hable'], 66: ['hablemos'], 67: ['hablad'], 68: ['hablen'], 69: ['hables'], 70: ['hable'], 71: ['hablemos'], 72: ['habléis'], 73: ['hablen']}
    assert verb.conjugate("cargar") == {1: ['cargar'], 2: ['cargando'], 3: ['cargado'], 4: ['cargada'], 5: ['cargados'], 6: ['cargadas'], 7: ['cargo'], 8: ['cargas'], 9: ['cargás'], 10: ['carga'], 11: ['cargamos'], 12: ['cargáis'], 13: ['cargan'], 14: ['cargaba'], 15: ['cargabas'], 16: ['cargaba'], 17: ['cargábamos'], 18: ['cargabais'], 19: ['cargaban'], 20: ['cargé'], 21: ['cargaste'], 22: ['cargó'], 23: ['cargamos'], 24: ['cargasteis'], 25: ['cargaron'], 26: ['cargaré'], 27: ['cargarás'], 28: ['cargará'], 29: ['cargaremos'], 30: ['cargaréis'], 31: ['cargarán'], 32: ['cargaría'], 33: ['cargarías'], 34: ['cargaría'], 35: ['cargaríamos'], 36: ['cargaríais'], 37: ['cargarían'], 38: ['carge'], 39: ['carges'], 40: ['cargés'], 41: ['carge'], 42: ['cargemos'], 43: ['cargéis'], 44: ['cargen'], 45: ['cargara'], 46: ['cargaras'], 47: ['cargara'], 48: ['cargáramos'], 49: ['cargarais'], 50: ['cargaran'], 51: ['cargase'], 52: ['cargases'], 53: ['cargase'], 54: ['cargásemos'], 55: ['cargaseis'], 56: ['cargasen'], 57: ['cargare'], 58: ['cargares'], 59: ['cargare'], 60: ['cargáremos'], 61: ['cargareis'], 62: ['cargaren'], 63: ['carga'], 64: ['cargá'], 65: ['carge'], 66: ['cargemos'], 67: ['cargad'], 68: ['cargen'], 69: ['carges'], 70: ['carge'], 71: ['cargemos'], 72: ['cargéis'], 73: ['cargen']}
