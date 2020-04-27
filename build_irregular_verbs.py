#import urllib.request
import requests
import json
import re
import os

FILENAME="irregular_verbs.json"

# list from https://en.wiktionary.org/wiki/Module:es-conj/data/paradigms
paradigms = {
  "-ar": {
    "andar": "andar",
    "dar": "dar",
    "errar": "errar",
    "estar": "estar",
    "jugar": "jugar",
#    "-car": "-car",
    "-car i-í": "-car (i-í)",
    "-car o-ue": "-car (o-ue)",
#    "-gar": "-gar",
    "-gar e-ie": "-gar (e-ie)",
    "-gar i-í": "-gar (i-í)",
    "-gar o-ue": "-gar (o-ue)",
    "-guar": "-guar",
    "-izar": "-izar",
    "-eizar": "-eizar",
#    "-zar": "-zar",
    "-zar e-ie": "-zar (e-ie)",
    "-zar go-güe": "-zar (go-güe)",
    "-zar o-ue": "-zar (o-ue)",
    "e-ie": "e-ie",
    "go-güe": "go-güe",
    "i-í": "i-í",
    "i-í unstressed": "i-í",
    "iar-ar": "-iar-ar",
    "o-hue": "o-hue",
    "o-ue": "o-ue",
    "u-ú": "u-ú",
    "imp": "imp"
  },
  "-er": {
    "atardecer": "atardecer",
    "atañer": "atañer",
    "caber": "caber",
    "caer": "caer",
    "haber": "haber",
    "hacer": "hacer",
    "hacer i-í": "hacer (i-í)",
    "nacer": "c-zc",
    "placer": "placer",
    "poder": "poder",
    "-poner": "poner",
    "poner": "poner",
    "poseer": "-eer",
    "proveer": "-eer",
    "querer": "querer",
    "raer": "raer",
    "roer": "roer",
    "romper": "romper",
    "saber": "saber",
    "ser": "ser",
    "soler": "soler",
    "tener": "tener",
    "traer": "traer",
    "valer": "valer",
    "ver": "ver",
    "ver e-é": "ver",
    "yacer": "yacer",
    "-cer": "-cer",
    "-cer o-ue": "-cer (o-ue)",
    "-eer": "-eer",
    "-ger": "-ger",
    "-olver": "-olver",
    "-ñer": "-ñer",
    "c-zc": "c-zc",
    "e-ie": "e-ie",
    "o-hue": "o-hue",
    "o-ue": "o-ue" ,
    "-tener": "tener",
  },
  "-ir": {
    "asir": "asir",
    "aterir": "aterir",
    "concernir": "e-ie",
    "decir": "decir",
    "bendecir": "decir",
    "maldecir": "decir",
    "manumitir": "manumitir",
    "predecir": "decir",
    "redecir": "decir",
    "elegir": "-egir",
    "erguir": "erguir",
    "imprimir": "imprimir",
    "morir": "o-ue",
    "pudrir": "pudrir",
    "ir": "ir",
    "rehuir": "rehuir",
    "salir": "salir",
    "sustituir": "-uir",
    "-venir": "venir",
    "venir": "venir",
    "-brir": "-brir",
    "-cir": "-cir",
    "-ducir": "-ducir", 
    "-egir": "-egir",
    "-gir": "-gir",
    "-guir": "-guir",
    "-guir (e-i)": "-guir (e-i)",
    "-güir": "-güir",
    "-quir": "-quir",
    "-scribir": "-scribir",
    "-uir": "-uir",
    "-ñir": "-ñir",
    "-ñir e-i": "-ñir (e-i)",
    "c-zc": "c-zc",
    "e-i": "e-i",
    "e-ie": "e-ie",
    "e-ie-i": "e-ie-i",
    "i-ie": "i-ie",
    "i-í": "i-í",
    "o-ue": "o-ue",
    "u-ú": "u-ú",
  },
  "-ír": {
    "embaír": "embaír",
    "oír": "oír",
    "reír": "-eír",
    "-eír": "-eír",
    "freír": "-eír",
    "refreír": "-eír",
  }
}

_json_hash = ""
def hash_json(data):
    global _json_hash
    _json_hash = hash(str(data))

