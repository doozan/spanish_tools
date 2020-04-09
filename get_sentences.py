import sys
import spanish_sentences

def format_sentences(sentences):
    return "\n".join('spa: %s\neng: %s' % pair[:2] for pair in sentences )

def get_sentences(lookup, pos, count):
    results = spanish_sentences.get_sentences(lookup, pos, count)

    if len(results['sentences']):
        print("Matched ", results['matched'])
        print( format_sentences(results['sentences']) )

    return ""

get_sentences(sys.argv[1], sys.argv[2], int(sys.argv[3]))
