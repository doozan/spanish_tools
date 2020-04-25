import sys
import spanish_words
import argparse

parser = argparse.ArgumentParser(description='Get lemma from word and pos')
parser.add_argument('word', help="Word to get lemma for")
parser.add_argument('pos', nargs="?", default="", help="part of speech")
args = parser.parse_args()

words = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt", synonyms="spanish_data/synonyms.txt", iverbs="spanish_data/irregular_verbs.txt")

print(words.get_lemma(args.word, args.pos.lower()))
