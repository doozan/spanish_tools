import re
from os import path

FILE=path.join(path.dirname(__file__), 'es-en.txt')
allwords = {}

# TODO: check file exists and print error message
with open(FILE) as infile:
    for line in infile:

        word = re.match("^([^{]+)", line).group(1)
        word = word.strip()
        if word not in allwords:
            allwords[word] = [line]
        else:
            allwords[word].append(line)

# TODO: check file exists and print error message
FILE=path.join(path.dirname(__file__), 'custom.txt')
with open(FILE) as infile:
    for line in infile:

        word = re.match("^([^{]+)", line).group(1)
        word = word.strip()
        if word not in allwords:
            allwords[word] = [line]
        else:
            allwords[word].append(line)

def parse_spanish(data):

    res = re.match("^(.*) ?\{(.*?)\} ?\[?([^\]]*)\]?", data)

    # This only applies to 4 obscure entries in the database
    # better to just delete the bad lines
    if not res:
        print("DOES NOT MATCH REGEX: '%s'"% data)
        return {}

    tags = []
    if res.group(3) != "":
        tags = [ item.strip() for item in res.group(3).split(',') ]

    return {
        'lemma': res.group(1).strip(),
        'pos': res.group(2),
        'tags': tags
    }

def parse_line(line):
    esp, eng = line.split("::")
    return {
       'esp': parse_spanish(esp),
       'eng': eng.strip()
    }

def is_verb(pos):
    return pos.startswith("v")

def is_noun(pos):
    if pos in ["n", "f", "fp", "fs", "m", "mf", "mp", "ms"]:
        return True

def strip_eng_verb(eng):
    if eng.startswith("to "):
        return eng[3:]
    return eng

def should_ignore(item):
    if {"archaic", "dated", "historical", "obsolete", "rare"} & { tag.lower() for tag in item['tags'] }:
        return True

    return False


def do_analysis(word, items):

    usage = {}

    for item in items:
        if should_ignore(item['esp']):
            continue

        pos = item['esp']['pos']
        if pos not in usage:
            usage[pos] = {}

        tag = "x"
        if len(item['esp']['tags']):
            tag = ", ".join(item['esp']['tags'])
        if tag not in usage[pos]:
            usage[pos][tag] = []

        # Definitions are separated by commas and semicolons
        for defs in item['eng'].split("; "):
            is_new_def=True
            for eng in defs.split(", "):
                if is_verb(pos):
                    eng = strip_eng_verb(eng)
                if is_new_def:
                    eng = ";" + eng

                if eng not in usage[pos][tag]:
                    usage[pos][tag].append(eng)
                is_new_def = False


    if "m" in usage and "f" in usage:
        usage['m-f'] = {}
        if 'm' in usage:
            for tag in usage["m"].keys():
                newtag = 'm ' + tag if tag != 'x' else 'm'
                usage['m-f'][newtag] = usage['m'][tag]
            del usage['m']
        if 'f' in usage:
            for tag in usage["f"].keys():
                newtag = 'f ' + tag if tag != 'x' else 'f'
                usage['m-f'][newtag] = usage['f'][tag]
            del usage['f']


    return usage



# "primary" defs start with a ';' and synonyms follow
# for word with many definitons this can be too much info

# given the following input:
# [ ";def1", "def1-syn1", "def1-syn2", ";def2", ";def3", "def3-syn1" ]
# limit=2 gives [ ";def1", ";def2" ]
# limit=4 gives [ ";def1", "syn1-1", ";def2", ";def3" ]
# limit=5 gives [ ";def1", "syn1-1", ";def2", ";def3", "def3-syn1" ]


def get_best_defs(defs,limit):
    best = []

    if len(defs) <= limit:
        return defs

    #primary_defs = [ x[1:] for x in defs if x.startswith(';') ]

    # number of primary defs >= limit just return first limit defs
    #if len(primary_defs) >= limit:
    #    return primary_defs[:limit]

    # only one primary def, just return the first limit defs
    #elif len(primary_defs) == 1:
    #    return defs[:limit]

    # otherwise, build a list of defs to keep starting with primary defs
    # then the first syn of each def
    # then the second...
    # until we've hit the limit of keepers
    # Since it's important to keep the primary def and the synonyms together
    # we build a list of keepers by their index and then sort that index to
    # get things in the correct order

    keepidx = []
    keep_depth = 0

    while len(keepidx) < limit:
        cur_depth=0
        index=0
        for item in defs:
            if item.startswith(';'):
                cur_depth=0
            else:
                cur_depth += 1

            if cur_depth == keep_depth:
                keepidx.append(index)
                if len(keepidx) >= int(limit):
                    break
            index += 1
        keep_depth += 1
        if keep_depth > 3:
            break;

    keepers = []
    for idx in sorted(keepidx):
        keepers.append(defs[idx])

    return keepers

def defs_to_string(defs, pos):
    usage = ""
    if is_verb(pos):
        usage = "to "

    first=True
    for item in defs:
        sep=','
        word = item
        if item.startswith(';'):
            sep=';'
            word=item[1:]

        if not first:
            usage += sep+" "+word
        else:
            usage += word
            first=False

    return usage

def lookup(word, pos=""):
    query = word + " {"

    results = []

    if word not in allwords:
        #print("Not found ", word)
        return []

    lines = allwords[word]
    for line in lines:
        results.append(parse_line(line))

    # do pos filtering
    filtered = []
    if pos != "":
        for item in results:
            item_pos = item['esp']['pos']
            if (pos == "verb" and is_verb(item_pos)) or \
               (pos == "noun" and is_noun(item_pos)) or \
               (pos == item_pos):
                   filtered.append(item)
        if not len(filtered):
            removed = [ item['esp']['pos'] for item in results ]
            print("%s: %s not in %s" % (word,pos, removed))
    else:
        filtered = results

    analysis = do_analysis(word, filtered)
    return analysis
