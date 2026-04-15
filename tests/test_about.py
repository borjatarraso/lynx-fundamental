"""Tests for about information — centralized source, consistency across modes."""

import pytest
from lynx import (
    LICENSE_TEXT,
    __author__,
    __author_email__,
    __license__,
    __version__,
    __year__,
    get_about_text,
)


class TestAboutMetadata:
    def test_version_format(self):
        parts = __version__.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_author(self):
        assert __author__ == "Borja Tarraso"

    def test_author_email(self):
        assert __author_email__ == "borja.tarraso@member.fsf.org"
        assert "@" in __author_email__

    def test_license(self):
        assert __license__ == "BSD-3-Clause"

    def test_year(self):
        assert __year__.isdigit()
        assert int(__year__) >= 2026


class TestGetAboutText:
    def test_returns_dict(self):
        about = get_about_text()
        assert isinstance(about, dict)

    def test_required_keys(self):
        about = get_about_text()
        required_keys = {"name", "version", "author", "email", "year", "license", "license_text", "description"}
        assert required_keys.issubset(about.keys())

    def test_values_match_module_attrs(self):
        about = get_about_text()
        assert about["version"] == __version__
        assert about["author"] == __author__
        assert about["email"] == __author_email__
        assert about["year"] == __year__
        assert about["license"] == __license__

    def test_license_text_content(self):
        about = get_about_text()
        lt = about["license_text"]
        assert "BSD 3-Clause License" in lt
        assert "Borja Tarraso" in lt
        assert "borja.tarraso@member.fsf.org" in lt
        assert "Redistribution and use" in lt
        assert "WITHOUT WARRANTY" not in lt or "AS IS" in lt

    def test_description_nonempty(self):
        about = get_about_text()
        assert len(about["description"]) > 20


class TestLicenseText:
    def test_bsd_three_clause_structure(self):
        assert "1." in LICENSE_TEXT
        assert "2." in LICENSE_TEXT
        assert "3." in LICENSE_TEXT

    def test_disclaimer(self):
        assert "AS IS" in LICENSE_TEXT
        assert "WITHOUT WARRANTY" not in LICENSE_TEXT or "AS IS" in LICENSE_TEXT
        assert "DISCLAIMED" in LICENSE_TEXT

    def test_copyright_holder(self):
        assert "Borja Tarraso" in LICENSE_TEXT
        assert "borja.tarraso@member.fsf.org" in LICENSE_TEXT
