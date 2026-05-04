"""Skill registry: discovery, loading, and management of skills."""

from __future__ import annotations

import json
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from skilltree.models import OriginType, Scope, SemVer, Skill, SkillTree
from skilltree.origins import OriginCheckResult, check_all_origins, check_skill_origin

logger = logging.getLogger(__name__)

# Regex to extract frontmatter-style metadata from SKILL.md
_METADATA_RE = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n",
    re.DOTALL | re.MULTILINE,
)


def _built_in_root() -> Path:
    """Return the path to the embedded built-in skills directory.

    Works for both editable installs and packaged wheels.
    """
    if sys.version_info >= (3, 9):
        from importlib.resources import files
    else:
        from importlib_resources import files  # type: ignore[import-not-found,unused-ignore]

    return files("skilltree").joinpath("skills", "built-in")  # type: ignore[return-value]


# Default skill roots: BUILT_IN is embedded in the package.
# User and Project scopes are optional overrides loaded from filesystem.
DEFAULT_SKILL_ROOTS: dict[Scope, list[Path]] = {
    Scope.BUILT_IN: [_built_in_root()],
    Scope.EXTRA: [],
    Scope.USER: [
        Path.home() / ".config" / "agents" / "skills",
        Path.home() / ".claude" / "skills",
    ],
    Scope.PROJECT: [
        Path.cwd() / ".skills",
    ],
}


@dataclass(slots=True)
class RegistryConfig:
    """Configuration for the skill registry."""

    roots: dict[Scope, list[Path]] = field(default_factory=lambda: {
        k: list(v) for k, v in DEFAULT_SKILL_ROOTS.items()
    })
    # Glob pattern to find skill directories
    skill_pattern: str = "**/SKILL.md"
    # File that marks a directory as a skill
    skill_manifest: str = "SKILL.md"
    # Optional JSON metadata sidecar
    metadata_file: str = "skill.json"


