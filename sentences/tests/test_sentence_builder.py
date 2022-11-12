import os
from pytest import fixture

from ..sentence_builder import SentenceBuilder, Phrase

from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms
from spanish_tools.freq import FrequencyList
from spanish_tools.freq import NgramPosProbability
from ngram.ngramdb import NgramDB

@fixture(scope="module")
def ngramdb(request):
    filename = request.module.__file__
    test_dir, _ = os.path.split(filename)

    ngramdb_filename = os.path.join(test_dir, "../../../ngram/spa/ngram-1950.db")
    return NgramDB(ngramdb_filename)

@fixture(scope="module")
def wordlist(request):
    filename = request.module.__file__
    test_dir, _ = os.path.split(filename)

#    wordlist_filename = os.path.join(test_dir, "es-en.data")
    wordlist_filename = os.path.join(test_dir, "../../../spanish_data/es-en.data")
    return Wordlist.from_file(wordlist_filename)

@fixture(scope="module")
def allforms(request):
    filename = request.module.__file__
    test_dir, _ = os.path.split(filename)

    allforms_filename = os.path.join(test_dir, "../../../spanish_data/es_allforms.csv")
    return AllForms.from_file(allforms_filename)

@fixture(scope="module")
def ngprobs(request):
    filename = request.module.__file__
    test_dir, _ = os.path.split(filename)

    ngprobs_filename = os.path.join(test_dir, "../../../ngram/es-1-1950.ngprobs")
    ngcase_filename = os.path.join(test_dir, "../../../ngram/es-1-1950.ngcase")
    return NgramPosProbability(ngprobs_filename, ngcase_filename)


@fixture(scope="module")
def freq(wordlist, allforms, ngprobs):
    return FrequencyList(wordlist, allforms, ngprobs)


@fixture(scope="module")
def builder(request, allforms, freq, ngramdb):
    filename = request.module.__file__
    test_dir, _ = os.path.split(filename)

#    print(len(allforms.all))
#    exit()

    builder = SentenceBuilder(allforms, freq, ngramdb)

    return builder



# --dictionary ../spanish_data/es-en.data        --allforms ../spanish_data/es_allforms.csv        --ngprobs ../spanish_data/es-1-1950.ngprobs        --tags ../spanish_data/spa-only.txt.json --ngramdb ../deck/ngram.db        ../spanish_data/eng-spa.tsv 

def test_has_interjection():

    assert SentenceBuilder.has_interjection("caray", "blah, caray!") == True
    assert SentenceBuilder.has_interjection("caray", "caray, blah") == True
    assert SentenceBuilder.has_interjection("caray", "blah caray blah") == False
    assert SentenceBuilder.has_interjection("caray", "blah caray, blah") == False
    assert SentenceBuilder.has_interjection("caray", "blah caray") == False
    assert SentenceBuilder.has_interjection("caray", "caray blah") == False

def test_get_phrases(builder):

    # Should match "gracias a Dios" but not the embedded "gracias a"
    assert builder.get_phrases("Gracias a Dios, por fin llegaron.") == [
            Phrase(form='gracias a dios', lemma='Gracias a Dios', start=0, end=15),
            Phrase(form='por fin', lemma='por fin', start=15, end=23)
            ]
   # [Phrase(text='gracias a dios', start=0, end=15), Phrase(text='por fin', start=15, end=23)]

    # Should not match "El Hierro" because of the case difference
    assert builder.get_phrases("El Hierro conduce bien el calor.") == [Phrase(form='el hierro', lemma='El Hierro', start=0, end=9)] 
    assert builder.get_phrases("El hierro conduce bien el calor.") == []

    assert builder.get_phrases("Iré afuera a ver los fuegos artificiales.") == [
            Phrase(form='a ver', lemma='a ver', start=10, end=16),
            Phrase(form='fuegos artificiales', lemma='fuego artificial', start=20, end=41)]

def test_get_lemmas(ngprobs):

    assert ngprobs.get_preferred_case("dios") == "XX"
#    assert builder.get_lemmas("dios", "n") == "XX"

def test_get_sentence():
    line = "For God's sake!\t¡Por el amor de Dios!\tCC-BY 2.0 (France) Attribution: tatoeba.org #863686 (cris) & #863699 (washisnein)\t0\t0"
    sentence = SentenceBuilder.get_sentence(line)

    assert sentence.english == "For God's sake!"
    assert sentence.spanish == "¡Por el amor de Dios!"
    assert sentence.credits == "CC-BY 2.0 (France) Attribution: tatoeba.org #863686 (cris) & #863699 (washisnein)"
    assert sentence.eng_score == 0
    assert sentence.eng_id == 863686
    assert sentence.eng_user == "cris"
    assert sentence.spa_score == 0
    assert sentence.spa_id == 863699
    assert sentence.spa_user == "washisnein"


