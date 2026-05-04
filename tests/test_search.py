"""Tests for search index."""

from pathlib import Path

from skilltree.models import Scope, Skill
from skilltree.search import SearchIndex


def make_skill(name: str, content: str = "") -> Skill:
    return Skill(
        id=name.lower().replace(" ", "-"),
        name=name,
        description=f"Description for {name}",
        scope=Scope.BUILT_IN,
        path=Path("/dev/null"),  # type: ignore[arg-type]
        tags=[name.split()[0].lower()],
        content=content,
    )


def test_search_ranking():
    idx = SearchIndex()
    skills = [
        make_skill("Docker Expert", "Advanced Docker containerization and security"),
        make_skill("Kubernetes Mastery", "Production Kubernetes operations"),
        make_skill("Python Basics", "Learn Python programming"),
    ]
    idx.build(skills)

    results = idx.query("docker container")
    assert len(results) >= 1
    # Docker Expert should rank highest
    assert results[0][0] == "docker-expert"


def test_search_no_results():
    idx = SearchIndex()
    idx.build([make_skill("Foo Bar")])
    assert idx.query("bazqux") == []
