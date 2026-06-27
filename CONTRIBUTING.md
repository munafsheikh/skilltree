# Contributing to skilltree

Thanks for considering a contribution. This project welcomes bug fixes, new built-in skills, documentation improvements, and feature work.

## Getting started

```bash
git clone https://github.com/munafsheikh/skilltree.git
cd skilltree
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

See [docs/BUILD_AND_TEST.md](docs/BUILD_AND_TEST.md) for the full dev workflow (linting, type checking, coverage).

## Before opening a PR

1. **Lint & format**: `ruff check src tests && ruff format src tests`
2. **Type check**: `mypy src`
3. **Test**: `pytest -v` — add or update tests for any behavior change
4. Keep changes focused; unrelated cleanups belong in a separate PR

CI (`.github/workflows/ci.yml`) runs lint, the test matrix (Python 3.10–3.13), a build, and a Docker build check on every PR — make sure these pass locally first.

## What to contribute

- **Bug fixes** — include a regression test where practical
- **New built-in skills** — see [docs/EXTENDING.md](docs/EXTENDING.md#adding-a-new-built-in-skill) for the `SKILL.md` format and directory layout
- **New MCP tools, transports, or origin checkers** — see the relevant sections of [docs/EXTENDING.md](docs/EXTENDING.md)
- **Documentation** — fixes/clarifications to README or `docs/` are always welcome
- **Roadmap items** — see [docs/ROADMAP.md](docs/ROADMAP.md); comment on or open an issue before starting larger work to avoid duplicate effort

## Commit & PR conventions

- Write descriptive commit messages explaining *why*, not just *what*
- Reference related issues in the PR description
- Keep PRs reasonably small and reviewable; large features should be discussed in an issue first

## Code style

- Python 3.10+ idioms; type hints required (mypy strict mode)
- Follow existing module boundaries — see [docs/EXTENDING.md](docs/EXTENDING.md#architecture-overview)
- No unrelated formatting churn in functional PRs

## Reporting issues

Open a GitHub issue with steps to reproduce, expected vs. actual behavior, and your environment (Python version, OS, transport used). For security issues, avoid filing a public issue — contact the maintainers directly.

## License

By contributing, you agree your contributions are licensed under the project's MIT license.
