import requests
import json
import re
import os
import argparse
import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def fail(*args, **kwargs):
    eprint(*args, **kwargs)
    exit(1)

parser = argparse.ArgumentParser(description='Scrape irregular verb usage from wiktionary')
parser.add_argument('-p', '--patterns', help="Save pattern usage to specified file")
parser.add_argument('-v', '--verbs',    help="Save irregular verb list to specified file")
parser.add_argument('-c', '--cache',    help="Cache file name to use (Default: _cache.json)")
args = parser.parse_args()

if args.patterns is None and args.verbs is None:
    parser.error("You must specify either --patterns or --verbs to dump files")

if args.cache is None:
    args.cache = "_cache.json"


_cache = None
def init_cache():
    global _cache
    if _cache is None:
        _cache = { "hash": {}, "data": {} }
        if os.path.isfile(args.cache):
            with open(args.cache) as infile:
                _cache['data'] = json.load(infile)

def save_cache():
    global _cache
    with open(args.cache, "w") as outfile:
        json.dump(_cache['data'], outfile, ensure_ascii=False)

def has_changed(tag, data):
    global _cache

    hashvalue = hash(str(data))
    if tag not in _cache['hash'] or _cache['hash'][tag] != hashvalue:
        _cache['hash'][tag] = hashvalue
        return True
    return False

def update_data(tag, data):
    if _cache is None:
        init_cache()
    if has_changed(tag, data):
        _cache['data'][tag] = data
        save_cache()

def load_data(tag, default=None):
    global _cache
    if _cache is None:
        init_cache()
    if tag in _cache['data']:
        return _cache['data'][tag]
    return default



#def load_json(filename):
#    if os.path.isfile(filename):
#        with open(filename) as infile:
#            data =  json.load(infile)
#            is_changed(infile, data)
#            return data

#def save_json(filename, data):
#    if not is_changed(filename, data):
#        return
#    with open(filename, "w") as outfile:
#        json.dump(data, outfile, ensure_ascii=False)


def lua2python(data, varname):

    dicts = []
    idx = 0
    maxidx = len(data)-1


    # find all pairs of braces {} and flag those missing any = assignments as lists (unless they're empty)
    chunks = []
    while idx<maxidx:
        if data[idx] == "{":
            dicts.append({"start": idx, "is_list": True})
        elif data[idx] == "}":
            item = dicts.pop()
            item["end"] = idx
            chunks.append(item)
        elif data[idx] == "=" and len(dicts):
            dicts[len(dicts)-1]["is_list"] = False
        idx += 1

    # replace {} with [] in lists
    replacements = {}
    for item in chunks:
        if item['is_list']:
            # Empty sets of braces aren't considered lists
            if (data[item['start']+1:item['end']].strip()) == "":
                continue
            replacements[item['start']] = "["
            replacements[item['end']] = "]"

        else:
            inquote = False
            for idx in range(item['start'],item['end']):
                if data[idx] == '"':    # very simple quote handling, doesn't understand escapes
                    inquote = not inquote
                if not inquote and data[idx] == "=":
                    replacements[idx] = ":"

    replaced = ""
    strpos = 0
    for idx in sorted(replacements.keys()):
        replaced += data[strpos:idx] + replacements[idx]
        strpos = idx+1
    replaced += data[strpos:len(data)]


    data = replaced
    # quote unquoted bare items being assigned values
    # this blows up on items within quotes so skip lines with a single " before the match
