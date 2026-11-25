"""Tests for skilltree registry."""

from pathlib import Path

import pytest

from skilltree.models import Scope, SemVer
from skilltree.registry import RegistryConfig, SkillRegistry


@pytest.fixture
def sample_registry(tmp_path: Path) -> SkillRegistry:
    built_in = tmp_path / "built-in"
    built_in.mkdir()
    skill_dir = built_in / "example-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: Example Skill\n"
        "description: An example skill for testing.\n"
        "version: 1.0.0\n"
        "tags: [test, example]\n"
        "---\n\n"
        "# Example Skill\n\n"
        "This is a test skill.\n",
        encoding="utf-8",
    )
    cfg = RegistryConfig()
    cfg.roots = {Scope.BUILT_IN: [built_in], Scope.EXTRA: [], Scope.USER: [], Scope.PROJECT: []}
    reg = SkillRegistry(cfg)
    reg.scan()
    return reg


class TestRegistry:
    def test_scan_finds_skill(self, sample_registry: SkillRegistry):
        skills = sample_registry.list_all()
        assert len(skills) == 1
        assert skills[0].id == "example-skill"
        assert skills[0].name == "Example Skill"
        assert skills[0].version == SemVer.parse("1.0.0")

    def test_get_by_id(self, sample_registry: SkillRegistry):
        skill = sample_registry.get("example-skill")
        assert skill is not None
        assert skill.name == "Example Skill"

    def test_get_by_uri(self, sample_registry: SkillRegistry):
        skill = sample_registry.get_by_uri("skill://built-in/example-skill")
        assert skill is not None
        assert skill.name == "Example Skill"

    def test_search(self, sample_registry: SkillRegistry):
        results = sample_registry.search("example")
        assert len(results) == 1
        assert results[0].id == "example-skill"

    def test_list_by_scope(self, sample_registry: SkillRegistry):
        assert len(sample_registry.list_by_scope(Scope.BUILT_IN)) == 1
        assert len(sample_registry.list_by_scope(Scope.USER)) == 0

    def test_list_by_tag(self, sample_registry: SkillRegistry):
        assert len(sample_registry.list_by_tag("test")) == 1
        assert len(sample_registry.list_by_tag("missing")) == 0

    def test_tree_structure(self, sample_registry: SkillRegistry):
        tree = sample_registry.get_tree()
        assert tree.name == "root"
        assert tree.total_skills == 1

    def test_mark_installed(self, sample_registry: SkillRegistry):
        sample_registry.mark_installed("example-skill")
        skill = sample_registry.get("example-skill")
        assert skill is not None
        assert skill.installed_version == SemVer.parse("1.0.0")
        assert not skill.has_local_update()

    def test_installed_state_persistence(self, sample_registry: SkillRegistry, tmp_path: Path):
        state_path = tmp_path / "installed.json"
        sample_registry.mark_installed("example-skill")
        sample_registry.save_installed_state(state_path)
        assert state_path.exists()

        sample_registry.load_installed_state(state_path)
        skill = sample_registry.get("example-skill")
        assert skill is not None
        assert skill.installed_version == SemVer.parse("1.0.0")
