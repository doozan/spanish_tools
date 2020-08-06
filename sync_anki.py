#!/usr/bin/python3
# -*- python-mode -*-

import argparse
import csv
import genanki
import json
import math
import os
import psutil
import re
import sqlite3
import subprocess
import sys
import time
import urllib.request

import spanish_sentences
import spanish_speech
from spanish_words import SpanishWords

parser = argparse.ArgumentParser(description='Import anki deck/sync')
parser.add_argument('filename', help="apkg file to import")
parser.add_argument('--anki', help="Use the specified anki profile")
parser.add_argument('--remove', help="Filename containing note ids to remove")
args = parser.parse_args()

args.filename = os.path.abspath(args.filename)
if not os.path.isfile(args.filename):
    print(f"File does not exist: {args.filename}")
    exit(1)

if args.remove and not os.path.isfile(args.remove):
    print(f"File does not exist: {args.remove}")
    exit(1)

def request(action, **params):
    return {'action': action, 'params': params, 'version': 6}

def invoke(action, **params):
    requestJson = json.dumps(request(action, **params)).encode('utf-8')
    response = json.load(urllib.request.urlopen(urllib.request.Request('http://localhost:8765', requestJson)))
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']


def sync_anki(profile, deck_filename, removed_filename=None):

    if any("/usr/bin/anki" in p.info['cmdline'] for p in psutil.process_iter(['cmdline'])):
        print("Anki is already running, cannot continue")
        exit(1)
        # TODO: Switch to profile if already running?

    params = ["/usr/bin/anki"]
    if profile:
        params += [f"--profile={profile}"]

    proc = subprocess.Popen(params)

    tries=120
    while tries:
        try:
            result = invoke('deckNames')

        except urllib.error.URLError:
            time.sleep(1)
        else:
            break
        tries-=1

    if not tries:
        print("Failed to start Anki or problem running AnkiConnect")
        proc.terminate()
        exit(1)

    result = invoke('importPackage', path=deck_filename)

    removed_notes = []
    with open(args.remove) as infile:
        removed_notes = [ line.split(" ",1)[0].split("#",1)[0].strip() for line in infile ]

    if len(removed_notes):
        print(f"removing {removed_notes}")
        result = invoke('deleteNotes', notes=removed_notes)
        print(f"result {result}")

        time.sleep(6)

    # Do this again to force a database save
    result = invoke('importPackage', path=deck_filename)

    result = invoke('sync')
    time.sleep(3)

    # And again just to settle things after the sync
    result = invoke('importPackage', path=deck_filename)
    time.sleep(3)

    proc.terminate()

sync_anki(args.anki, args.filename, removed_filename=args.remove)
