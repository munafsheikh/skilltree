"""Data models for skilltree."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class Scope(str, Enum):
    """Skill scope defines the origin and precedence of a skill."""

    BUILT_IN = "built-in"
    EXTRA = "extra"
    USER = "user"
    PROJECT = "project"

    def precedence(self) -> int:
        """Return precedence value: higher overrides lower."""
        return {
            Scope.BUILT_IN: 0,
            Scope.EXTRA: 1,
            Scope.USER: 2,
            Scope.PROJECT: 3,
        }[self]


@dataclass(frozen=True, slots=True)
class SemVer:
    """Semantic version wrapper."""

    major: int = 0
    minor: int = 0
    patch: int = 0
    prerelease: str = ""
    build: str = ""

    _PATTERN = re.compile(
        r"^(?P<major>\d+)"
        r"(?:\.(?P<minor>\d+))?"
        r"(?:\.(?P<patch>\d+))?"
        r"(?:-(?P<pre>[a-zA-Z0-9.]+))?"
        r"(?:\+(?P<build>[a-zA-Z0-9.]+))?$"
    )

    @classmethod
    def parse(cls, text: str) -> SemVer:
        """Parse a semantic version string."""
        text = text.strip().lstrip("v")
        m = cls._PATTERN.match(text)
        if not m:
            raise ValueError(f"Invalid semver: {text!r}")
        gd = m.groupdict()
        return cls(
            major=int(gd["major"] or 0),
            minor=int(gd["minor"] or 0),
            patch=int(gd["patch"] or 0),
            prerelease=gd["pre"] or "",
            build=gd["build"] or "",
        )

    def __str__(self) -> str:
        v = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            v += f"-{self.prerelease}"
        if self.build:
            v += f"+{self.build}"
        return v

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        for attr in ("major", "minor", "patch"):
            self_val = getattr(self, attr)
            other_val = getattr(other, attr)
            if self_val != other_val:
                return self_val < other_val
        # No prerelease > any prerelease
        if not self.prerelease and other.prerelease:
            return False
        if self.prerelease and not other.prerelease:
            return True
        if self.prerelease and other.prerelease:
            return self.prerelease < other.prerelease
        return False

    def __le__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return self == other or self < other

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return not self <= other

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return not self < other


class OriginType(str, Enum):
    """How a skill's origin is tracked and checked for updates."""

    EMBEDDED = "embedded"  # Shipped with the server package
    GIT = "git"  # Git repository
    HTTP = "http"  # HTTP(S) manifest or raw URL
    LOCAL = "local"  # Local filesystem only, no remote tracking


@dataclass(slots=True)
class Skill:
    """Represents a single skill in the tree."""

    id: str
    name: str
    description: str
    scope: Scope
    path: Path
    version: SemVer = field(default_factory=lambda: SemVer(0, 0, 0))
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    content: str = ""
    content_hash: str = ""
    installed_version: SemVer | None = None
    installed_path: Path | None = None
    mtime: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Origin tracking --------------------------------------------------
    origin: str = ""  # URL, git repo, or local path to source
    origin_type: OriginType = OriginType.LOCAL
    origin_ref: str = ""  # Git branch/tag, subpath, or manifest URL
    remote_version: SemVer | None = None  # Last known version from origin
    remote_hash: str = ""  # Last known hash/commit from origin
    last_checked: datetime | None = None  # When we last checked the origin
    is_outdated: bool = False  # True if origin has a newer version

    @property
    def relative_path(self) -> str:
        """Return a URI-friendly relative path."""
        return self.path.as_posix()

    @property
    def uri(self) -> str:
        """Return the skill URI."""
        return f"skill://{self.scope.value}/{self.id}"

    @property
    def tree_uri(self) -> str:
        """Return the tree resource URI."""
        return f"skilltree://{self.scope.value}"

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()[:16]

    def has_local_update(self) -> bool:
        """Check if a newer local version is available than installed."""
        if self.installed_version is None:
            return False
        return self.version > self.installed_version

    def has_origin_update(self) -> bool:
        """Check if the origin has a newer version than what we have locally."""
        if self.remote_version is None:
            return False
        return self.remote_version > self.version

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "scope": self.scope.value,
            "version": str(self.version),
            "tags": self.tags,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "uri": self.uri,
            "content_hash": self.content_hash or self.compute_hash(),
            "installed_version": str(self.installed_version) if self.installed_version else None,
            "has_local_update": self.has_local_update(),
            # Origin info
            "origin": self.origin,
            "origin_type": self.origin_type.value,
            "origin_ref": self.origin_ref,
            "remote_version": str(self.remote_version) if self.remote_version else None,
            "remote_hash": self.remote_hash,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "is_outdated": self.is_outdated,
            "has_origin_update": self.has_origin_update(),
            "mtime": self.mtime.isoformat(),
        }


@dataclass(slots=True)
class SkillTree:
    """Represents a subtree or the entire skill tree."""

    name: str
    scope: Scope
    description: str = ""
    skills: list[Skill] = field(default_factory=list)
    subtrees: list[SkillTree] = field(default_factory=list)

    @property
    def uri(self) -> str:
        return f"skilltree://{self.scope.value}/{self.name}"

    @property
    def total_skills(self) -> int:
        """Count all skills recursively."""
        return len(self.skills) + sum(s.total_skills for s in self.subtrees)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "scope": self.scope.value,
            "description": self.description,
            "uri": self.uri,
            "total_skills": self.total_skills,
            "skills": [s.to_dict() for s in self.skills],
            "subtrees": [s.to_dict() for s in self.subtrees],
        }
