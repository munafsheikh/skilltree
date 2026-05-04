"""Origin tracking and update checking for skills.

Each skill can declare an origin (git repo, HTTP URL, or local path).
This module checks those origins to see if a newer version is available.
"""

from __future__ import annotations

import json
import logging
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from skilltree.models import OriginType, SemVer, Skill

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class OriginCheckResult:
    """Result of checking a skill's origin for updates."""

    skill_id: str
    origin_type: OriginType
    origin: str
    is_accessible: bool
    error: str | None = None
    remote_version: SemVer | None = None
    remote_hash: str = ""
    is_outdated: bool = False
    checked_at: datetime = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.checked_at is None:
            self.checked_at = datetime.now(timezone.utc)


class OriginChecker(ABC):
    """Abstract base for origin update checkers."""

    @property
    @abstractmethod
    def handles(self) -> set[OriginType]:
        """Origin types this checker supports."""
        ...

    @abstractmethod
    async def check(self, skill: Skill) -> OriginCheckResult:
        """Check the skill's origin for updates."""
        ...


class EmbeddedOriginChecker(OriginChecker):
    """Built-in skills are embedded in the package.

    They are considered up-to-date with the server version.
    """

    @property
    def handles(self) -> set[OriginType]:
        return {OriginType.EMBEDDED}

    async def check(self, skill: Skill) -> OriginCheckResult:
        return OriginCheckResult(
            skill_id=skill.id,
            origin_type=OriginType.EMBEDDED,
            origin=skill.origin or "embedded",
            is_accessible=True,
            remote_version=skill.version,
            remote_hash=skill.content_hash,
            is_outdated=False,
        )


class LocalOriginChecker(OriginChecker):
    """Local filesystem skills: compare mtime against a reference file."""

    @property
    def handles(self) -> set[OriginType]:
        return {OriginType.LOCAL}

    async def check(self, skill: Skill) -> OriginCheckResult:
        origin_path = Path(skill.origin) if skill.origin else skill.path
        accessible = origin_path.exists()
        remote_hash = ""
        if accessible and origin_path.is_dir():
            manifest = origin_path / "SKILL.md"
            if manifest.exists():
                remote_hash = _hash_file(manifest)
        return OriginCheckResult(
            skill_id=skill.id,
            origin_type=OriginType.LOCAL,
            origin=str(origin_path),
            is_accessible=accessible,
            remote_hash=remote_hash,
            is_outdated=accessible and remote_hash != skill.content_hash,
        )


class GitOriginChecker(OriginChecker):
    """Check git repositories for new tags or commits."""

    @property
    def handles(self) -> set[OriginType]:
        return {OriginType.GIT}

    async def check(self, skill: Skill) -> OriginCheckResult:
        origin = skill.origin or ""
        ref = skill.origin_ref or "HEAD"

        if not origin:
            return OriginCheckResult(
                skill_id=skill.id,
                origin_type=OriginType.GIT,
                origin="",
                is_accessible=False,
                error="No origin URL set",
            )

        # Try to get the latest commit on the remote ref
        remote_hash = await _git_ls_remote(origin, ref)
        if remote_hash is None:
            return OriginCheckResult(
                skill_id=skill.id,
                origin_type=OriginType.GIT,
                origin=origin,
                is_accessible=False,
                error=f"Could not resolve ref {ref!r} from {origin}",
            )

        # Try to parse a version from the newest tag reachable from ref
        remote_version = await _git_latest_tag(origin, ref) or skill.version

        is_outdated = remote_hash != skill.content_hash and remote_hash != skill.remote_hash
        # Also consider outdated if remote version is newer
        if remote_version and skill.version:
            is_outdated = is_outdated or (remote_version > skill.version)

        return OriginCheckResult(
            skill_id=skill.id,
            origin_type=OriginType.GIT,
            origin=origin,
            is_accessible=True,
            remote_version=remote_version,
            remote_hash=remote_hash,
            is_outdated=is_outdated,
        )


