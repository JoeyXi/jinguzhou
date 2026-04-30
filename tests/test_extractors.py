import pytest

from jinguzhou.policy.extractors import FieldPathError, resolve_field_path


def test_jsonpath_resolves_brackets_arrays_and_recursive_keys() -> None:
    payload = {
        "request": {
            "destinations": [
                {"url": "https://api.example.com"},
                {"url": "https://backup.example.com"},
            ]
        },
        "metadata": {"files": [{"path": "/tmp/a"}, {"path": "/tmp/b"}]},
        "literal.key": {"path": "/var/log/app.log"},
    }

    assert resolve_field_path(payload, "$.request.destinations[*].url") == [
        "https://api.example.com",
        "https://backup.example.com",
    ]
    assert resolve_field_path(payload, "$['literal.key'].path") == ["/var/log/app.log"]
    assert resolve_field_path(payload, "$..path") == [
        "/tmp/a",
        "/tmp/b",
        "/var/log/app.log",
    ]


def test_jsonpath_supports_negative_indexes_and_object_wildcards() -> None:
    payload = {
        "operations": [
            {"target": "/tmp/first"},
            {"target": "/etc/hosts"},
        ],
        "named": {
            "first": {"url": "https://one.example.com"},
            "second": {"url": "https://two.example.com"},
        },
    }

    assert resolve_field_path(payload, "$.operations[-1].target") == ["/etc/hosts"]
    assert resolve_field_path(payload, "$.named[*].url") == [
        "https://one.example.com",
        "https://two.example.com",
    ]


def test_jsonpath_reports_unclosed_brackets() -> None:
    with pytest.raises(FieldPathError):
        resolve_field_path({"request": {"url": "https://example.com"}}, "$.request[")
