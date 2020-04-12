import sys
import spanish_dictionary

def pretty_print(word, item):
    for pos in item:
        print("==========================")
        print("%s (%s)"%(word, pos))

        for tag in item[pos]:
            defs = spanish_dictionary.get_best_defs(item[pos][tag],4)
            usage = spanish_dictionary.defs_to_string(defs, pos)

            if tag == "x":
                print(usage)
            else:
                print("%s: %s" % (tag, usage))
    print("==========================")


if len(sys.argv) == 2:
    result = spanish_dictionary.lookup(sys.argv[1])
    pretty_print(sys.argv[1], result)
elif len(sys.argv) == 3:
    result = spanish_dictionary.lookup(sys.argv[1], sys.argv[2])
    pretty_print(sys.argv[1], result)
else:
    print("Usage: %s <query> [pos]" % sys.argv[0])
