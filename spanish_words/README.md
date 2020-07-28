This library is used to play with Spanish words.  Using the Wiktionary word database, it's pretty
good at guessing lemmas for nouns and adjectives and it can conjugate and reverse conjugate
Spanish verbs.

The conjugation paradigms are scraped from Wiktionary using the `build_paradigms.py` script:
```
./build_paradigms.py > paradigms.py
```