class HTTPOriginChecker(OriginChecker):
    """Check HTTP(S) endpoints for a remote manifest."""

    @property
    def handles(self) -> set[OriginType]:
        return {OriginType.HTTP}

    async def check(self, skill: Skill) -> OriginCheckResult:
        origin = skill.origin or ""
        if not origin:
            return OriginCheckResult(
                skill_id=skill.id,
                origin_type=OriginType.HTTP,
                origin="",
                is_accessible=False,
                error="No origin URL set",
            )

        manifest_url = skill.origin_ref or origin
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(manifest_url)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            return OriginCheckResult(
                skill_id=skill.id,
                origin_type=OriginType.HTTP,
                origin=origin,
                is_accessible=False,
                error=str(exc),
            )

        remote_version = None
        remote_hash = data.get("hash", data.get("content_hash", ""))
        version_str = data.get("version", "")
        if version_str:
            try:
                remote_version = SemVer.parse(version_str)
            except ValueError:
                pass

        is_outdated = False
        if remote_version and skill.version:
            is_outdated = remote_version > skill.version
        elif remote_hash and remote_hash != skill.content_hash:
            is_outdated = True

        return OriginCheckResult(
            skill_id=skill.id,
            origin_type=OriginType.HTTP,
            origin=origin,
            is_accessible=True,
            remote_version=remote_version,
            remote_hash=remote_hash,
            is_outdated=is_outdated,
        )


# ------------------------------------------------------------------
# Registry of checkers
# ------------------------------------------------------------------

_CHECKERS: dict[OriginType, OriginChecker] = {
    OriginType.EMBEDDED: EmbeddedOriginChecker(),
    OriginType.LOCAL: LocalOriginChecker(),
    OriginType.GIT: GitOriginChecker(),
    OriginType.HTTP: HTTPOriginChecker(),
}


async def check_skill_origin(skill: Skill) -> OriginCheckResult:
    """Check a single skill's origin for updates."""
    checker = _CHECKERS.get(skill.origin_type)
    if checker is None:
        return OriginCheckResult(
            skill_id=skill.id,
            origin_type=skill.origin_type,
            origin=skill.origin,
            is_accessible=False,
            error=f"No checker registered for origin type {skill.origin_type.value}",
        )
    return await checker.check(skill)


async def check_all_origins(skills: list[Skill]) -> list[OriginCheckResult]:
    """Check all provided skills for origin updates."""
    import anyio

    results: list[OriginCheckResult] = []
    async with anyio.create_task_group() as tg:

        def _make_task(skill: Skill) -> None:
            async def _task() -> None:
                try:
                    result = await check_skill_origin(skill)
                except Exception as exc:
                    result = OriginCheckResult(
                        skill_id=skill.id,
                        origin_type=skill.origin_type,
                        origin=skill.origin,
                        is_accessible=False,
                        error=str(exc),
                    )
                results.append(result)

            tg.start_soon(_task)

        for skill in skills:
            _make_task(skill)
    return results


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _hash_file(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


async def _git_ls_remote(repo_url: str, ref: str) -> str | None:
    """Return the commit hash for a ref via ls-remote."""
    cmd = ["git", "ls-remote", "--quiet", repo_url, ref]
    try:
        proc = await anyio.run_process(cmd, check=False)  # type: ignore[attr-defined]
        if proc.returncode != 0:
            return None
        stdout = proc.stdout.decode("utf-8").strip()
        if not stdout:
            return None
        # Format: "<hash>\t<ref>"
        return stdout.split()[0]
    except Exception as exc:
        logger.debug("git ls-remote failed for %s: %s", repo_url, exc)
        return None


async def _git_latest_tag(repo_url: str, ref: str) -> SemVer | None:
    """Try to find the newest semver tag reachable from ref."""
    cmd = ["git", "ls-remote", "--tags", "--sort=-v:refname", repo_url]
    try:
        proc = await anyio.run_process(cmd, check=False)  # type: ignore[attr-defined]
        if proc.returncode != 0:
            return None
        stdout = proc.stdout.decode("utf-8").strip()
        if not stdout:
            return None
        best: SemVer | None = None
        for line in stdout.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            tag = parts[1].replace("refs/tags/", "").rstrip("^{}")
            try:
                v = SemVer.parse(tag)
            except ValueError:
                continue
            if best is None or v > best:
                best = v
        return best
    except Exception as exc:
        logger.debug("git tag listing failed for %s: %s", repo_url, exc)
        return None
