from spanish_words.verbs import SpanishVerbs

verb = None

def test_init(spanish):
    global verb
    verb = SpanishVerbs(spanish)

def test_conjugate():
    conjugate = verb.conjugate
    # Regular
    assert conjugate("hablar", 7) == ['hablo']

    # Irregular
    assert conjugate("ser", 21) == ['fuiste']

    # Pattern has multiple words for form
    assert conjugate("proveer", 3) == ['proveído', 'provisto']

    # Pattern uses multiple stems
    assert conjugate("mirar") == {1: ['mirar'], 2: ['mirando'], 3: ['mirado'], 4: ['mirada'], 5: ['mirados'], 6: ['miradas'], 7: ['miro'], 8: ['miras'], 9: ['mirás'], 10: ['mira'], 11: ['miramos'], 12:
['miráis'], 13: ['miran'], 14: ['miraba'], 15: ['mirabas'], 16: ['miraba'], 17: ['mirábamos'], 18: ['mirabais'], 19: ['miraban'], 20: ['miré'], 21: ['miraste'], 22: ['miró'], 23: ['miramos'], 24: ['mirasteis'], 25: ['miraron'], 26: ['miraré'], 27: ['mirarás'], 28: ['mirará'], 29: ['miraremos'], 30: ['miraréis'], 31: ['mirarán'], 32: ['miraría'], 33: ['mirarías'], 34: ['miraría'], 35: ['miraríamos'], 36: ['miraríais'], 37: ['mirarían'], 38: ['mire'], 39: ['mires'], 40: ['mirés'], 41: ['mire'], 42: ['miremos'], 43: ['miréis'], 44: ['miren'], 45: ['mirara'], 46: ['miraras'], 47: ['mirara'], 48: ['miráramos'], 49: ['mirarais'], 50: ['miraran'], 51: ['mirase'], 52: ['mirases'], 53: ['mirase'], 54: ['mirásemos'], 55: ['miraseis'], 56: ['mirasen'], 57: ['mirare'], 58: ['mirares'], 59: ['mirare'], 60: ['miráremos'], 61: ['mirareis'], 62: ['miraren'], 63: ['mira'], 64: ['mirá'], 65: ['mire'], 66: ['miremos'], 67: ['mirad'], 68: ['miren'], 69: ['mires'], 70: ['mire'], 71: ['miremos'], 72: ['miréis'], 73: ['miren']}

    # verb uses two different conjugation patterns
    assert conjugate("emparentar", 7) == ['empariento', 'emparento']

    assert conjugate("hablar") == {1: ['hablar'], 2: ['hablando'], 3: ['hablado'], 4: ['hablada'], 5: ['hablados'], 6: ['habladas'], 7: ['hablo'], 8: ['hablas'], 9: ['hablás'], 10: ['habla'], 11: ['hablamos'], 12: ['habláis'], 13: ['hablan'], 14: ['hablaba'], 15: ['hablabas'], 16: ['hablaba'], 17: ['hablábamos'], 18: ['hablabais'], 19: ['hablaban'], 20: ['hablé'], 21: ['hablaste'], 22: ['habló'], 23: ['hablamos'], 24: ['hablasteis'], 25: ['hablaron'], 26: ['hablaré'], 27: ['hablarás'], 28: ['hablará'], 29: ['hablaremos'], 30: ['hablaréis'], 31: ['hablarán'], 32: ['hablaría'], 33: ['hablarías'], 34: ['hablaría'], 35: ['hablaríamos'], 36: ['hablaríais'], 37: ['hablarían'], 38: ['hable'], 39: ['hables'], 40: ['hablés'], 41: ['hable'], 42: ['hablemos'], 43: ['habléis'], 44: ['hablen'], 45: ['hablara'], 46: ['hablaras'], 47: ['hablara'], 48: ['habláramos'], 49: ['hablarais'], 50: ['hablaran'], 51: ['hablase'], 52: ['hablases'], 53: ['hablase'], 54: ['hablásemos'], 55: ['hablaseis'], 56: ['hablasen'], 57: ['hablare'], 58: ['hablares'], 59: ['hablare'], 60: ['habláremos'], 61: ['hablareis'], 62: ['hablaren'], 63: ['habla'], 64: ['hablá'], 65: ['hable'], 66: ['hablemos'], 67: ['hablad'], 68: ['hablen'], 69: ['hables'], 70: ['hable'], 71: ['hablemos'], 72: ['habléis'], 73: ['hablen']}
    assert conjugate("cargar") == {1: ['cargar'], 2: ['cargando'], 3: ['cargado'], 4: ['cargada'], 5: ['cargados'], 6: ['cargadas'], 7: ['cargo'], 8: ['cargas'], 9: ['cargás'], 10: ['carga'], 11: ['cargamos'], 12: ['cargáis'], 13: ['cargan'], 14: ['cargaba'], 15: ['cargabas'], 16: ['cargaba'], 17: ['cargábamos'], 18: ['cargabais'], 19: ['cargaban'], 20: ['cargué'], 21: ['cargaste'], 22: ['cargó'], 23: ['cargamos'], 24: ['cargasteis'], 25: ['cargaron'], 26: ['cargaré'], 27: ['cargarás'], 28: ['cargará'], 29: ['cargaremos'], 30: ['cargaréis'], 31: ['cargarán'], 32: ['cargaría'], 33: ['cargarías'], 34: ['cargaría'], 35: ['cargaríamos'], 36: ['cargaríais'], 37: ['cargarían'], 38: ['cargue'], 39: ['cargues'], 40: ['cargués'], 41: ['cargue'], 42: ['carguemos'], 43: ['carguéis'], 44: ['carguen'], 45: ['cargara'], 46: ['cargaras'], 47: ['cargara'], 48: ['cargáramos'], 49: ['cargarais'], 50: ['cargaran'], 51: ['cargase'], 52: ['cargases'], 53: ['cargase'], 54: ['cargásemos'], 55: ['cargaseis'], 56: ['cargasen'], 57: ['cargare'], 58: ['cargares'], 59: ['cargare'], 60: ['cargáremos'], 61: ['cargareis'], 62: ['cargaren'], 63: ['carga'], 64: ['cargá'], 65: ['cargue'], 66: ['carguemos'], 67: ['cargad'], 68: ['carguen'], 69: ['cargues'], 70: ['cargue'], 71: ['carguemos'], 72: ['carguéis'], 73: ['carguen']}



