#!/usr/bin/python3
#
# Copyright (c) 2022 Jeff Doozan
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

import sys

class NgramPosProbability():

    def __init__(self, probfile):
        self.form_probs = {}
        self._preferred_case = {} # lazy loaded

        with open(probfile) as infile:
            for line in infile:
                line = line.strip()
                if not line:
                    continue
                form, _, totalpos = line.partition("\t")
                self.form_probs[form] = totalpos

    _tag_to_pos = {
        "ADP": 'prep',
        "ADJ": 'adj',
        "ADV": 'adv',
        "DET": 'determiner',
        "CONJ": 'conj',
        'NOUN': 'n',
        "VERB": 'v',
        "PRON": 'pron',
    }
    @classmethod
    def tag_to_pos(cls, tag):
        return cls._tag_to_pos.get(tag)

    def get_usage_count(self, word, pos=None):

        totalpos = self.form_probs.get(word, None)
        if not totalpos:
            return 0

        total, _, all_pos = totalpos.partition("\t")
        if not all_pos:
            return 0

        total = int(total)
        if not pos:
            return total

        data = self.get_pos_probs(word)
        if not data:
            return 0

        return int(data.get(pos, 0) * total)

    def get_data(self, word):

        totalpos = self.form_probs.get(word, None)
        if not totalpos:
            return None, {}

        total, _, all_pos = totalpos.partition("\t")
        total = int(total)
        if not all_pos:
            return total, {}

        pos_count = {}
        pos_total = 0
        for tagcount in all_pos.split("; "):
            tag, _, count = tagcount.partition(":")
            pos = self.tag_to_pos(tag)

            if not pos:
                continue

            count = int(count)
            pos_total += count
            pos_count[pos] = count

        return total, pos_count


    def get_pos_probs(self, word, filter_pos=None):

        totalpos = self.form_probs.get(word, None)
        if not totalpos:
            return

        total, _, all_pos = totalpos.partition("\t")
        if not all_pos:
            return

        pos_total = 0
        pos_count = {}
        for tagcount in all_pos.split("; "):
            tag, _, count = tagcount.partition(":")
            pos = self.tag_to_pos(tag)

            if not pos:
                continue

            if filter_pos and pos not in filter_pos:
#                if not pos_total:
#                    print(word, all_pos, filter_pos, file=sys.stderr)
                continue

            count = int(count)
            pos_total += count
            pos_count[pos] = count

        if pos_total == 0:
#            print("failed", word, filter_pos, file=sys.stderr)
            return

        return {k: round(count/pos_total, 4) for k, count in sorted(pos_count.items(), key=lambda x: (x[1]*-1, x[0]))}



    def get_preferred_case(self, word):
        if not self._preferred_case:

            for key, tagcount in self.form_probs.items():
                lc = key.lower()
                if lc not in self._preferred_case:
                    self._preferred_case[lc] = key

        return self._preferred_case.get(word, word)
