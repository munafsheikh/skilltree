"""Tests for skilltree models."""

import pytest

from skilltree.models import Scope, SemVer, Skill


class TestSemVer:
    def test_parse_basic(self):
        v = SemVer.parse("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_parse_with_v_prefix(self):
        v = SemVer.parse("v2.0.0")
        assert v.major == 2

    def test_parse_prerelease(self):
        v = SemVer.parse("1.0.0-alpha.1")
        assert v.prerelease == "alpha.1"

    def test_comparison(self):
        assert SemVer.parse("1.0.0") < SemVer.parse("2.0.0")
        assert SemVer.parse("1.0.0") == SemVer.parse("1.0.0")
        assert SemVer.parse("1.0.0-alpha") < SemVer.parse("1.0.0")

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            SemVer.parse("not-a-version")


class TestSkill:
    def test_has_update_when_installed_older(self):
        skill = Skill(
            id="test",
            name="Test",
            description="",
            scope=Scope.BUILT_IN,
            path=None,  # type: ignore[arg-type]
            version=SemVer.parse("2.0.0"),
            installed_version=SemVer.parse("1.0.0"),
        )
        assert skill.has_local_update()

    def test_no_update_when_equal(self):
        skill = Skill(
            id="test",
            name="Test",
            description="",
            scope=Scope.BUILT_IN,
            path=None,  # type: ignore[arg-type]
            version=SemVer.parse("1.0.0"),
            installed_version=SemVer.parse("1.0.0"),
        )
        assert not skill.has_local_update()