def test_get_score():
    get_score = verb.get_score
    # prefer the infinitive
    assert get_score({'verb': 'ver', 'form': 1}) > get_score({'verb': 'ver', 'form': 10})

    # ve, both imperative but ir wins for being irregular
    assert get_score({'verb': 'ir', 'form': 63}) > get_score({'verb': 'ver', 'form': 63})

    # comido, prefer past participle over irregular indicative
    assert get_score({'verb': 'comer', 'form': 3}) > get_score({'verb': 'comedir', 'form': 7})


def test_get_endings():
    get_endings = verb.get_endings
    assert get_endings("-er", "") == {'er': [1], 'iendo': [2], 'ido': [3], 'ida': [4], 'idos': [5], 'idas': [6], 'o': [7], 'es': [8], 'és': [9], 'e': [10, 63], 'emos': [11], 'éis': [12], 'en': [13], 'ía': [14, 16], 'ías': [15], 'íamos': [17], 'íais': [18], 'ían': [19], 'í': [20], 'iste': [21], 'ió': [22], 'imos': [23], 'isteis': [24], 'ieron': [25], 'eré': [26], 'erás': [27], 'erá': [28], 'eremos': [29], 'eréis': [30], 'erán': [31], 'ería': [32, 34], 'erías': [33], 'eríamos': [35], 'eríais': [36], 'erían': [37], 'a': [38, 41, 65, 70], 'as': [39, 69], 'ás': [40], 'amos': [42, 66, 71], 'áis': [43, 72], 'an': [44, 68, 73], 'iera': [45, 47], 'ieras': [46], 'iéramos': [48], 'ierais': [49], 'ieran': [50], 'iese': [51, 53], 'ieses': [52], 'iésemos': [54], 'ieseis': [55], 'iesen': [56], 'iere': [57, 59], 'ieres': [58], 'iéremos': [60], 'iereis': [61], 'ieren': [62], 'é': [64], 'ed': [67]}
    assert get_endings("-er", "atardecer") == {'cer': [1], 'ciendo': [2], 'cido': [3], 'cida': [4], 'cidos': [5], 'cidas': [6], 'zco': [7], 'ces': [8], None: [9, 40, 64], 'ce': [10, 63], 'cemos': [11], 'céis': [12], 'cen': [13], 'cía': [14, 16], 'cías': [15], 'cíamos': [17], 'cíais': [18], 'cían': [19], 'cí': [20], 'ciste': [21], 'ció': [22], 'cimos': [23], 'cisteis': [24], 'cieron': [25], 'ceré': [26], 'cerás': [27], 'cerá': [28], 'ceremos': [29], 'ceréis': [30], 'cerán': [31], 'cería': [32, 34], 'cerías': [33], 'ceríamos': [35], 'ceríais': [36], 'cerían': [37], 'zca': [38, 41, 65, 70], 'zcas': [39, 69], 'zcamos': [42, 66, 71], 'zcáis': [43, 72], 'zcan': [44, 68, 73], 'ciera': [45, 47], 'cieras': [46], 'ciéramos': [48], 'cierais': [49], 'cieran': [50], 'ciese': [51, 53], 'cieses': [52], 'ciésemos': [54], 'cieseis': [55], 'ciesen': [56], 'ciere': [57, 59], 'cieres': [58], 'ciéremos': [60], 'ciereis': [61], 'cieren': [62], 'ced': [67]}