class SkillRegistry:
    """Discovers, loads, and caches skills from filesystem roots."""

    def __init__(self, config: RegistryConfig | None = None) -> None:
        self.config = config or RegistryConfig()
        self._skills: dict[str, Skill] = {}
        self._trees: dict[str, SkillTree] = {}
        self._by_scope: dict[Scope, list[Skill]] = {
            s: [] for s in Scope
        }
        self._by_tag: dict[str, list[Skill]] = {}

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def scan(self) -> None:
        """Scan all configured roots and rebuild the registry."""
        self._skills.clear()
        self._trees.clear()
        for s in Scope:
            self._by_scope[s].clear()
        self._by_tag.clear()

        for scope, roots in self.config.roots.items():
            for root in roots:
                if not root.exists():
                    logger.debug("Skipping non-existent root: %s", root)
                    continue
                self._scan_root(root, scope)

        logger.info(
            "Registry scan complete: %d skills across %d scopes",
            len(self._skills),
            sum(1 for v in self._by_scope.values() if v),
        )

    def _scan_root(self, root: Path, scope: Scope) -> None:
        for manifest in root.rglob(self.config.skill_manifest):
            try:
                skill = self._load_skill(manifest, root, scope)
            except Exception as exc:
                logger.warning("Failed to load skill at %s: %s", manifest, exc)
                continue
            self._index(skill)

    def _load_skill(self, manifest: Path, root: Path, scope: Scope) -> Skill:
        content = manifest.read_text(encoding="utf-8")
        meta = self._extract_metadata(content, manifest.parent)
        rel = manifest.parent.relative_to(root)
        skill_id = str(rel.as_posix()).replace("/", "--")

        version_str = meta.get("version", "0.0.0")
        version = SemVer.parse(version_str) if version_str else SemVer(0, 0, 0)

        # Origin metadata
        origin_type_str = meta.get("origin_type", "")
        if scope == Scope.BUILT_IN:
            origin_type = OriginType.EMBEDDED
        elif origin_type_str:
            try:
                origin_type = OriginType(origin_type_str)
            except ValueError:
                origin_type = OriginType.LOCAL
        else:
            origin_type = OriginType.LOCAL

        skill = Skill(
            id=skill_id,
            name=meta.get("name", manifest.parent.name),
            description=meta.get("description", ""),
            scope=scope,
            path=manifest.parent,
            version=version,
            tags=meta.get("tags", []),
            dependencies=meta.get("dependencies", []),
            metadata=meta.get("metadata", {}),
            content=content,
            content_hash=meta.get("content_hash", ""),
            origin=meta.get("origin", ""),
            origin_type=origin_type,
            origin_ref=meta.get("origin_ref", ""),
        )
        if not skill.content_hash:
            skill.content_hash = skill.compute_hash()
        return skill

    def _extract_metadata(self, content: str, skill_dir: Path) -> dict[str, Any]:
        meta: dict[str, Any] = {}
        m = _METADATA_RE.match(content)
        if m:
            import yaml
            try:
                meta = yaml.safe_load(m.group(1)) or {}
            except Exception:
                pass
        # Allow JSON sidecar to override / extend
        sidecar = skill_dir / "skill.json"
        if sidecar.exists():
            try:
                meta.update(json.loads(sidecar.read_text(encoding="utf-8")))
            except Exception:
                pass
        return meta

    def _index(self, skill: Skill) -> None:
        self._skills[skill.id] = skill
        self._by_scope[skill.scope].append(skill)
        for tag in skill.tags:
            self._by_tag.setdefault(tag.lower(), []).append(skill)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get(self, skill_id: str) -> Skill | None:
        """Fetch a single skill by ID."""
        return self._skills.get(skill_id)

    def get_by_uri(self, uri: str) -> Skill | None:
        """Fetch a skill by its URI (e.g. skill://built-in/foo)."""
        prefix = "skill://"
        if not uri.startswith(prefix):
            return None
        rest = uri[len(prefix):]
        # Format: scope/id or scope/path/with--double--dashes
        scope_str, skill_id = rest.split("/", 1)
        try:
            scope = Scope(scope_str)
        except ValueError:
            return None
        skill = self._skills.get(skill_id)
        if skill and skill.scope == scope:
            return skill
        return None

    def list_all(self) -> list[Skill]:
        """Return all discovered skills."""
        return list(self._skills.values())

    def list_by_scope(self, scope: Scope) -> list[Skill]:
        """Return skills for a given scope."""
        return list(self._by_scope.get(scope, []))

    def list_by_tag(self, tag: str) -> list[Skill]:
        """Return skills tagged with ``tag``."""
        return list(self._by_tag.get(tag.lower(), []))

    def search(self, query: str) -> list[Skill]:
        """Simple substring search across name, description, tags, id."""
        q = query.lower()
        results = []
        for skill in self._skills.values():
            haystack = " ".join(
                filter(
                    None,
                    [
                        skill.id.lower(),
                        skill.name.lower(),
                        skill.description.lower(),
                        " ".join(skill.tags).lower(),
                        skill.scope.value.lower(),
                        skill.origin.lower(),
                    ],
                )
            )
            if q in haystack:
                results.append(skill)
        return results

    def list_outdated(self) -> list[Skill]:
        """Return skills whose origin reports a newer version available."""
        return [s for s in self._skills.values() if s.is_outdated]

    # ------------------------------------------------------------------
    # Trees
    # ------------------------------------------------------------------

    def get_tree(self, scope: Scope | None = None) -> SkillTree:
        """Build a hierarchical skill tree.

        If ``scope`` is given, return that scope's tree only.
        Otherwise return a meta-tree containing all scopes as subtrees.
        """
        if scope is not None:
            return self._build_scope_tree(scope)

        meta = SkillTree(
            name="root",
            scope=Scope.BUILT_IN,
            description="All skill trees",
        )
        for s in Scope:
            if self._by_scope[s]:
                meta.subtrees.append(self._build_scope_tree(s))
        return meta

    def _build_scope_tree(self, scope: Scope) -> SkillTree:
        root = SkillTree(
            name=scope.value,
            scope=scope,
            description=f"Skills from {scope.value} scope",
        )
        # Build a simple tree from directory structure
        tree_map: dict[str, SkillTree] = {}
        for skill in self._by_scope[scope]:
            parts = skill.id.split("--")
            # parts[:-1] are intermediate dirs
            current = root
            for part in parts[:-1]:
                if part not in tree_map:
                    subtree = SkillTree(name=part, scope=scope)
                    tree_map[part] = subtree
                    current.subtrees.append(subtree)
                    current = subtree
                else:
                    current = tree_map[part]
            current.skills.append(skill)
        return root

    # ------------------------------------------------------------------
    # Origin checking
    # ------------------------------------------------------------------

    async def check_origins(self, skill_ids: list[str] | None = None) -> list[OriginCheckResult]:
        """Check origins for updates.

        If ``skill_ids`` is None, checks all skills.
        """
        if skill_ids is None:
            skills = self.list_all()
        else:
            skills = [s for sid in skill_ids if (s := self._skills.get(sid))]

        results = await check_all_origins(skills)
        for result in results:
            skill = self._skills.get(result.skill_id)
            if skill is None:
                continue
            skill.remote_version = result.remote_version
            skill.remote_hash = result.remote_hash
            skill.last_checked = result.checked_at
            skill.is_outdated = result.is_outdated
        self.save_origin_state()
        return results

    async def check_origin(self, skill_id: str) -> OriginCheckResult:
        """Check a single skill's origin for updates."""
        skill = self._skills.get(skill_id)
        if skill is None:
            raise KeyError(f"Skill not found: {skill_id}")
        result = await check_skill_origin(skill)
        skill.remote_version = result.remote_version
        skill.remote_hash = result.remote_hash
        skill.last_checked = result.checked_at
        skill.is_outdated = result.is_outdated
        self.save_origin_state()
        return result

    # ------------------------------------------------------------------
    # Installation state
    # ------------------------------------------------------------------

    def load_installed_state(self, state_path: Path | None = None) -> None:
        """Load installed-versions map from a JSON file."""
        if state_path is None:
            state_path = Path.home() / ".config" / "skilltree" / "installed.json"
        if not state_path.exists():
            return
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Failed to load installed state: %s", exc)
            return
        for skill_id, info in data.items():
            skill = self._skills.get(skill_id)
            if skill is None:
                continue
            try:
                skill.installed_version = SemVer.parse(info.get("version", "0.0.0"))
            except ValueError:
                pass
            if info.get("path"):
                skill.installed_path = Path(info["path"])

    def save_installed_state(self, state_path: Path | None = None) -> None:
        """Persist installed-versions map to a JSON file."""
        if state_path is None:
            state_path = Path.home() / ".config" / "skilltree" / "installed.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            skill.id: {
                "version": str(skill.installed_version),
                "path": str(skill.installed_path) if skill.installed_path else None,
            }
            for skill in self._skills.values()
            if skill.installed_version is not None
        }
        state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def mark_installed(self, skill_id: str, path: Path | None = None) -> None:
        """Mark a skill as installed at its current version."""
        skill = self._skills.get(skill_id)
        if skill is None:
            raise KeyError(f"Skill not found: {skill_id}")
        skill.installed_version = skill.version
        skill.installed_path = path

    # ------------------------------------------------------------------
    # Origin state persistence
    # ------------------------------------------------------------------

    def load_origin_state(self, state_path: Path | None = None) -> None:
        """Load origin check state from a JSON file."""
        if state_path is None:
            state_path = Path.home() / ".config" / "skilltree" / "origins.json"
        if not state_path.exists():
            return
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Failed to load origin state: %s", exc)
            return
        for skill_id, info in data.items():
            skill = self._skills.get(skill_id)
            if skill is None:
                continue
            rv = info.get("remote_version")
            if rv:
                try:
                    skill.remote_version = SemVer.parse(rv)
                except ValueError:
                    pass
            skill.remote_hash = info.get("remote_hash", "")
            if "last_checked" in info:
                try:
                    skill.last_checked = datetime.fromisoformat(info["last_checked"])
                except ValueError:
                    pass
            skill.is_outdated = info.get("is_outdated", False)
            if "origin" in info:
                skill.origin = info["origin"]
            if "origin_type" in info:
                try:
                    skill.origin_type = OriginType(info["origin_type"])
                except ValueError:
                    pass
            if "origin_ref" in info:
                skill.origin_ref = info["origin_ref"]

    def save_origin_state(self, state_path: Path | None = None) -> None:
        """Persist origin check state to a JSON file."""
        if state_path is None:
            state_path = Path.home() / ".config" / "skilltree" / "origins.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            skill.id: {
                "origin": skill.origin,
                "origin_type": skill.origin_type.value,
                "origin_ref": skill.origin_ref,
                "remote_version": str(skill.remote_version) if skill.remote_version else None,
                "remote_hash": skill.remote_hash,
                "last_checked": skill.last_checked.isoformat() if skill.last_checked else None,
                "is_outdated": skill.is_outdated,
            }
            for skill in self._skills.values()
            if skill.last_checked is not None
        }
        state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Re-scan the filesystem and reload state."""
        self.scan()
        self.load_installed_state()
        self.load_origin_state()
