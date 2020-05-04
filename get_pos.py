import sys
import argparse
import spanish_words
import spanish_sentences
import get_best_pos

parser = argparse.ArgumentParser(description='Guess most likely pos from word')
parser.add_argument('word', help="Word to get pos for")
parser.add_argument('--pos', nargs="+", type=str, help="space separated list of parts of speech to get best from")
args = parser.parse_args()

words = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt", synonyms="spanish_data/synonyms.txt")
sentences = spanish_sentences.sentences("spanish_data/sentences.json")

print(get_best_pos.get_best_pos(args.word, words, sentences, debug=True))
