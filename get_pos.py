import sys
import argparse
import get_best_pos

parser = argparse.ArgumentParser(description='Guess most likely pos from word')
parser.add_argument('word', help="Word to get pos for")
parser.add_argument('--pos', nargs="+", type=str, help="space separated list of parts of speech to get best from")
args = parser.parse_args()

print(get_best_pos.get_best_pos(args.word, debug=True))