#    pattern = r"([a-zA-Z0-9\-_]+)\s*:"
#    data = re.sub(pattern, r'"\1":', data)

    # strip [] from items being assigned values
    pattern = r"""(?x)     #
               \[          # opening bracket
               ([^\]]+)    # all chars until the closing bracket
               \]          # closing bracket
               \s*:        # whitespace :
    """
    data = re.sub(pattern, r'  \1:', data)



    # Strip anything that isn't part of data assignment
    newdata = varname + " = {\n"
    in_data = False
    depth = 0
    for line in data.split("\n"):
        line = line.replace("\t", "    ")

        if in_data:
            depth += line.count("{") + line.count("[") - line.count("}") - line.count("]")
            if depth == 0:
                in_data = False
                # add a , after the last closing }
                line = re.sub("}([^}]*)$", r"},\1", line)
                # add a , after the last closing ]
                line = re.sub("\]([^\]]*)$", r"],\1", line)
            if depth < 0:
                eprint(line)
                fail("Too many closing brackets")

            elif line.strip() == "":
                newdata += "\n"
            else:
                newdata += line+"\n"
        elif "=" in line:

            # ignore variable declarations
            if "local " in line:
                continue

            line = re.sub(r"""data\[([^\]]+)\]\s+=""", r"\1:", line)
            depth = line.count("{") + line.count("[") - line.count("}") - line.count("]")
            if depth:
                in_data = True
                newdata += line+"\n"
            else:


                # add a comma to the end of single line assignment items
                newdata += line+",\n"

        #  permit empty lines, but ignore everything else
        elif line.strip() == "":
            newdata += "\n"

    # convert lua string escapes to python strings
    newdata = re.sub(r"'''", r"'", newdata)

    # convert lua comments to python comments
    newdata = re.sub(r"--", r"#", newdata)

    # convert lua true to python True
    newdata = re.sub(r"true", r"True", newdata)

    # convert lua false to python False
    newdata = re.sub(r"false", r"False", newdata)

    newdata += "}"

    return newdata


def get_template_params(template):
    template = template[2:-2]
    params = template.split("|")
    ending =  params[0][len("es-conj"):]

    item = {
        'pattern': "",
        'stems': []
    }

    for param in params[1:]:
        if "=" in param:
            if param.startswith("p="):
                item['pattern'] = param[2:]
        else:
            item['stems'].append(param)

    return item


def find_templates(wikitext):
    return re.findall(r"{{es-conj[^}]+}}", wikitext, re.MULTILINE)

def get_patterns(wikitext):
    patterns = [ get_template_params(x) for x in find_templates(wikitext) ]

    # remove dups and preserve order (requires cpython 3.6+)
    return list(map(json.loads, dict.fromkeys(map(json.dumps, patterns)).keys()))


def load_paradigm_list():
    data = load_data("paradigm_list")
    if not data:
        url = 'https://en.wiktionary.org/w/api.php?action=query&prop=revisions&rvslots=*&rvprop=content&format=json&titles=Module:es-conj/data/paradigms'

        eprint("dl", url)
        res = requests.get( url )
        json_data = res.json()
        data = list(json_data['query']['pages'].values())[0]['revisions'][0]['slots']['main']['*']

        update_data("paradigm_list", data)


    global _paradigm_list
    pydata = lua2python(data, "global _paradigm_list\n_paradigm_list")
    exec(pydata)
    return _paradigm_list

def scrape_verb(verb):
    url = 'https://en.wiktionary.org/w/api.php?action=query&prop=revisions&rvslots=*&rvprop=content|ids&format=json&titles=' + verb
    niceurl = 'https://en.wiktionary.org/wiki/' + verb

    eprint("dl", url)
    res = requests.get( url )
    json_data = res.json()
    revision = list(json_data['query']['pages'].values())[0]['revisions'][0]['revid']
    wikitext = list(json_data['query']['pages'].values())[0]['revisions'][0]['slots']['main']['*']
    return { "wikitext": wikitext, "revision": revision, "url": niceurl }

def scrape_paradigm(ending, paradigm):
    title = 'Module:es-conj/data/' + ending
    if paradigm != "":
        title += "/" + paradigm
    url = 'https://en.wiktionary.org/w/api.php?action=query&prop=revisions&rvslots=*&rvprop=content|ids&format=json&titles=' + title
    niceurl = 'https://en.wiktionary.org/wiki/' + title

    eprint("dl", url)
    res = requests.get( url )
    json_data = res.json()
    revision = list(json_data['query']['pages'].values())[0]['revisions'][0]['revid']
    wikitext = list(json_data['query']['pages'].values())[0]['revisions'][0]['slots']['main']['*']
    return { "wikitext": wikitext, "revision": revision, "url": niceurl }

def load_verbs():
    return load_data("verbs", {})

def save_verbs(data):
    update_data("verbs", data)

