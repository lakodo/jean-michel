# Core Concepts

## What "Asynchronous" Means

Interaction and execution are decoupled.

You continuously interact with one persistent agent without waiting for previous tasks to finish. Messages are translated into background tasks.

There is:

- one interface
- one timeline
- one persistent agent
- no session resets
- no parallel chat threads

## Philosophy

Jean-Michel is built around four principles:

1. Constraint-first engineering.
2. Autonomy without opacity.
3. Worktree isolation.
4. Merge-ready output.

## Commitology

Commitology enforces disciplined commit production.

It includes:

- conventional commit adherence
- style inference from repository history
- structured commit generation
- Commitizen integration when available

## AST-Based Structural Editing (optional)

Instead of raw text edits, Jean-Michel can:

- parse Python into AST
- modify structural nodes
- regenerate normalized code

## Initialization Layer

On first integration with a project, Jean-Michel creates and versions `.jean-michel/` metadata for:

- features
- constraints
- scope rules
- historical commit analysis
- monitoring metadata

## Features and Constraints

Jean-Michel distinguishes:

- constraints: negative scopes / hard exclusions
- features: positive authorized scopes

Rules:

- constraints override features
- scope conflicts are detected
- conflicts are surfaced in monitoring/dashboard

## Continuous Analysis

Jean-Michel can continuously monitor:

- duplication
- imports
- dead code
- bad practices
- refactor opportunities
- coverage regressions

It can propose improvement branches and follow-up tasks.

## Multi-Device Continuity

Jean-Michel is repository-centric, not machine-centric.

A background sync task can:

- fetch remote updates
- detect new commits/branch movement
- evaluate sync state
- trigger analysis on remote changes

Git remains the source of truth for repository history.

## Feature-Aware Evolution

Features are treated as scoped, versioned engineering units.

The scheduler can reason about cross-feature interactions and classify conflicts such as:

- scope overlap
- contract violations
- coverage regressions
- responsibility drift
- hidden coupling

Constraint rules remain dominant over feature scopes.
