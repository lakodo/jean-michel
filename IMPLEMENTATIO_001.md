# Implementation de Jean-Michel : architecture et modules clés

(propsoé par ChatGPT 5.2)

Voici une architecture “codable” (et maintenable) pour Jean-Michel, en couches, avec des frontières nettes entre **conversation**, **planification**, **exécution**, **git/worktrees**, **policies**, **observabilité**, **sync multi-device**. L’objectif est de rendre le système **déterministe** dans l’exécution, et **optionnellement IA** dans la planification.

## 1) Principes d’implémentation

* **Core déterministe** : tout ce qui touche à Git, aux worktrees, aux commits, aux scopes, aux hooks, aux tests, au monitoring doit être strictement déterministe et testable.
* **IA en “planner” seulement** : l’IA produit des *plans* (task graphs) et des *artefacts* (messages, propositions), mais n’exécute rien directement.
* **Événementiel + journal append-only** : la conversation et le système produisent des événements immuables; l’état est une projection (rebuildable).
* **Isolation par worktree** : jamais d’édition directe de `main`. Toute action code → worktree + branche + commits.
* **Observabilité d’abord** : chaque tâche a un ID, des logs, un statut, des métriques (diff size, files touched, coverage delta, etc.).

---

## 2) Modules majeurs (domain-driven)

### A. `timeline/` — Conversation as a log

**Rôle :** stocker la “timeline” unique (messages devs, réponses agent, événements système).

* Stockage: fichiers JSONL dans `.jean-michel/timeline/` ou SQLite (recommandé pour requêtes).
* API: `append_message()`, `append_event()`, `stream_since(cursor)`.

**Pourquoi :** la timeline est la source de vérité côté “intention”. Le scheduler lit, mais n’écrit que via événements/réponses.

---

### B. `state/` — Event sourcing + projections

**Rôle :** reconstruire l’état courant à partir des événements.

* Projections typiques:

  * `FeatureRegistryProjection` (features, scopes, dépendances)
  * `ConstraintRegistryProjection`
  * `BranchRegistryProjection` (worktrees, branches, commits, status)
  * `RepoHealthProjection` (lint, tests, coverage, duplication alerts)
  * `SyncProjection` (remote head, last fetch, divergence)

**Pourquoi :** tu veux pouvoir reprendre sur une autre machine, détecter conflits, et ne pas “perdre” l’état si un process tombe.

---

### C. `policy/` — Scopes, constraints, features (authorization engine)

**Rôle :** décider “est-ce que cette action est permise ?”

* Modèles:

  * `ConstraintScope` : deny hard / deny ask / deny ask+reason
  * `FeatureScope` : allow patterns (glob), allow create dirs, allow delete, etc.
* Algo:

  * `is_allowed(change_set, context)` avec priorité contraintes > features
  * détection overlap & conflits feature/feature, feature/constraint
* Sortie: décisions structurées + explications (pour dashboard).

**Pourquoi :** c’est la barrière de sécurité principale.

---

### D. `gitx/` — Git & Worktrees (infrastructure critique)

**Rôle :** gérer worktrees, branches, commits, cherry-pick.

* `WorktreeManager`:

  * create/remove/list worktrees
  * naming rules (branch naming policy)
* `RepoInspector`:

  * diff stats, file lists, rename detection
* `IntegrationManager`:

  * merge/rebase/cherry-pick (toujours explicit)
  * “virtual merge plan” (préflight) avant action

**Pourquoi :** c’est le “kernel” du système; il doit être ultra robuste.

---

### E. `commitology/` — Conventional commits + style inference

**Rôle :** produire des commits conformes et cohérents avec l’historique.

* `CommitStyleDetector`:

  * lit `git log` (messages)
  * détecte types dominants, scope usage, breaking changes, format footers
* `CommitMessageBuilder`:

  * construit message (type/scope/subject/body/footers)
  * option “commitizen” si présent (mais pas obligatoire)
* `CommitGuard`:

  * refuse commit si pre-commit/test required non passés (ou marque “draft”)

**Pourquoi :** la sortie doit être merge-ready.

---

### F. `tasks/` — Task model + DAG (Curry/Dask)

**Rôle :** représenter et exécuter des tâches.

* `Task` (spec): id, inputs, outputs, deps, resources, timeout, retry policy
* `TaskRunner` (engine): exécute localement ou via Dask
* `ArtifactStore`: stocke outputs (diff, logs, metrics, reports)
* Types de tasks:

  * `PlanTask` (IA) → produit DAG + intent
  * `CodeEditTask` → modifie worktree (text/AST)
  * `LintTask`, `PreCommitTask`, `TestTask`, `CoverageTask`
  * `AnalyzeTask` (duplication, imports, etc.)
  * `SyncTask` (fetch/poll remote)
  * `MonitorTask` (diff stats, cognitive load score)

**Pourquoi :** tout doit être orchestrable, rejouable, composable.

---

### G. `codeops/` — Editing engines (text + AST optionnel)

**Rôle :** appliquer des changements au code dans un worktree.

* `TextPatchEngine` (MVP): applique patch/diff (unifié) + garde-fous
* `AstPatchEngine` (option): parse/transform/dump
* Toujours: produire `ChangeSet` (liste normalisée des fichiers + hunks + summary)

