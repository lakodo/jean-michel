# Architecture Overview

Jean-Michel is composed of five major layers:

```text
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

The developer is not chatting with an LLM session.
They interact with a persistent project-level entity that reads timeline intent and schedules execution.

## Scheduler and Orchestration Engine

The scheduler:

- reads the conversation timeline
- decides whether to respond
- creates task graphs
- manages worktrees
- supervises commit production
- selectively integrates branches

Task execution may rely on a Dask-based scheduler (via [Curry](https://github.com/lakodo/curry) or equivalent), allowing:

- dependency graphs
- parallel task execution
- deterministic chaining
- post-task hooks (for example continuous analysis)

## Worktree Model

Every feature or improvement:

- spawns a dedicated Git worktree
- creates isolated branches
- produces structured commits
- runs lint/hooks/tests
- reports status to the scheduler

No background mutation touches `main` directly.

## Execution Bricks

Reusable bricks include:

- code generation
- AST mutation
- refactoring
- test writing and execution
- coverage analysis
- commit creation
- linting/pre-commit
- monitoring

## Monitoring and Dashboard

For each branch, Jean-Michel tracks:

- diff size
- files added/deleted/modified
- commit count
- coverage delta
- structural impact

Branches are scored by cognitive load (green/orange/red) to prioritize review.
