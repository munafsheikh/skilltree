"""Full-text search over skills."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from skilltree.models import Skill


def _tokenize(text: str) -> set[str]:
    """Lower-case, alphanumeric tokens."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


@dataclass(slots=True)
class SearchIndex:
    """In-memory inverted index for skills."""

    _index: dict[str, set[str]] = field(default_factory=dict)

    def add(self, skill: Skill) -> None:
        """Index a single skill."""
        tokens: set[str] = set()
        tokens |= _tokenize(skill.id)
        tokens |= _tokenize(skill.name)
        tokens |= _tokenize(skill.description)
        tokens |= _tokenize(skill.scope.value)
        for tag in skill.tags:
            tokens |= _tokenize(tag)
        # Also index raw content (first 10k chars to keep memory bounded)
        tokens |= _tokenize(skill.content[:10000])
        for tok in tokens:
            self._index.setdefault(tok, set()).add(skill.id)

    def build(self, skills: Iterable[Skill]) -> None:
        """Build index from an iterable of skills."""
        self._index.clear()
        for skill in skills:
            self.add(skill)

    def query(self, q: str) -> list[tuple[str, float]]:
        """Return (skill_id, score) sorted by relevance."""
        query_tokens = _tokenize(q)
        if not query_tokens:
            return []

        scores: dict[str, float] = {}
        for tok in query_tokens:
            ids = self._index.get(tok, set())
            for sid in ids:
                scores[sid] = scores.get(sid, 0.0) + 1.0

        # Normalize by query length
        norm = len(query_tokens)
        results = [(sid, score / norm) for sid, score in scores.items()]
        results.sort(key=lambda x: x[1], reverse=True)
        return results
