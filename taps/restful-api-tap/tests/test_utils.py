"""Tests for tap utils: flatten_json used when preparing stream records (e.g. for schema inference)."""

import json

from restful_api_tap.utils import flatten_json


def test_flatten_json():
    """flatten_json flattens nested dicts for stream record payloads; except_keys preserve JSON strings."""
    d = {
        "a": 1,
        "b": {"a": 2, "b": {"a": 3}, "c": {"a": "bacon", "b": "yum"}},
        "c": [{"foo": "bar"}, {"eggs": "spam"}],
        "d": [4, 5],
        "e.-f": 6,
    }
    ret = flatten_json(d, except_keys=["b_c"])
    assert ret["a"] == 1
    assert ret["b_a"] == 2
    assert ret["b_b_a"] == 3
    assert ret["b_c"] == json.dumps({"a": "bacon", "b": "yum"})
    assert ret["c"] == json.dumps([{"foo": "bar"}, {"eggs": "spam"}])
    assert ret["d"] == json.dumps([4, 5])
    assert ret["e__f"] == 6
