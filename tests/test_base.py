from cesspool.cli import _tokenize, _reconstruct_jsonpath


def test__reconstruct_jsonpath():
    dupa = _tokenize('{"a": [{"b":[]}, {"b":[{"c":"dshia"}]}]}')
    ee = _reconstruct_jsonpath(dupa, "dshia")
    assert(ee == "a[2].")
