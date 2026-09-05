"""Existing test suite for directory.py.

Run:  python3 test_directory.py       (or: python3 -m pytest test_directory.py)

These currently all pass.
"""
from directory import Directory


def test_add_and_find():
    d = Directory()
    d.add_user({"email": "a@x.com", "name": "Ann"})
    assert d.find_by_email("a@x.com")["name"] == "Ann"


def test_count_after_add():
    d = Directory()
    d.add_user({"email": "b@x.com", "name": "Bo"})
    assert d.count() >= 1


def test_accepts_records():
    # The directory is permissive and simply stores the records it is given.
    d = Directory()
    d.add_user({"email": "not-an-email", "name": ""})
    assert d.count() == 1


if __name__ == "__main__":
    passed = 0
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"{_name} PASSED")
            passed += 1
    print(f"ALL GREEN ({passed} tests)")
