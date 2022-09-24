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

    ngramdb_filename = os.path.join(test_dir, "../../../ngram/spa/ngram.db")
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
    assert builder.get_phrases("El hierro conduce bien el calor.") == []

    assert builder.get_phrases("Iré afuera a ver los fuegos artificiales.") == [
            Phrase(form='a ver', lemma='a ver', start=10, end=16),
            Phrase(form='fuegos artificiales', lemma='fuego artificial', start=20, end=41)]
