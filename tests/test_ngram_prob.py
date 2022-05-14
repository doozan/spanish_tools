import os
import pytest
from pytest import fixture

from ..ngram_prob import NgramPosProbability

@fixture
def ngram_prob(request):
    filename = request.module.__file__
    test_dir, _ = os.path.split(filename)
    return NgramPosProbability(os.path.join(test_dir, "test_ngram_prob.wordlist"))

def test_simple(ngram_prob):
    assert ngram_prob.get_pos_probs("de") == {'prep': 0.8683, 'n': 0.1259, 'adv': 0.0046, 'determiner': 0.0006, 'conj': 0.0004, 'v': 0.0002, 'adj': 0.0}

    assert ngram_prob.get_pos_probs("de", ["prep", "n", "v"]) == {'prep': 0.8732, 'n': 0.1266, 'v': 0.0002}

    assert ngram_prob.get_usage_count("de") == 3570503

    assert ngram_prob.get_usage_count("de", "n") == 449526
    assert int(3570503 * 0.1259) == 449526

    assert ngram_prob.get_usage_count("de", "v") == 714
