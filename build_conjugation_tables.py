#import urllib.request
import requests
import json
import re
import os

_hash_cache = {}
def is_changed(filename, data):
    global _hash_cache
    hashvalue = hash(str(data))
    if filename not in _hash_cache or _hash_cache[filename] != hashvalue:
        _hash_cache[filename] = hashvalue
        return True
    return False

def load_json(filename):
    if os.path.isfile(filename):
        with open(filename) as infile:
            data =  json.load(infile)
            is_changed(infile, data)
            return data

def save_json(filename, data):
    if not is_changed(filename, data):
        #print("No save needed")
        return
    with open(filename, "w") as outfile:
        #print("saving")
        json.dump(data, outfile, ensure_ascii=False)


def lua2python(data, varname):

    dicts = []
    idx = 0
    maxidx = len(data)-1


    # find all pairs of braces {} and flag those missing any = assignments as lists
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
                print("Too many closing brackets")
                print(line)
                exit()

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



def load_paradigm_list():
    data = load_json("paradigm_list.json")
    if not data:
        url = 'https://en.wiktionary.org/w/api.php?action=query&prop=revisions&rvslots=*&rvprop=content&format=json&titles=Module:es-conj/data/paradigms'

        print("dl", url)
        res = requests.get( url )
        json_data = res.json()
        data = list(json_data['query']['pages'].values())[0]['revisions'][0]['slots']['main']['*']

        save_json("paradigm_list.json", data)

    return data


def scrape_paradigm(ending, paradigm):
    title = 'Module:es-conj/data/' + ending
    if paradigm != "":
        title += "/" + paradigm
    url = 'https://en.wiktionary.org/w/api.php?action=query&prop=revisions&rvslots=*&rvprop=content|ids&format=json&titles=' + title
    niceurl = 'https://en.wiktionary.org/wiki/' + title

    print("dl", url)
    res = requests.get( url )
    json_data = res.json()
    revision = list(json_data['query']['pages'].values())[0]['revisions'][0]['revid']
    wikitext = list(json_data['query']['pages'].values())[0]['revisions'][0]['slots']['main']['*']
    return { "wikitext": wikitext, "revision": revision, "url": niceurl }

def load_paradigm(ending, paradigm):
    paradigms = load_json("paradigms.json")
    if not paradigms:
        paradigms = {}
    if ending not in paradigms:
        paradigms[ending] = {}

    if paradigm not in paradigms[ending]:
        paradigms[ending][paradigm] = scrape_paradigm(ending, paradigm)

    save_json("paradigms.json", paradigms)

    return paradigms[ending][paradigm]


pdata = load_paradigm_list()
data = lua2python(pdata, "paradigm_list")

paradigm_list = {}
exec(data)

paradigms = {}
dump = "paradigms = {}\n"
for ending,pgroup in paradigm_list.items():
    for paradigm in pgroup:
        if ending not in paradigms:
            luadata = load_paradigm(ending, "")
            dump += "paradigms['%s'] = {}\n"%(ending)
            dump += "# Data from: %s (revision: %s)\n"%(luadata["url"],luadata["revision"])
            dump += lua2python(luadata["wikitext"], "paradigms['%s']['']"%(ending)) +"\n\n"
            paradigms[ending] = { "": luadata }

        luadata = load_paradigm(ending, paradigm)
        dump += "# Data from: %s (revision: %s)\n"%(luadata["url"],luadata["revision"])
        dump += lua2python(luadata["wikitext"], "paradigms['%s']['%s']"%(ending,paradigm)) +"\n\n"
        paradigms[ending][paradigm] = luadata


print("# This file is generated automatically, do not hand edit")
print(dump)
