"""Tests for origin tracking and update checking."""

from pathlib import Path

import pytest

from skilltree.models import OriginType, Scope, SemVer, Skill
from skilltree.origins import (
    EmbeddedOriginChecker,
    LocalOriginChecker,
    check_skill_origin,
)
from skilltree.registry import RegistryConfig, SkillRegistry


@pytest.fixture
def embedded_skill() -> Skill:
    return Skill(
        id="test-embedded",
        name="Test Embedded",
        description="",
        scope=Scope.BUILT_IN,
        path=Path("/dev/null"),  # type: ignore[arg-type]
        version=SemVer.parse("1.0.0"),
        origin_type=OriginType.EMBEDDED,
        origin="embedded",
    )


@pytest.fixture
def local_skill(tmp_path: Path) -> Skill:
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    manifest = skill_dir / "SKILL.md"
    manifest.write_text("# My Skill\n", encoding="utf-8")
    return Skill(
        id="test-local",
        name="Test Local",
        description="",
        scope=Scope.USER,
        path=skill_dir,
        version=SemVer.parse("1.0.0"),
        origin_type=OriginType.LOCAL,
        origin=str(skill_dir),
        content_hash="abc123",
    )


class TestEmbeddedOriginChecker:
    async def test_embedded_is_always_up_to_date(self, embedded_skill: Skill):
        checker = EmbeddedOriginChecker()
        result = await checker.check(embedded_skill)
        assert result.is_accessible
        assert not result.is_outdated
        assert result.remote_version == embedded_skill.version


class TestLocalOriginChecker:
    async def test_local_up_to_date_when_hash_matches(self, local_skill: Skill):
        checker = LocalOriginChecker()
        result = await checker.check(local_skill)
        assert result.is_accessible
        # Hash won't match because we set a fake content_hash
        assert result.is_outdated

    async def test_local_not_accessible_when_missing(self):
        skill = Skill(
            id="missing",
            name="Missing",
            description="",
            scope=Scope.USER,
            path=Path("/nonexistent"),  # type: ignore[arg-type]
            origin_type=OriginType.LOCAL,
            origin="/nonexistent",
        )
        checker = LocalOriginChecker()
        result = await checker.check(skill)
        assert not result.is_accessible


class TestCheckSkillOrigin:
    async def test_check_embedded(self, embedded_skill: Skill):
        result = await check_skill_origin(embedded_skill)
        assert result.skill_id == embedded_skill.id
        assert result.origin_type == OriginType.EMBEDDED
        assert not result.is_outdated


class TestRegistryOriginState:
    def test_load_origin_state(self, tmp_path: Path):
        built_in = tmp_path / "built-in"
        built_in.mkdir()
        skill_dir = built_in / "example"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: Example\n"
            "description: Test\n"
            "version: 1.0.0\n"
            "origin_type: git\n"
            "origin: https://example.com/repo.git\n"
            "origin_ref: main\n"
            "---\n",
            encoding="utf-8",
        )
        cfg = RegistryConfig()
        cfg.roots = {Scope.BUILT_IN: [], Scope.EXTRA: [], Scope.USER: [built_in], Scope.PROJECT: []}
        reg = SkillRegistry(cfg)
        reg.scan()

        skill = reg.get("example")
        assert skill is not None
        assert skill.origin_type == OriginType.GIT
        assert skill.origin == "https://example.com/repo.git"
        assert skill.origin_ref == "main"

    def test_origin_state_persistence(self, tmp_path: Path):
        built_in = tmp_path / "built-in"
        built_in.mkdir()
        skill_dir = built_in / "example"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: Example\ndescription: Test\nversion: 1.0.0\n---\n",
            encoding="utf-8",
        )
        cfg = RegistryConfig()
        cfg.roots = {Scope.BUILT_IN: [built_in], Scope.EXTRA: [], Scope.USER: [], Scope.PROJECT: []}
        reg = SkillRegistry(cfg)
        reg.scan()

        state_path = tmp_path / "origins.json"
        skill = reg.get("example")
        assert skill is not None
        skill.remote_version = SemVer.parse("2.0.0")
        skill.remote_hash = "deadbeef"
        skill.is_outdated = True
        from datetime import datetime, timezone

        skill.last_checked = datetime.now(timezone.utc)

        reg.save_origin_state(state_path)
        assert state_path.exists()

        reg2 = SkillRegistry(cfg)
        reg2.scan()
        reg2.load_origin_state(state_path)
        skill2 = reg2.get("example")
        assert skill2 is not None
        assert skill2.remote_version == SemVer.parse("2.0.0")
        assert skill2.remote_hash == "deadbeef"
        assert skill2.is_outdated

    def test_has_origin_update(self):
        skill = Skill(
            id="test",
            name="Test",
            description="",
            scope=Scope.BUILT_IN,
            path=Path("/dev/null"),  # type: ignore[arg-type]
            version=SemVer.parse("1.0.0"),
            remote_version=SemVer.parse("2.0.0"),
        )
        assert skill.has_origin_update()

    def test_no_origin_update_when_equal(self):
        skill = Skill(
            id="test",
            name="Test",
            description="",
            scope=Scope.BUILT_IN,
            path=Path("/dev/null"),  # type: ignore[arg-type]
            version=SemVer.parse("1.0.0"),
            remote_version=SemVer.parse("1.0.0"),
        )
        assert not skill.has_origin_update()


@pytest.fixture
def local_git_repo(tmp_path: Path) -> tuple[str, str]:
    """A throwaway git repo with one commit tagged v1.2.0 and one tagged v1.10.0."""
    import subprocess

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args], check=True, capture_output=True, text=True
        ).stdout.strip()

    git("init", "-q", "-b", "main")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "t")
    (tmp_path / "SKILL.md").write_text("# s\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-q", "-m", "init")
    git("tag", "v1.2.0")
    git("tag", "-a", "v1.10.0", "-m", "annotated")
    return str(tmp_path), git("rev-parse", "HEAD")


async def test_git_ls_remote_returns_commit_hash(local_git_repo: tuple[str, str]) -> None:
    from skilltree.origins import _git_ls_remote

    url, head = local_git_repo
    assert await _git_ls_remote(url, "refs/heads/main") == head


async def test_git_latest_tag_picks_highest_semver(local_git_repo: tuple[str, str]) -> None:
    from skilltree.origins import _git_latest_tag

    url, _ = local_git_repo
    assert await _git_latest_tag(url, "main") == SemVer.parse("1.10.0")