def load_verb(verb):
    data = load_verbs()
    if not data:
        data = {}
    if verb not in data:
        data[verb] = scrape_verb(verb)

    save_verbs(data)
    return data[verb]


def load_paradigms():
    return load_data("paradigms", {})

def save_paradigms(data):
    update_data("paradigms", data)

def load_paradigm(ending, paradigm):
    paradigms = load_paradigms()
    if not paradigms:
        paradigms = {}
    if ending not in paradigms:
        paradigms[ending] = {}

    if paradigm not in paradigms[ending]:
        paradigms[ending][paradigm] = scrape_paradigm(ending, paradigm)

    save_paradigms(paradigms)

    return paradigms[ending][paradigm]


def load_category_members(ending, pattern):
    categories = load_data("categories", {})

    if ending not in categories:
        categories[ending] = {}

    if pattern not in categories[ending]:
        url = make_category_link(ending, pattern)
        eprint("dl ",url)
        res = requests.get( url )
        json_data = res.json()
        if not json_data or 'query' not in json_data or 'categorymembers' not in json_data['query']:
            eprint("No json data for ", ending, p)
        else:
            categories[ending][pattern] = [ verb for verb in [ item['title'] for item in json_data['query']['categorymembers'] ]]

    update_data("categories", categories)
    return categories[ending][pattern]


def make_category_link(ending, paradigm):
    return "https://en.wiktionary.org/w/api.php?action=query&format=json&list=categorymembers&cmlimit=500&cmtitle=" \
           + "Category:Spanish_verbs_ending_in_" + ending + "_(conjugation_" + paradigm.replace(" ", "_") + ")"


def dump_patterns(filename):

    paradigm_list = load_paradigm_list()
    paradigms = load_paradigms()

    dump = "paradigms = {}\n"
    for ending,pgroup in paradigm_list.items():

        # Scrape the rules for the ending
        luadata = load_paradigm(ending, "")
        if ending not in paradigms:
            paradigms[ending] = { "": luadata }

        dump += "paradigms['%s'] = {}\n"%(ending)
        dump += "# Data from: %s (revision: %s)\n"%(luadata["url"],luadata["revision"])
        dump += lua2python(luadata["wikitext"], "paradigms['%s']['']"%(ending)) +"\n\n"

        # Scrape the rules for the pattern
        for pattern in pgroup:
            luadata = load_paradigm(ending,pattern)
            dump += "# Data from: %s (revision: %s)\n"%(luadata["url"],luadata["revision"])
            dump += lua2python(luadata["wikitext"], "paradigms['%s']['%s']"%(ending,pattern)) +"\n\n"
            paradigms[ending][pattern] = luadata

    with open(filename, "w") as outfile:
        outfile.write("# This file is generated automatically, do not hand edit\n#\n")
        outfile.write(dump)


def dump_verbs(filename):

    paradigm_list = load_paradigm_list()
    paradigms = load_paradigms()
    verbs = load_verbs()

    dump = "{\n"
    for ending,pgroup in paradigm_list.items():
        for pattern in pgroup:

            # Get all the verbs that use the pattern
            # skip the common irregulars that follow easy rules
            if ending == "-ar" and pattern in [ "-zar", "-car", "-gar" ]:
                continue

            category_members = load_category_members(ending, pattern)
            for verb in category_members:
                # Skip non-verbs that are included in the category list
                if verb.startswith("-"):
                    continue
                if verb not in verbs:
                    verbs[verb] = load_verb(verb)

    first = True
    for verb in verbs:
        # Skip reflixives if the non-reflexive is on the list
        if verb.endswith("se") and verb[:-2] in verbs:
            continue
        data = get_patterns(verbs[verb]['wikitext'])
        if first:
            dump += '"%s": %s'%(verb,json.dumps(data))
            first = False
        else:
            dump += ',\n"%s": %s'%(verb,json.dumps(data))


    dump += "\n}"

    with open(filename, "w") as outfile:
        outfile.write(dump)


def init():

    if args.patterns:
        dump_patterns(args.patterns)

    if args.verbs:
        dump_verbs(args.verbs)

init()