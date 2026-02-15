# Jean-Michel

[![Release](https://img.shields.io/github/v/release/lakodo/jean-michel)](https://github.com/lakodo/jean-michel/releases)
[![Build status](https://img.shields.io/github/actions/workflow/status/lakodo/jean-michel/main.yml?branch=main)](https://github.com/lakodo/jean-michel/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/lakodo/jean-michel/branch/main/graph/badge.svg)](https://codecov.io/gh/lakodo/jean-michel)
[![Commit activity](https://img.shields.io/github/commit-activity/m/lakodo/jean-michel)](https://github.com/lakodo/jean-michel/commits/main)
[![License](https://img.shields.io/github/license/lakodo/jean-michel)](https://github.com/lakodo/jean-michel/blob/main/LICENSE)

**An opinionated AI assistant for rigorous, constrained, asynchronous software development.**
Define protected scopes and explicit features, delegate background work to autonomous worktrees, and integrate with your existing toolchain (pre-commit, Makefile). Agents produce isolated commits following Conventional Commits and submit merge-ready changes with minimal disruption to the main session.

---

## Project Links

- Repository: <https://github.com/lakodo/jean-michel>
- Curry scheduler backend reference: <https://github.com/lakodo/curry>

---

## Installation

Jean-Michel is intended to be installed and used from another repository.

### Option 1: Install from PyPI

From your target project root:

```bash
uv add jean-michel
```

Then use the CLI:

```bash
uv run jm --help
```

### Option 2: Install from a Local Path (development phase)

If you are iterating locally on Jean-Michel and want to consume it from another repo:

```bash
uv add --editable /absolute/path/to/jean-michel
```

Then:

```bash
uv run jm --help
```

### Conversation DB Path

Jean-Michel stores conversation data in DuckDB.

You can force a specific database path with:

```bash
JEAN_MICHEL_DB_PATH=/path/to/your/project/.jean-michel/conversation.duckdb uv run jm lm
```

If this variable is not set, the default path is:

```text
.jean-michel/conversation.duckdb
```

---

## What “Asynchronous” Means

Interaction and execution are decoupled.

You continuously interact with a single persistent agent — issuing instructions, refining intent, or adding new requests — without waiting for prior tasks to complete. Each message is translated into structured background tasks processed independently.

There is:

- one interface
- one timeline
- one persistent agent
- no session resets
- no parallel chat threads

The agent orchestrates execution in the background (isolated worktrees, autonomous commits, continuous analysis), while the dialogue remains uninterrupted and cumulative.

---

## Philosophy

Jean-Michel is built around four principles:

1. **Constraint-first engineering** — Safety and scope control are primary.
2. **Autonomy without opacity** — Agents act independently, but every action is traceable.
3. **Worktree isolation** — No direct mutation of the main branch.
4. **Merge-ready output** — Every change must be reviewable, measurable, and conventional.

---

## Architecture Overview

Jean-Michel is composed of five major layers:

```
Developer(s)
      ↓
Conversation Timeline (single persistent channel)
      ↓
Primary Agent (semantic interpreter)
      ↓
Scheduler / Orchestrator
      ↓
Execution Bricks (code, tests, commits, analysis, coverage, etc.)
```

The developer is not “chatting with an LLM.”
They are interacting with a persistent project-level entity that reads the timeline and decides what to execute.

---

## Core Concepts

### 1. Commitology (C-O-2-M-I-T-O-L-O-G-Y)

Commitology enforces disciplined commit production.

Features:

- Strict adherence to Conventional Commits
- Automatic detection of existing repository commit style
- Style inference from historical commits
- Structured commit generation
- Integration with Commitizen (if available)

Every autonomous branch produces atomic, structured, reviewable commits.

---

### 2. AST-Based Structural Editing (Optional Module)

Instead of operating on raw text, Jean-Michel can:

- Parse Python into AST
- Modify structural nodes (functions, classes, statements)
- Regenerate normalized code dumps

Advantages:

- Deterministic formatting
- No bracket/indentation corruption
- Lower token overhead
- Explicit structural diffs
- Reduced debug cycles

All injections occur at tree-level, not via search-and-replace.

---

### 3. Initialization Layer

On first integration with a project:

- A hidden directory (e.g., `.jean-michel/`) is created.
- Knowledge base is initialized:
  - Features
  - Constraints
  - Scope rules
  - Historical commit analysis
  - Monitoring metadata

This directory is versioned.

It defines the behavioral contract of the assistant inside the repository.

---

### 4. Features and Constraints (Scope System)

Jean-Michel distinguishes between:

#### Constraints (Negative Scopes)

- Files that must never be modified
- Files that require explicit permission
- Hard exclusions (non-negotiable)

#### Features (Positive Scopes)

- Authorized modification perimeter
- Allowed directories
- Allowed file creation zones

Rules:

- Constraints always override features.
- Scope conflicts are detected automatically.
- Conflicts are surfaced in the dashboard.

This system prevents uncontrolled codebase mutation.

---

### 5. Continuous Analysis

Independent of active feature work, Jean-Michel continuously monitors:

- Code duplication
- New imports
- Dead code
- Bad practices
- Refactor opportunities
- Coverage regressions

Continuous analysis can:

- Propose improvement branches
- Trigger refactor tasks
- Generate docstrings
- Suggest test augmentation

It is proactive, not reactive.

---

### 6. Multi-Device Continuity

Jean-Michel is repository-centric, not machine-centric.

When the server is running, a background synchronization task can:

- Fetch remote updates
- Detect new commits and branch movements
- Evaluate local/remote sync state
- Trigger follow-up analysis when remote activity is detected

Remote-triggered changes (for example from GitHub UI or another workstation) can be classified and handled the same way as local timeline-driven tasks:

- Impact analysis on modified scope
- Optional isolated worktree creation
- Lint/format/test follow-ups when applicable
- Improvement or correction proposals

An optional lightweight relay service can be introduced for cross-device coordination (task state, metadata, notifications), but Git remains the source of truth for repository history.

Design constraints remain unchanged:

- No hidden rebases
- No silent force-push
- No divergence from Git history
- Worktree isolation and commitology always apply

---

### 7. Feature-Aware Evolution & Cross-Feature Conflict Resolution

Features are treated as scoped, versioned engineering units (stored in `.jean-michel/` metadata), not simple labels.

A feature definition can include:

- Authorized perimeter
- Modified files or directories
- Structural scope
- Expected test coverage targets
- Associated worktrees and branches

Because features are formalized, the scheduler can reason about interactions between them.

When a new feature evolves shared structures, Jean-Michel can:

- Detect perimeter overlap with existing features
- Identify coupling and contract surface changes
- Evaluate regression and coverage impact
- Trigger extension or corrective tasks

Internally, features can be managed as a dependency graph. If a dependent feature mutates shared entities, the scheduler can increase revalidation priority and schedule targeted regression checks.

Conflict classes include:

- Scope overlap
- Contract violations
- Coverage regressions
- Responsibility drift
- Hidden coupling introduction

Constraint rules remain dominant over feature scopes.

---

## Scheduler & Orchestration Engine

The scheduler is the core execution brain.

It:

- Reads the conversation timeline
- Decides whether to respond
- Creates task graphs
- Manages worktrees
- Supervises commit production
- Selectively integrates branches

It is not necessarily the conversational interface.
It operates behind it.

Task execution may rely on a Dask-based scheduler (via [Curry](https://github.com/lakodo/curry) or equivalent), allowing:

- Dependency graphs
- Parallel task execution
- Deterministic chaining
- Post-task hooks (e.g., continuous analysis)

---

## Worktree Model

Every feature or improvement:

- Spawns a dedicated Git worktree
- Creates isolated branches
- Produces structured commits
- Runs lint / hooks / tests
- Reports status to the scheduler

Branches can be:

- Fully merged
- Partially cherry-picked
- Rebased then merged
- Rejected

No background mutation touches `main` directly.

---

## Execution Bricks

The scheduler composes reusable bricks:

- Code generation
- AST mutation
- Refactoring
- Test writing
- Test execution
- Coverage analysis
- Commit creation
- Linting / pre-commit
- Continuous analysis
- Monitoring

Bricks are composable and dependency-aware.

Example chain:

```
Generate feature
    ↓
Run lint / format
    ↓
Write tests
    ↓
Run tests
    ↓
Compute coverage
    ↓
Commit
    ↓
Continuous analysis
```

---

## Coverage-Driven Improvement

Coverage is not passive.

If coverage drops or is insufficient within the scope of a feature:

- Test-writing tasks are triggered
- Coverage delta becomes an objective metric
- Improvement tasks can be spawned automatically

---

## Monitoring & Dashboard

Jean-Michel includes a monitoring layer for each branch:

- Diff size
- Files added / deleted / modified
- Commit count
- Coverage delta
- Structural impact

Branches are scored based on cognitive load:

- Small → Green
- Growing → Orange
- Heavy → Red

The dashboard allows:

- Reviewing diffs
- Selecting branches for integration
- Cherry-picking commits
- Prioritizing review

---

## Conversation Timeline

The conversation is a persistent timeline.

Multiple developers may post messages.

The scheduler:

- Reads the timeline
- Decides when to act
- May request clarification
- May report task launches
- May indicate work already done

The conversation never resets.

It accumulates.

---

## What Jean-Michel Is Not

- Not a code generator that edits `main` directly
- Not a multi-threaded chat interface
- Not an opaque AI making silent changes
- Not a replacement for code review

It is an orchestration layer for disciplined autonomous engineering.

---

## Status

Conceptual architecture.
Modules to formalize next:

- Commitology
- Scope engine (features & constraints)
- AST editing engine
- Scheduler core
- Worktree manager
- Continuous analysis engine
- Monitoring & dashboard API

---

## Development Setup

Install the local environment and hooks:

```bash
make install
```

Run formatting and checks once after bootstrap:

```bash
uv run pre-commit run -a
```

---

## Releasing

For a release workflow aligned with the current CI:

1. Add `PYPI_TOKEN` in repository secrets: <https://github.com/lakodo/jean-michel/settings/secrets/actions/new>
2. Create a GitHub release: <https://github.com/lakodo/jean-michel/releases/new>
3. Use a semantic tag format: `X.Y.Z`
