import treetaggerwrapper
import spanish_words

tagger = treetaggerwrapper.TreeTagger(TAGLANG='es')#,TAGDIR="~/Downloads/treetagger/")

tag2pos = {
'ACRNM': "", # acronym (ISO, CEI)
'ADJ': "adj", # Adjectives (mayores, mayor)
'ADV': "adv", # Adverbs (muy, demasiado, cómo)
'ALFP': "", # Plural letter of the alphabet (As/Aes, bes)
'ALFS': "", # Singular letter of the alphabet (A, b)
'ART': "art", # Articles (un, las, la, unas)
'BACKSLASH': "", # backslash (\)
'CARD': "num", # Cardinals
'CC': "conj", # Coordinating conjunction (y, o)
'CCAD': "conj", # Adversative coordinating conjunction (pero)
'CCNEG': "conj", # Negative coordinating conjunction (ni)
'CM': "", # comma (,)
'CODE': "", # Alphanumeric code
'COLON': "", # colon (:)
'CQUE': "conj", # que (as conjunction)
'CSUBF': "conj", # Subordinating conjunction that introduces finite clauses (apenas)
'CSUBI': "conj", # Subordinating conjunction that introduces infinite clauses (al)
'CSUBX': "conj", # Subordinating conjunction underspecified for subord-type (aunque)
'DASH': "", # dash (-)
'DM': "pron", # Demonstrative pronouns (ésas, ése, esta)
'DOTS': "", # POS tag for "..."
'FO': "", # Formula
'FS': "", # Full stop punctuation marks
'INT': "", # Interrogative pronouns (quiénes, cuántas, cuánto)
'ITJN': "interj", # Interjection (oh, ja)
'LP': "", # left parenthesis ("(", "[")
'NC': "noun", # Common nouns (mesas, mesa, libro, ordenador)
'NEG': "", # Negation
'NMEA': "noun", # measure noun (metros, litros)
'NMON': "noun", # month name
'NP': "noun", # Proper nouns
'ORD': "adj", # Ordinals (primer, primeras, primera)
'PAL': "", # Portmanteau word formed by a and el
'PDEL': "", # Portmanteau word formed by de and el
'PE': "", # Foreign word
'PERCT': "", # percent sign (%)
'PNC': "", # Unclassified word
'PPC': "pron", # Clitic personal pronoun (le, les)
'PPO': "pron", # Possessive pronouns (mi, su, sus)
'PPX': "pron", # Clitics and personal pronouns (nos, me, nosotras, te, sí)
'PREP': "prep", # Negative preposition (sin)
'PREP': "prep", # Preposition
'PREP/DEL': "prep", #  Complex preposition "después del"
'QT': "", # quotation symbol (" ' `)
'QU': "adj", # Quantifiers (sendas, cada)
'REL': "pron", # Relative pronouns (cuyas, cuyo)
'RP': "", # right parenthesis (")", "]")
'SE': "", # Se (as particle)
'SEMICOLON': "", # semicolon (;)
'SLASH': "", # slash (/)
'SYM': "", # Symbols
'UMMX': "", # measure unit (MHz, km, mA)
'VCLIger': "verb", #  clitic gerund verb
'VCLIinf': "verb", #  clitic infinitive verb
'VCLIfin': "verb", #  clitic finite verb
'VEadj': "verb", # Verb estar. Past participle
'VEfin': "verb", # Verb estar. Finite
'VEger': "verb", # Verb estar. Gerund
'VEinf': "verb", # Verb estar. Infinitive
'VHadj': "verb", # Verb haber. Past participle
'VHfin': "verb", # Verb haber. Finite
'VHger': "verb", # Verb haber. Gerund
'VHinf': "verb", # Verb haber. Infinitive
'VLadj': "verb", # Lexical verb. Past participle
'VLfin': "verb", # Lexical verb. Finite
'VLger': "verb", # Lexical verb. Gerund
'VLinf': "verb", # Lexical verb. Infinitive
'VMadj': "verb", # Modal verb. Past participle
'VMfin': "verb", # Modal verb. Finite
'VMger': "verb", # Modal verb. Gerund
'VMinf': "verb", # Modal verb. Infinitive
'VSadj': "verb", # Verb ser. Past participle
'VSfin': "verb", # Verb ser. Finite
'VSger': "verb", # Verb ser. Gerund
'VSinf': "verb", # Verb ser. Infinitive
}


mismatch = {}

def tag_to_pos(tag):

    if "\t" not in tag:
        return "__BADTAG__" #+tag+"-__"

    word,usage,oldlemma = tag.split("\t")

    pos = tag2pos[usage]
    if pos:
        pos = pos.lower()
        lemma = spanish_words.get_lemma(word, pos)
        if oldlemma != lemma:
            mismatch[oldlemma] = lemma

        return pos+":"+lemma+"|@"+word


def clean(spanish):
    return spanish.lower()

def get_tags(spanish):
    tags = tagger.tag_text(spanish)
#    print(tags)
    pos_tags = map(tag_to_pos, tags)
    good_tags = [ t for t in pos_tags if t ]
    return good_tags

with open("spa.txt") as infile:
    seen = {}
    for line in infile:
        line = line.strip()
        english, spanish, credits = line.split("\t")
        tags = get_tags(clean(spanish))
        if "__BADTAG__" in tags:
            continue

        words = spanish.count(" ")+1

        # ignore simple sentences
        if len(tags) < 2:
            continue

        # ignore sentences with less than 6 or more than 15 spanish words
        if words < 5 or words > 15:
            continue

        # ignore duplicates
        if english in seen or spanish in seen:
            continue
        else:
            seen[english] = 1
            seen[spanish] = 1

        # ignore sentences with the same adj/adv/noun/verb combination
        unique_tags = [t for t in tags if t[0] in ["a", "n", "v" ]]
        uniqueid = ":".join(sorted(unique_tags))
        if uniqueid in seen:
            continue
        seen[uniqueid] = 1

        spanish_tagged = " ".join(tags)
        print("%s\t%s\t%s\t%s"%(english, spanish, spanish_tagged, credits))

#    print(mismatch)
