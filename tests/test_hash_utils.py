import json

from abqpilot.core.hash_utils import canonical_json, sha256_file, sha256_json_obj


def test_sha256_file_is_deterministic(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("abc", encoding="utf-8")

    assert sha256_file(path) == sha256_file(path)


def test_sha256_json_obj_is_deterministic_despite_key_order():
    left = {"b": 2, "a": {"d": 4, "c": 3}}
    right = {"a": {"c": 3, "d": 4}, "b": 2}

    assert canonical_json(left) == canonical_json(right)
    assert sha256_json_obj(left) == sha256_json_obj(right)


def test_sha256_json_obj_can_exclude_volatile_keys():
    left = {"status": "OK", "created_at": "one", "nested": {"updated_at": "two", "value": 1}}
    right = {"status": "OK", "created_at": "other", "nested": {"updated_at": "other", "value": 1}}

    assert sha256_json_obj(left, exclude_keys={"created_at", "updated_at"}) == sha256_json_obj(
        right, exclude_keys={"created_at", "updated_at"}
    )
    assert json.loads(canonical_json(left, exclude_keys={"created_at", "updated_at"})) == {
        "nested": {"value": 1},
        "status": "OK",
    }