**Pourquoi :** ton AST approche est super, mais en MVP tu veux au moins un patch engine fiable.

---

### H. `analysis/` — Continuous analysis (proactive)

**Rôle :** watchers + heuristiques + propositions.

* Déclencheurs:

  * fin de chain de tâches
  * détection remote commit
  * changements imports
  * duplication / complexité
* Sortie: `SuggestionEvent` → peut créer branches “improvement”
* Doit être “non-intrusif” : propose, n’impose pas.

---

### I. `sync/` — Multi-device continuity

**Rôle :** synchroniser l’état et détecter modifications externes.

* `GitRemoteWatcher`: fetch régulièrement, compare heads, détecte nouveaux commits
* `StateSync`: push/pull `.jean-michel/` (optionnel via service `jean-michel.tech`)
* `TriggerOnRemoteChange`: génère tasks (analysis/monitoring) automatiquement

**Important :** Git reste source de vérité pour le code; `.jean-michel` est la “méta”.

---

### J. `dashboard/` — API + UI

**Rôle :** exposer l’état, les branches, les metrics, et les actions d’intégration.

* Backend: FastAPI
* Front: React/Next ou simple HTMX au début
* Vues clés:

  * timeline
  * branches/worktrees list + diff size + score (green/orange/red)
  * feature graph + conflicts
  * suggestions queue
  * task graph execution view (DAG)

---

## 3) Flux d’exécution (end-to-end)

### 3.1 Message → Plan → DAG → Worktrees → Commits → Monitoring

1. Dev écrit dans timeline.
2. `Scheduler` lit les nouveaux messages (cursor).
3. `Planner` (IA ou règles) produit un **Intent** + un **TaskGraph**.
4. `PolicyEngine` valide le plan (scopes/constraints).
5. `TaskRunner` exécute:

   * create worktree
   * edit code
   * lint/pre-commit
   * tests/coverage
   * commitology commit
   * monitoring
6. Le scheduler écrit une réponse dans timeline + un `BranchUpdateEvent`.
7. Dashboard affiche.

### 3.2 Nouvel événement remote (phone GitHub) → Analysis

1. `SyncTask` fetch remote.
2. `RepoInspector` détecte diff/commit.
3. `analysis/` propose: “ce changement touche feature X, lancer tests/coverage ?”
4. Scheduler poste dans timeline.

---

## 4) Le “Scheduler” (le cerveau derrière le chatter)

Je le coderais comme un **process** qui:

* maintient un cursor sur la timeline,
* produit des décisions (réponses / tâches),
* orchestre via Curry/Dask,
* met à jour l’état via événements.

### Sous-composants

* `TimelineConsumer`
* `IntentExtractor` (peut être simple au début)
* `Planner` (LLM optional)
* `PolicyGate`
* `GraphDispatcher`
* `ResultSummarizer` (écrit dans timeline)
* `Reconciler` (intègre résultats, met à jour projections)

**Important :** le scheduler n’a pas besoin d’être “smart” en MVP. Il peut être un routeur déterministe.

---

## 5) Structure de repo پیشنillée

```text
jean_michel/
  __init__.py
  cli.py
  timeline/
  state/
  policy/
  gitx/
  commitology/
  tasks/
  codeops/
  analysis/
  sync/
  dashboard/
  models/          # Pydantic models / dataclasses partagés
  utils/
```

Dans le repo user:

```text
.jean-michel/
  config.toml
  timeline.db (ou timeline/*.jsonl)
  features/
    users.toml
    auth.toml
  constraints.toml
  branches.json
  metrics/
  artifacts/
```

---

## 6) MVP réaliste (sans perdre l’ambition)

Pour livrer vite sans te cramer:

### MVP 1

* timeline (SQLite)
* worktree manager
* commitology minimal (conventional commit enforced)
* policy scopes minimal (glob allow/deny)
* task engine (local runner, Curry optional)
* monitoring diff stats + dashboard minimal (FastAPI endpoints)

### MVP 2

* continuous analysis (imports/duplication basique)
* coverage tasks + auto “write tests” trigger (même heuristique)
* multi-device watcher (git fetch polling)

### MVP 3

* AST editing engine
* service jean-michel.tech (state relay)
* feature graph + conflict resolver suggestions

---

## 7) Points difficiles à sécuriser dès le début

* **Reproductibilité**: chaque tâche doit enregistrer inputs/outputs.
* **Atomicité Git**: pas de half-commits, pas de dirty worktrees.
* **Policy enforcement**: toute édition passe par `PolicyGate`.
* **Gestion concurrence**: lock par worktree + lock repo global pour opérations sensibles (fetch, gc, etc.).
* **Ergonomie**: dashboard = priorité, sinon l’utilisateur se noie.

---

Si tu veux, je peux enchaîner immédiatement avec la “deuxième chose” que tu mentionnais (tu as dit “deux choses”), et te proposer soit:

* une arborescence `.jean-michel/` + schémas TOML/JSON,
* ou un squelette de classes Python (Pydantic/dataclasses) pour `Feature`, `Constraint`, `Task`, `ChangeSet`, `Branch`, `Event`.