def test_get_inflection_id():
    get_inflection_id = verb.get_inflection_id
    assert get_inflection_id({'mood': 'gerund'}) == 2
    assert get_inflection_id({'mood': 'indicative', 'tense': 'present', 'pers': 3, 'number': 's'}) == 10
    assert get_inflection_id({'pers': 3, 'mood': 'indicative', 'tense': 'present', 'number': 's'}) == 10


def test_reverse_conjugate():
    reverse_conjugate = verb.reverse_conjugate
    assert reverse_conjugate("podría") == [{'verb': 'poder', 'form': 32}, {'verb': 'poder', 'form': 34}]
    assert reverse_conjugate("comido") == [{'verb': 'comedir', 'form': 7}, {'verb': 'comer', 'form': 3}]
    assert reverse_conjugate("volaste") == [{'verb': 'volar', 'form': 21}]
    assert reverse_conjugate("fuiste") == [{'form': 21, 'verb': 'ir'}, {'form': 21, 'verb': 'ser'}]

    assert reverse_conjugate("notaword") == []

    assert reverse_conjugate("hablo")[0]['verb'] == "hablar"
    assert reverse_conjugate("proveído")[0]['verb'] == "proveer"
    assert reverse_conjugate("provisto")[0]['verb'] == "proveer"

    assert reverse_conjugate("mirando")[0]['verb'] == "mirar"
    assert reverse_conjugate("mirabais")[0]['verb'] == "mirar"

    # Verb uses two different conjugation patterns
    assert reverse_conjugate("emparento")[0]['verb'] == "emparentar"
    assert reverse_conjugate("empariento")[0]['verb'] == "emparentar"

    assert reverse_conjugate("suelto")[0]['verb'] == "soltar"

    assert reverse_conjugate("damelos")[0]['verb'] == "dar"
    assert reverse_conjugate("dalosme") == []
    assert reverse_conjugate("daloslos") == []


def test_select_best():
    reverse_conjugate = verb.reverse_conjugate
    select_best = verb.select_best

    v = reverse_conjugate("podría")
    res = select_best(v)
    assert len(res) == 1 and res[0]['verb'] == 'poder'

    v = []
    assert select_best(v) == []

    v = [{'verb': 'volar', 'form': 21}]
    assert select_best(v) == [{'verb': 'volar', 'form': 21}]

    pairs = {
        "comido": "comer",
        "ve": "ir",
        "sé": "saber",
        "haciendo": "hacer",
        "vete": "ir",
        "vengan": "venir",
        "volaste": "volar",
        "temes": "temer",
        "viste": "ver",
        "podemos": "poder",
        "suelen": "soler",
        "viven": "vivir",
        "diste": "dar",
    }

    for k,v in pairs.items():
        item = reverse_conjugate(k)
        res = select_best(item)
        assert len(res) == 1
        assert [k, res[0]['verb']] == [k, v]


def test_is_irregular():
    is_irregular = verb.is_irregular
    assert is_irregular(None, 7) == False
    assert is_irregular("", 7) == False
    assert is_irregular("notaword", 7) == False

    assert is_irregular("tener", 7) == True
    assert is_irregular("tener", 1) == False

    assert is_irregular("hablar", 7) == False

