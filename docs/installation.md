# Installation

Jean-Michel is intended to be installed and used from another repository.

## Option 1: Install from PyPI

From your target project root:

```bash
uv add jean-michel
```

Then use the CLI:

```bash
uv run jm --help
```

## Option 2: Install from a Local Path (development phase)

If you are iterating locally on Jean-Michel and want to consume it from another repo:

```bash
uv add --editable /absolute/path/to/jean-michel
```

Then:

```bash
uv run jm --help
```

## Conversation DB Path

Jean-Michel stores conversation data in DuckDB.

You can force a specific database path with:

```bash
JEAN_MICHEL_DB_PATH=/path/to/your/project/.jean-michel/storage.duckdb uv run jm lm
```

If this variable is not set, the default path is:

```text
.jean-michel/storage.duckdb
```

## API Port Strategy

By default, Jean-Michel computes a deterministic API port per repository (range `5600-6599`) from repository identity.
This avoids port collisions when multiple repositories use Jean-Michel on the same machine.

To force a specific port:

```bash
JEAN_MICHEL_API_PORT=5656 make api
```

## Coverage Command

Coverage is computed in an isolated worktree at the selected commit.

Default command:

```text
uv run pytest --cov --cov-report=xml
```

Override command when needed:

```bash
JEAN_MICHEL_COVERAGE_CMD="uv run pytest --cov --cov-report=xml --cov=your_package" uv run jm api
```

You can also update the command at runtime from:

- Repository tab in the web app
- API endpoints: `GET /api/coverage/command`, `POST /api/coverage/command`
- MCP tools: `get_coverage_command`, `set_coverage_command`