def test_get_sentence_tags(builder):

    line = "Will God forgive us?\t¿Dios nos va a perdonar?\tCC-BY 2.0 (France) Attribution: tatoeba.org #6372690 (OsoHombre) & #9150720 (rafaeldejesus8199)\t4\t5"
    tag_data = [{ "id":"9638",
        "tokens" : [
           { "id" : "t9638.1", "begin" : "286854", "end" : "286855", "form" : "¿", "lemma" : "¿", "tag" : "Fia", "ctag" : "Fia", "pos" : "punctuation", "type" : "questionmark", "punctenclose" : "open"},
           { "id" : "t9638.2", "begin" : "286855", "end" : "286859", "form" : "Dios", "lemma" : "dios", "tag" : "NCMS000", "ctag" : "NC", "pos" : "noun", "type" : "common", "gen" : "masculine", "num" : "singular"},
           { "id" : "t9638.3", "begin" : "286860", "end" : "286863", "form" : "nos", "lemma" : "nos", "tag" : "PP1CP00", "ctag" : "PP", "pos" : "pronoun", "type" : "personal", "person" : "1", "gen" : "common", "num" : "plural"},
           { "id" : "t9638.4", "begin" : "286864", "end" : "286866", "form" : "va", "lemma" : "ir", "tag" : "VMIP3S0", "ctag" : "VMI", "pos" : "verb", "type" : "main", "mood" : "indicative", "tense" : "present", "person" : "3", "num" : "singular"},
           { "id" : "t9638.5", "begin" : "286867", "end" : "286868", "form" : "a", "lemma" : "a", "tag" : "SP", "ctag" : "SP", "pos" : "adposition", "type" : "preposition"},
           { "id" : "t9638.6", "begin" : "286869", "end" : "286877", "form" : "perdonar", "lemma" : "perdonar", "tag" : "VMN0000", "ctag" : "VMN", "pos" : "verb", "type" : "main", "mood" : "infinitive"},
           { "id" : "t9638.7", "begin" : "286877", "end" : "286878", "form" : "?", "lemma" : "?", "tag" : "Fit", "ctag" : "Fit", "pos" : "punctuation", "type" : "questionmark", "punctenclose" : "close"}
           ]}]
    expected_tags = {'prop': ['Dios'], 'pron': ['nos'], 'v': ['va|ir', 'perdonar'], 'prep': ['a']}

    sentence = builder.get_sentence(line)
    res = builder.get_sentence_tags(sentence, tag_data)
    print(res)
    assert res == expected_tags

    line = "For God's sake!\t¡Por el amor de Dios!\tCC-BY 2.0 (France) Attribution: tatoeba.org #863686 (cris) & #863699 (washisnein)\t0\t0"
    tag_data = [
      {
        "tokens" : [
           { "id" : "t329.1", "begin" : "9581", "end" : "9582", "form" : "¡", "lemma" : "¡", "tag" : "Faa", "ctag" : "Faa", "pos" : "punctuation", "type" : "exclamationmark", "punctenclose" : "open"},
           { "id" : "t329.2", "begin" : "9582", "end" : "9585", "form" : "Por", "lemma" : "por", "tag" : "SP", "ctag" : "SP", "pos" : "adposition", "type" : "preposition"},
           { "id" : "t329.3", "begin" : "9586", "end" : "9588", "form" : "el", "lemma" : "el", "tag" : "DA0MS0", "ctag" : "DA", "pos" : "determiner", "type" : "article", "gen" : "masculine", "num" : "singular"},
           { "id" : "t329.4", "begin" : "9589", "end" : "9593", "form" : "amor", "lemma" : "amor", "tag" : "NCMS000", "ctag" : "NC", "pos" : "noun", "type" : "common", "gen" : "masculine", "num" : "singular"},
           { "id" : "t329.5", "begin" : "9594", "end" : "9596", "form" : "de", "lemma" : "de", "tag" : "SP", "ctag" : "SP", "pos" : "adposition", "type" : "preposition"},
           { "id" : "t329.6", "begin" : "9597", "end" : "9601", "form" : "Dios", "lemma" : "dios", "tag" : "NP00SP0", "ctag" : "NP", "pos" : "noun", "type" : "proper", "neclass" : "person", "nec" : "PER"},
           { "id" : "t329.7", "begin" : "9601", "end" : "9602", "form" : "!", "lemma" : "!", "tag" : "Fat", "ctag" : "Fat", "pos" : "punctuation", "type" : "exclamationmark", "punctenclose" : "close"}]
      }]
    expected_tags = {'phrase-prep': ['por', 'de'], 'phrase-art': ['el'], 'phrase-n': ['amor'], 'phrase-prop': ['Dios'], 'interj': ['por el amor de dios|por el amor de Dios']}

    sentence = builder.get_sentence(line)
    res = builder.get_sentence_tags(sentence, tag_data)
    print(res)
    assert res == expected_tags

def test_get_lemmas(builder):

#        lemmas = sorted(set(w.word for w in self.freq.get_preferred_lemmas(word, None, pos)))
#    lemmas = builder.freq.get_preferred_lemmas("abierta", None, "part")
    lemmas = builder.freq.get_preferred_lemmas("abierta", None, "v")
    print(len(lemmas))
    print([(w.word, w.pos) for w in lemmas])
    assert builder.get_lemmas("abierta", "part") == "abrir"
    assert builder.get_lemmas("ido", "part") == "ir"

