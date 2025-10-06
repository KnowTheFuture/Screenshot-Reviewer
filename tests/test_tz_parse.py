"""Timezone parsing tests for screenshot_enricher.parse_iso_utc."""

from datetime import UTC

from screenshot_enricher import parse_iso_utc


def test_naive_and_aware():
    naive = "2025-10-04T19:45:52.526079"
    aware = "2025-10-04T19:45:52.526079+00:00"
    assert parse_iso_utc(naive).tzinfo is UTC
    assert parse_iso_utc(aware).tzinfo is UTC
    assert parse_iso_utc(naive) == parse_iso_utc(aware)
