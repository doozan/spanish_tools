import spanish_words
import spanish_sentences
import get_best_pos

words = spanish_words.SpanishWords(dictionary="spanish_data/es-en.txt", synonyms="spanish_data/synonyms.txt", iverbs="spanish_data/irregular_verbs.txt")
sentences = spanish_sentences.sentences(words, "spanish_data/spa-tagged.txt")

test_words = {
"pesos": "noun",
"casa": "noun",
"bota": "noun",
"mira": "verb",
"era": "verb",
"anda": "verb",
"apenas": "adv",
"veras": "noun",
"adelanto": "noun",
"entendido": "verb",
"lamento": "verb",
"contento": "adj",
"placer": "noun",
"cuarto": "noun",
"partido": "noun",
"maestro": "noun",
"haz": "verb",
"sentido": "noun",
"asesino": "noun",
"drogas": "noun",
"salvo": "adv",
"alrededor": "adv",
"vete": "verb",
"rosa": "adj",
"noticias": "noun",
"doble": "adj",
"comida": "noun",
"chistes": "noun",
"alerta": "noun",
"ronda": "noun",
"agencia": "noun",
"mentiroso": "noun",
"mira": "verb",
}

matches = 0
for word,pos in test_words.items():
    res_pos = get_best_pos.get_best_pos(word, words, sentences, debug=False)
    if res_pos == pos:
        matches +=1
    else:
        print("%s should be %s [%s]"%(word,pos,res_pos))
print("%s/%s matched"%(matches, len(test_words.keys())))

