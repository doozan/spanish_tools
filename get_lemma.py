import sys
import spanish_lemmas

if len(sys.argv) == 3:
    print(spanish_lemmas.get_lemma(sys.argv[1], sys.argv[2]))
else:
    print("Usage: %s <word> <pos>" % sys.argv[0])
