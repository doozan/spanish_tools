import json

"""
convertir {{es-conj-ir|conv|rt|p=e-ie-i|combined=1}}
adquirir {{es-conj-ir|p=i-ie|adqu|r|combined=1}}
inquirir {{es-conj-ir|p=i-ie|inqu|r|combined=1}}
perquirir {{es-conj-ir|p=i-ie|perqu|r}}
readquirir {{es-conj-ir|p=i-ie|readqu|r|combined=1}}
cohibir {{es-conj-ir|p=i-í|coh|b|combined=1}}
prohibir {{es-conj-ir|p=i-í|proh|b|combined=1}}
adormir {{es-conj-ir|p=o-ue|ad|rm|combined=1}}
desmorir {{es-conj-ir|p=morir|desm|r}}
dormir {{es-conj-ir|p=o-ue|d|rm|combined=1}}
"""

def parse_template(word, template):
    template = template[2:-2]
    params = template.split("|")

    item = {
        'verb': word,
#        'ending': params[0][len("es-conj"):],
        'pattern': "",
        'stems': []
    }

    for param in params[1:]:
        if "=" in param:
            if param.startswith("p="):
                item['pattern'] = param[2:]
        else:
            item['stems'].append(param)

#    guess = "-"+word[-4:-2] if word.endswith("se") else "-"+word[-2:]
#    if guess != item['ending']:
#        print("Ending mismatch: guessed %s, but template says %s"%(guess, item['ending']))

    if item['pattern'].startswith("-"):
        return
    if item['pattern'] == word:
        return
    if word.startswith("-"):
        return

    print(item)

with open("irregular_verbs.json") as infile:
    data = json.load(infile)
    for k,v in data.items():
        if 'template' in v:
            parse_template(k, v['template'])
