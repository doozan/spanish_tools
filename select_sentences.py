#!/usr/bin/python3
# -*- python-mode -*-

import argparse
import csv
import os
import random
import urwid
import urwid.raw_display

import spanish_sentences
from spanish_words import SpanishWords

parser = argparse.ArgumentParser(description='Select sentences for word')
parser.add_argument('word', nargs="?", default=None, help="word")
parser.add_argument('pos',  nargs="?", default=None, help="part of speech")
parser.add_argument('--infile', help="If word not provided, read word list from file")
parser.add_argument('--outfile', default="spanish_data/sentences.forced", help="File to save sentence selections")
parser.add_argument('--dictionary', help="Dictionary file name (DEFAULT: es-en.txt)")
parser.add_argument('--sentences', help="Sentences file name (DEFAULT: sentences.tsv)")
parser.add_argument('--data-dir', help="Directory contaning the dictionary (DEFAULT: SPANISH_DATA_DIR environment variable or 'spanish_data')")
parser.add_argument('--custom-dir', help="Directory containing dictionary customizations (DEFAULT: SPANISH_CUSTOM_DIR environment variable or 'spanish_custom')")
args = parser.parse_args()

if not args.dictionary:
    args.dictionary="es-en.txt"

if not args.sentences:
    args.sentences="sentences.tsv"

if not args.data_dir:
    args.data_dir = os.environ.get("SPANISH_DATA_DIR", "spanish_data")

if not args.custom_dir:
    args.custom_dir = os.environ.get("SPANISH_CUSTOM_DIR", "spanish_custom")

words = SpanishWords(dictionary=args.dictionary, data_dir=args.data_dir, custom_dir=args.custom_dir)
sentences = spanish_sentences.sentences(sentences=args.sentences, data_dir=args.data_dir, custom_dir=args.custom_dir)

all_selections = {}


class SentenceChooser:
    palette=[
        ('reversed', 'standout', ''),
        ('foot','dark cyan', 'dark blue', 'bold'),
        ]


    def item_chosen(self, checkbox, new_state, user_data):
        c = self._all_options[user_data]
        tag = f"{c[3]}:{c[4]}"
        if new_state:
            self._selected_items.append(tag)
        else:
            self._selected_items.remove(tag)
        return


    def update_list(self):
        for idx in range(len(self._all_options)):
            c = self._all_options[idx]
            checkbox = self._checkboxes[idx]
            checkbox.set_label("\n  ".join([c[0], c[1]]))
            checkbox.set_state( f"{c[3]}:{c[4]}" in self._selected_items, do_callback=False )

    def randomize(self):
        random.shuffle(self._all_options)

        self._selected_items = []
        for idx in range(min(len(self._all_options), 3)):
            c = self._all_options[idx]
            self._selected_items.append(f"{c[3]}:{c[4]}")

        self.update_list()

    def __init__(self, word, pos, definition, all_options, selected):
        self._all_options = all_options
        self._selected_items = selected

        self.footer_text = ('foot', [
            f"{word} ({pos})    ",
            ('key', "r"), " select random  ",
            ('key', "s"), " save  ",
            ('key', "q"), " quit",
            ])

        title = f"{word} {pos}"


        body = []
        self._checkboxes = []
        for idx in range(len(all_options)):
            checkbox = urwid.CheckBox("")
            urwid.connect_signal(checkbox, 'change', self.item_chosen, idx)
            self._checkboxes.append(checkbox)
            body.append(checkbox)

        self.update_list()

        self.listbox = urwid.ListBox(urwid.SimpleFocusListWalker(body))

        self.definition = urwid.Text(definition)
        self.textbox = urwid.ListBox([self.definition])
        self.columns = urwid.Columns([(60, self.textbox), self.listbox], dividechars=3,
                focus_column=1)

        self.footer = urwid.AttrWrap(urwid.Text(self.footer_text), "foot")
        self.view = urwid.Frame(urwid.AttrWrap(self.columns, 'body'),
            footer=self.footer)


    def main(self):

        self.loop = urwid.MainLoop(self.view, self.palette,
            unhandled_input=self.unhandled_keypress)
        self.loop.run()
        return self._selected_items

    def unhandled_keypress(self, key):
        """Last resort for keypresses."""

        if key in ('q', 'Q'):
            self._selected_items = None
            raise urwid.ExitMainLoop()
        if key in ('s', 'S'):
            raise urwid.ExitMainLoop()
        if key in ('r', 'R'):
            self.randomize()
        return True


def format_def(item):

    results = []
    for pos in item:
        pos_tag = ""
        if len(item.keys()) > 1:
            pos_tag = f'{{{pos}}} '

        for tag in item[pos]:
            if len(results):
                results.append("\n")

            results.append(pos_tag)

            usage = item[pos][tag]

            if tag != "":
                results.append(f'[{tag}]: ')

            results.append(f'{usage}')

    return "".join(results)


def get_selection(word, pos):

    selected = []
    tag = f"{word}:{pos}"
    if tag in all_selections:
        selected = all_selections[tag]
    elif tag in default_selections:
        selected = default_selections[tag]

    selected_ids = sentences.itemtags_to_ids(selected)
    all_ids = selected_ids + [ x for x in sentences.get_all_sentence_ids(word, pos)['ids'] if x not in selected_ids ]
    all_options = sentences.get_sentences_from_ids(all_ids)

    definition = format_def(words.lookup(word, pos))
    return SentenceChooser(word, pos, definition, all_options, selected).main()

def save_selections():
    with open(args.outfile, "w") as outfile:
        csvwriter = csv.writer(outfile)
        for tag, ids in all_selections.items():
            if ids and len(ids):
                csvwriter.writerow( tag.split(":") + ids )




if os.path.isfile(args.outfile):
    with open(args.outfile) as infile:
        for line in infile:
            line = line.strip()
            if line.startswith("#"):
                continue
            word,pos,*selections = line.split(",")
            if len(selections):
                # Strip duplicates
                selections = list(dict.fromkeys(selections))
                tag = f"{word}:{pos}"
                all_selections[tag] = selections

default_selections = {}
all_items = []
if not args.infile:
    all_items.append( [args.word,args.pos] )

else:
    with open(args.infile) as infile:
        for line in infile:
            line = line.strip()
            if line.startswith("#"):
                continue
            word,pos,*selections = line.split(",")
            all_items.append( [word,pos] )
            if len(selections):
                # Strip duplicates
                selections = list(dict.fromkeys(selections))
                default_selections[f"{word}:{pos}"] = selections


for item in all_items:
    word = item[0]
    pos = item[1]

    selected = get_selection(word, pos)
    if selected is None:
        break

    all_selections[f"{word}:{pos}"] = list(selected)

save_selections()
