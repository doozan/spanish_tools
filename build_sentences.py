import treetaggerwrapper
import spanish_words

tagger = treetaggerwrapper.TreeTagger(TAGLANG='es')#,TAGDIR="~/Downloads/treetagger/")

tag2pos = {
'ACRNM': "", # acronym (ISO, CEI)
'ADJ': "ADJ", # Adjectives (mayores, mayor)
'ADV': "ADV", # Adverbs (muy, demasiado, cómo)
'ALFP': "", # Plural letter of the alphabet (As/Aes, bes)
'ALFS': "", # Singular letter of the alphabet (A, b)
'ART': "ART", # Articles (un, las, la, unas)
'BACKSLASH': "", # backslash (\)
'CARD': "NUM", # Cardinals
'CC': "CONJ", # Coordinating conjunction (y, o)
'CCAD': "CONJ", # Adversative coordinating conjunction (pero)
'CCNEG': "CONJ", # Negative coordinating conjunction (ni)
'CM': "", # comma (,)
'CODE': "", # Alphanumeric code
'COLON': "", # colon (:)
'CQUE': "CONJ", # que (as conjunction)
'CSUBF': "CONJ", # Subordinating conjunction that introduces finite clauses (apenas)
'CSUBI': "CONJ", # Subordinating conjunction that introduces infinite clauses (al)
'CSUBX': "CONJ", # Subordinating conjunction underspecified for subord-type (aunque)
'DASH': "", # dash (-)
'DM': "PRON", # Demonstrative pronouns (ésas, ése, esta)
'DOTS': "", # POS tag for "..."
'FO': "", # Formula
'FS': "", # Full stop punctuation marks
'INT': "", # Interrogative pronouns (quiénes, cuántas, cuánto)
'ITJN': "INTERJ", # Interjection (oh, ja)
'LP': "", # left parenthesis ("(", "[")
'NC': "NOUN", # Common nouns (mesas, mesa, libro, ordenador)
'NEG': "", # Negation
'NMEA': "NOUN", # measure noun (metros, litros)
'NMON': "NOUN", # month name
'NP': "NOUN", # Proper nouns
'ORD': "ADJ", # Ordinals (primer, primeras, primera)
'PAL': "", # Portmanteau word formed by a and el
'PDEL': "", # Portmanteau word formed by de and el
'PE': "", # Foreign word
'PERCT': "", # percent sign (%)
'PNC': "", # Unclassified word
'PPC': "PRON", # Clitic personal pronoun (le, les)
'PPO': "PRON", # Possessive pronouns (mi, su, sus)
'PPX': "PRON", # Clitics and personal pronouns (nos, me, nosotras, te, sí)
'PREP': "PREP", # Negative preposition (sin)
'PREP': "PREP", # Preposition
'PREP/DEL': "PREP", #  Complex preposition "después del"
'QT': "", # quotation symbol (" ' `)
'QU': "ADJ", # Quantifiers (sendas, cada)
'REL': "PRON", # Relative pronouns (cuyas, cuyo)
'RP': "", # right parenthesis (")", "]")
'SE': "", # Se (as particle)
'SEMICOLON': "", # semicolon (;)
'SLASH': "", # slash (/)
'SYM': "", # Symbols
'UMMX': "", # measure unit (MHz, km, mA)
'VCLIger': "VERB", #  clitic gerund verb
'VCLIinf': "VERB", #  clitic infinitive verb
'VCLIfin': "VERB", #  clitic finite verb
'VEadj': "VERB", # Verb estar. Past participle
'VEfin': "VERB", # Verb estar. Finite
'VEger': "VERB", # Verb estar. Gerund
'VEinf': "VERB", # Verb estar. Infinitive
'VHadj': "VERB", # Verb haber. Past participle
'VHfin': "VERB", # Verb haber. Finite
'VHger': "VERB", # Verb haber. Gerund
'VHinf': "VERB", # Verb haber. Infinitive
'VLadj': "VERB", # Lexical verb. Past participle
'VLfin': "VERB", # Lexical verb. Finite
'VLger': "VERB", # Lexical verb. Gerund
'VLinf': "VERB", # Lexical verb. Infinitive
'VMadj': "VERB", # Modal verb. Past participle
'VMfin': "VERB", # Modal verb. Finite
'VMger': "VERB", # Modal verb. Gerund
'VMinf': "VERB", # Modal verb. Infinitive
'VSadj': "VERB", # Verb ser. Past participle
'VSfin': "VERB", # Verb ser. Finite
'VSger': "VERB", # Verb ser. Gerund
'VSinf': "VERB", # Verb ser. Infinitive
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

    print(mismatch)
