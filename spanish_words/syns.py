import re

all_syns = {}

with open("data_dict1.txt", encoding="ISO-8859-1") as infile:
    for line in infile:

        spanish,english = line.split(":")
        if "/" not in spanish and ";" not in spanish:
            continue

        spanish = spanish.lower()
        spanish = re.sub(r"\[.*\]", "", spanish)
        spanish = re.sub(r"\(.*\)", "", spanish)
        spanish = re.sub(";", "/", spanish)

        word_syns = spanish.split("/")

        for word in word_syns:
            word = word.strip()
            if not re.match("^[a-zA-ZáéíñóúüÁÉÍÑÓÚÜ]{2,}$", word):
                continue
            if word not in all_syns:
                all_syns[word] = []
            for syn in word_syns:
                syn = syn.strip()
                if re.match("^[a-zA-ZáéíñóúüÁÉÍÑÓÚÜ]{2,}$", syn):
                    all_syns[word].append(syn)

with open("syns.txt", "w") as outfile:
    for k in sorted(all_syns.keys()):
        syns = set(all_syns[k])
        syns.remove(k)
        if len(syns):
            outfile.write("%s: %s\n"%(k, "/".join(sorted(syns))))
