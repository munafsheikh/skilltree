# Build & Test

## Requirements

- Python 3.10–3.13 (CI matrix tests all four)
- `pip` (or `uv` for faster installs)

## Setting up a dev environment

```bash
git clone https://github.com/munafsheikh/skilltree.git
cd skilltree
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

This installs the package in editable mode plus dev dependencies: `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff`, `mypy`.

## Running the CLI locally

```bash
skilltree-mcp --help
skilltree-mcp list
skilltree-mcp tree --scope built-in
# or, without an installed entry point:
python -m skilltree list
```

## Linting & formatting

```bash
ruff check src tests
ruff format src tests
```

Ruff is configured in `pyproject.toml` (line length 100, target Python 3.10, rule sets `E,F,I,W,N,UP,B,C4,SIM`).

## Type checking

```bash
mypy src
```

`mypy` runs in strict mode (see `[tool.mypy]` in `pyproject.toml`).

## Running tests

```bash
pytest -v
```

With coverage:

```bash
pytest -v --cov=skilltree --cov-report=term --cov-report=html
```

Run a single file or test:

```bash
pytest tests/test_models.py -v
pytest tests/test_search.py::test_search_ranking -v
```

Async tests are auto-detected (`asyncio_mode = "auto"` in `pyproject.toml`) — no `@pytest.mark.asyncio` decorator needed.

### Test layout

| File | Covers |
|---|---|
| `tests/test_models.py` | `SemVer` parsing/comparison, `Skill.has_update` logic |
| `tests/test_registry.py` | Scanning, scope/tag filtering, search, tree building |
| `tests/test_search.py` | Inverted-index ranking and empty-result handling |
| `tests/test_origins.py` | Origin checkers (embedded, local; git/http are mockable) |

When adding a feature, add or extend a test file alongside it — the CI `test` job runs the full suite on every push and PR.

## Building a distributable package

```bash
pip install build
python -m build
```

Produces a wheel and sdist in `dist/`. Sanity-check the wheel before publishing:

```bash
pip install dist/*.whl
skilltree-mcp --help
skilltree-mcp list --format json
```

## Continuous Integration

`.github/workflows/ci.yml` runs on every push to `main`/`master`, on tags `v*`, and on pull requests:

1. **lint** — `ruff check` + `ruff format --check`
2. **test** — pytest across Python 3.10–3.13, coverage uploaded to Codecov on 3.13
3. **build** — builds wheel/sdist, uploads as an artifact
4. **test-wheel** — installs the built wheel and smoke-tests the CLI and MCP server startup
5. **docker** — builds the Docker image (no push) to catch Dockerfile breakage
6. **release** — on `v*` tags only: downloads build artifacts and creates a GitHub Release

All jobs must pass before merging; `build`/`docker` depend on `lint`+`test` passing first.
