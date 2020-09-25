#!/usr/bin/python3
# -*- python-mode -*-

import luadata_to_python

import requests
import json
import re
import os
import argparse
import datetime

parser = argparse.ArgumentParser(description='Scrape irregular Spanish verb conjugation paradigms from wiktionary')
args = parser.parse_args()

def get_wikipage(page):
    url = 'https://en.wiktionary.org/w/api.php?action=query&prop=revisions&rvslots=*&rvprop=content|ids&format=json&titles=' + page
    niceurl = 'https://en.wiktionary.org/wiki/' + page

    res = requests.get( url )
    json_data = res.json()
    revision = list(json_data['query']['pages'].values())[0]['revisions'][0]['revid']
    wikitext = list(json_data['query']['pages'].values())[0]['revisions'][0]['slots']['main']['*']
    return { "wikitext": wikitext, "revision": revision, "url": niceurl }

def load_paradigm_list():

    data = get_wikipage('Module:es-conj/data/paradigms')

    global _paradigm_list
    pydata = luadata_to_python.convert(data["wikitext"], "data", "global _paradigm_list\n_paradigm_list", no_warning=True)
    exec(pydata)
    return _paradigm_list

def get_paradigm(ending, paradigm):
    page = 'Module:es-conj/data/' + ending
    if paradigm != "":
        page += "/" + paradigm

    return get_wikipage(page)

def dump_paradigms():

    paradigm_list = load_paradigm_list()

    dump = ["paradigms = {}\n"]
    for ending,pgroup in paradigm_list.items():
        dump.append(f"paradigms['{ending}'] = {{}}\n")

        # Scrape the rules for the patterns
        patterns = [""] + list(pgroup.keys())
        for pattern in patterns:
            res = get_paradigm(ending,pattern)
            dump.append(f"# Data from: {res['url']} (revision: {res['revision']}, scraped {datetime.datetime.now()})")
            dump.append(luadata_to_python.convert(res["wikitext"], "data", f"paradigms['{ending}']['{pattern}']", numeric_keys=True, no_warning=True))
            dump.append("\n\n")

    print("# This file is generated automatically, do not hand edit\n#\n")
    print(''.join(dump))


def main():
    dump_paradigms()

main()
