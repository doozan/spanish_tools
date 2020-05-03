import re
import sys
import os

class SpanishSynonyms:
    def __init__(self, datafile=None):
        self.allsyns = {}
        if datafile:
            self.load_data(datafile)

    def load_data(self, datafile):
        if not os.path.isfile(datafile):
            raise FileNotFoundError(f"Cannot open synonyms: '{datafile}'")

        with open(datafile) as infile:
            for line in infile:
                word, syns = line.split(':')
                syns = syns.strip()
                self.allsyns[word] = syns # syns.split('/')


    def get_synonyms(self, word):
        if word in self.allsyns and self.allsyns[word]:
            return self.allsyns[word].split('/')
        else:
            return []
