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
JEAN_MICHEL_DB_PATH=/path/to/your/project/.jean-michel/conversation.duckdb uv run jm lm
```

If this variable is not set, the default path is:

```text
.jean-michel/conversation.duckdb
```