def test_unstress():
    unstress = verb.unstress
    assert unstress("tést") == "test"

def test_do_conjugate():
    do_conjugate = verb.do_conjugate
    assert do_conjugate( ['cr', ''], '-ar', 'i-í unstressed') == {1: ['criar'], 2: ['criando'], 3: ['criado'], 4: ['criada'], 5: ['criados'], 6: ['criadas'], 7: ['crío'], 8: ['crías'], 9: ['crias', 'criás'], 10: ['cría'], 11: ['criamos'], 12: ['criais', 'criáis'], 13: ['crían'], 14: ['criaba'], 15: ['criabas'], 16: ['criaba'], 17: ['criábamos'], 18: ['criabais'], 19: ['criaban'], 20: ['crie', 'crié'], 21: ['criaste'], 22: ['crio', 'crió'], 23: ['criamos'], 24: ['criasteis'], 25: ['criaron'], 26: ['criaré'], 27: ['criarás'], 28: ['criará'], 29: ['criaremos'], 30: ['criaréis'], 31: ['criarán'], 32: ['criaría'], 33: ['criarías'], 34: ['criaría'], 35: ['criaríamos'], 36: ['criaríais'], 37: ['criarían'], 38: ['críe'], 39: ['críes'], 40: ['criéis', 'crieis'], 41: ['críe'], 42: ['criemos'], 43: ['crieis'], 44: ['críen'], 45: ['criara'], 46: ['criaras'], 47: ['criara'], 48: ['criáramos'], 49: ['criarais'], 50: ['criaran'], 51: ['criase'], 52: ['criases'], 53: ['criase'], 54: ['criásemos'], 55: ['criaseis'], 56: ['criasen'], 57: ['criare'], 58: ['criares'], 59: ['criare'], 60: ['criáremos'], 61: ['criareis'], 62: ['criaren'], 63: ['cría'], 64: ['criá', 'cria'], 65: ['críe'], 66: ['criemos'], 67: ['criad'], 68: ['críen'], 69: ['críes'], 70: ['críe'], 71: ['criemos'], 72: ['crieis'], 73: ['críen']}
    assert do_conjugate(['habl'], '-ar', '') == {1: ['hablar'], 2: ['hablando'], 3: ['hablado'], 4: ['hablada'], 5: ['hablados'], 6: ['habladas'], 7: ['hablo'], 8: ['hablas'], 9: ['hablás'], 10: ['habla'], 11: ['hablamos'], 12: ['habláis'], 13: ['hablan'], 14: ['hablaba'], 15: ['hablabas'], 16: ['hablaba'], 17: ['hablábamos'], 18: ['hablabais'], 19: ['hablaban'], 20: ['hablé'], 21: ['hablaste'], 22: ['habló'], 23: ['hablamos'], 24: ['hablasteis'], 25: ['hablaron'], 26: ['hablaré'], 27: ['hablarás'], 28: ['hablará'], 29: ['hablaremos'], 30: ['hablaréis'], 31: ['hablarán'], 32: ['hablaría'], 33: ['hablarías'], 34: ['hablaría'], 35: ['hablaríamos'], 36: ['hablaríais'], 37: ['hablarían'], 38: ['hable'], 39: ['hables'], 40: ['hablés'], 41: ['hable'], 42: ['hablemos'], 43: ['habléis'], 44: ['hablen'], 45: ['hablara'], 46: ['hablaras'], 47: ['hablara'], 48: ['habláramos'], 49: ['hablarais'], 50: ['hablaran'], 51: ['hablase'], 52: ['hablases'], 53: ['hablase'], 54: ['hablásemos'], 55: ['hablaseis'], 56: ['hablasen'], 57: ['hablare'], 58: ['hablares'], 59: ['hablare'], 60: ['habláremos'], 61: ['hablareis'], 62: ['hablaren'], 63: ['habla'], 64: ['hablá'], 65: ['hable'], 66: ['hablemos'], 67: ['hablad'], 68: ['hablen'], 69: ['hables'], 70: ['hable'], 71: ['hablemos'], 72: ['habléis'], 73: ['hablen']}

def test_is_past_participle():
    is_past_participle = verb.is_past_participle
    assert is_past_participle("notaword") == False
    assert is_past_participle("abierto") == True
    assert is_past_participle("rotas") == True
    assert is_past_participle("aeropuerto") == False
