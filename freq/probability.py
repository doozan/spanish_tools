#!/usr/bin/python3
#
# Copyright (c) 2021 Jeff Doozan
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Parses a FreeLing probabilitats.dat XML file

class PosProbability():

    def __init__(self, probfile):
        self.form_probs = {}
        self.suffix_probs = {}

        inSuffix = False
        inForm = False

        with open(probfile) as infile:
            for line in infile:
                if line.startswith("<"):
                    if line.startswith("</"):
                        inSuffix = False
                        inForm = False
                    elif line.startswith("<Suffixes"):
                        inSuffix = True
                    elif line.startswith("<FormTagFreq"):
                        inForm = True

                elif inSuffix:
                    word, total, *items = line.strip().split(" ")
                    self.suffix_probs[word] = items

                elif inForm:
                    word, types, *items = line.strip().split(" ")
                    self.form_probs[word] = items


    @staticmethod
    def tag_to_pos(tag):
        if tag.startswith("A"):
            return "adj"
        if tag.startswith("C"):
            return "conj"
        if tag.startswith("D"):
            return "art"
        if tag.startswith("I"):
            return "intj"
        if tag.startswith("NC"):
            return "n"
        if tag.startswith("NP"):
            return "prop"
        if tag.startswith("P"):
            return "pron"
        if tag.startswith("R"):
            return "adv"
        if tag.startswith("S"):
            return "prep"
        if tag.startswith("V"):
            if tag.startswith("VMP"):
                return "part"
            return "v"
        if tag.startswith("W"):
            return "num"
        if tag.startswith("Z"):
            return "num"

    def get_pos_probs(self, word, filter_pos=None):

        if word in self.form_probs:
            it = iter(self.form_probs[word])

        else:
            while word and word not in self.suffix_probs:
                word = word[1:]

            if not word:
#                print("no match", word)
                return []

            it = iter(self.suffix_probs[word])

        data = {}
        total = 0
        for tag in it:
            weight = int(next(it))
            tag_pos = self.tag_to_pos(tag)

            if not tag_pos:
#                print("unexpected tag", tag, self.form_probs[word], file=sys.stderr)
                #raise ValueError("unexpected tag", tag, self.form_probs[word])
                continue

            pos_list = ["v","adj","n"] if tag_pos == "part" else [tag_pos]
            for pos in pos_list:
                if filter_pos and pos not in filter_pos:
                    continue
                total += weight
                data[pos] = data.get(pos,0) + weight

        if total == 0:
#            print("failed", word, filter_pos, file=sys.stderr)
            return []

        return [ (form, count) for form,count in sorted(data.items(), key=lambda x: (x[1]*-1, x[0])) ]
        #return {k: count/total for k,count in sorted(data.items(), key=lambda x: (x[1]*-1, x[0]))}