def load_json():
    if os.path.isfile(FILENAME):
        with open(FILENAME) as infile:
            data =  json.load(infile)
            hash_json(data)
            return data

def save_json(data):
    if hash(str(data)) == _json_hash:
        print("No save needed")
        return
    with open(FILENAME, "w") as outfile:
        print("saving")
        json.dump(data, outfile)

def make_category_link(ending, paradigm):
    return "https://en.wiktionary.org/w/api.php?action=query&format=json&list=categorymembers&cmtitle=" \
           + "Category:Spanish_verbs_ending_in_" + ending + "_(conjugation_" + paradigm.replace(" ", "_") + ")"

def make_template_link(template):
    template = template[:-2]+"|json=1}}"
    return "https://en.wiktionary.org/w/api.php?action=expandtemplates&prop=wikitext&format=json&text=" \
           + template

def make_page_link(verb):
    return "https://en.wiktionary.org/w/api.php?action=query&prop=revisions&rvslots=*&rvprop=content&format=json&" \
            + "titles=" + verb

def scrape_irregular_verb_list():
    for ending,pgroup in paradigms.items():
        for p in pgroup:
            url = make_category_link(ending, p)
            res = requests.get( url )
            json_data = res.json()
            if not json_data or 'query' not in json_data or 'categorymembers' not in json_data['query']:
                print("No json data for ", ending, p)
                continue
            for verb in [ item['title'] for item in json_data['query']['categorymembers'] ]:
                if verb not in irregular_verbs:
                    irregular_verbs[verb] = { ending: p }


def load_irregular_verb_list():
    data = load_json()
    if not data:
        print("file no existy")
        exit()
        data = scrape_irregular_verb_list()
        save_json(data)
    return data


def scrape_verb_conjugation(verb, template):
    print("Scraping conjugation for ", verb)
    url = make_template_link(template)
    res = requests.get( url )
    json_data = res.json()
    if not json_data or 'expandtemplates' not in json_data or 'wikitext' not in json_data['expandtemplates']:
        print("No json data for ", verb)
        return

    return json.loads(json_data['expandtemplates']['wikitext'])

def scrape_verb_template(verb):
    print("Scraping template for ", verb)
    url = make_page_link(verb)
    res = requests.get( url )
    json_data = res.json()
    if not json_data or 'query' not in json_data or 'pages' not in json_data['query']:
        print("No json data for ", verb)
        return

    for pageid,page in json_data['query']['pages'].items():
        verbname = page['title']
        wikitext = page['revisions'][0]['slots']['main']['*']
        res = re.search(r"{{es-conj[^}]+}}", wikitext, re.MULTILINE)
        return res.group(0)

irregular_verbs = load_irregular_verb_list()

# add the base paradigms into the list (poner, tener, andar, etc)
for ending,pgroup in paradigms.items():
    for paradigm in pgroup:
        if paradigm.endswith("r") and " " not in paradigm and "-" not in paradigm:
            if paradigm not in irregular_verbs:
                irregular_verbs[paradigm] = { ending: paradigm }

for verb,verbdata in irregular_verbs.items():
    if verb.startswith("-"):
        continue
    if verb.endswith("se"):
        # Skip reflexives that are duplicates of non-reflexives
        if verb[:-2] in irregular_verbs:
            continue

    if 'template' not in verbdata:
        template = scrape_verb_template(verb)
        if not template:
            print("No template data for", verb)
        else:
            verbdata['template'] = template

    if 'conjugation' not in verbdata:
        conjugation = scrape_verb_conjugation(verb, verbdata['template'])
        if not conjugation:
            print("No conjugation data for", verb)
        else:
            verbdata['conjugation'] = conjugation

save_json(irregular_verbs)


reverse_irregular = {}
for verb,verbdata in irregular_verbs.items():
    if verb.startswith("-"):
        continue
    if verb.endswith("se"):
        if verb[:-2] in irregular_verbs:
            continue

    for conjugated in verbdata['conjugation'].keys():
        if conjugated not in reverse_irregular:
            reverse_irregular[conjugated] = verb
        else:
            reverse_irregular[conjugated] += "|"+verb

with open("reverse_irregular.json", "w") as outfile:
    json.dump(reverse_irregular, outfile, ensure_ascii=False)
