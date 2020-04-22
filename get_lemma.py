import sys
#import spanish_lemmas
import spanish_words
import argparse

parser = argparse.ArgumentParser(description='Get lemma from word and pos')
parser.add_argument('word', help="Word to get lemma for")
parser.add_argument('pos', nargs="?", default="", help="part of speech")
args = parser.parse_args()

#print(spanish_lemmas.get_lemma(args.word, args.pos.lower()))
print(spanish_words.get_lemma(args.word, args.pos.lower()))
