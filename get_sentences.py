import sys
import spanish_words
import spanish_sentences
import argparse

parser = argparse.ArgumentParser(description='Get sentences that contain variations of specified word')
parser.add_argument('word', help="Word to search for")
parser.add_argument('pos', nargs="?", default="", help="part of speech")
parser.add_argument('count', nargs="?", default=3, type=int, help="Max sentences to retrieve")
args = parser.parse_args()

words = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt", synonyms="spanish_data/synonyms.txt", iverbs="spanish_data/irregular_verbs.txt")
spanish_sentences = spanish_sentences.sentences(words, "spanish_data/spa-tagged.txt")

def format_sentences(sentences):
    return "\n".join('spa: %s\neng: %s' % pair[:2] for pair in sentences )

def get_sentences(lookup, pos, count):
    results = spanish_sentences.get_sentences(lookup, pos, count)

    if len(results['sentences']):
        print("Matched ", results['matched'])
        print( format_sentences(results['sentences']) )

    return ""

get_sentences(args.word, args.pos, args.count)
