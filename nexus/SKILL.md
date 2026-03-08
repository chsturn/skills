---
name: nexus
description: >
  Project operating mode for Chris' personal software projects such as HSV,
  Sentinel Trader, Wine, Dopamind, and similar new projects. Trigger when the
  user invokes /nexus, mentions one of these project names in a work context, or
  asks for personal project work such as features, CI/CD, reviews, architecture,
  stack decisions, or deployments. Always load Chris Coding Standards from
  carlo_memory first, then check relevant reference projects if needed, and only
  then fall back to generic best practices.
---

# Nexus

Load the project context first, then choose the right workflow.

## Core rules

- Treat `carlo_memory` as the first source for standards, preferences, infra, and prior decisions.
- Prefer **Chris Coding Standards** over generic best practices.
- Use existing projects as implementation references only after checking memory.
- For project-specific work, look for the closest matching reference among HSV, Sentinel Trader, Wine, and Dopamind.
- Keep responses and plans practical.
- If a command would change external systems (GitHub, deploys, production config), require explicit user intent unless already provided.

## Memory & standards access

### Fixed memory services
- FalkorDB / Graph: `192.168.178.100:6379`
- FalkorDB Browser: `http://192.168.178.100:3000`
- Qdrant: `http://192.168.178.100:6333`
- Ollama Embeddings: `http://192.168.178.100:11434`

### How to query `carlo_memory`
Use the bundled helper:
- `scripts/query_memory.sh '<cypher>'`

Typical examples:
- Project context:
  - `scripts/query_memory.sh 'MATCH (p:Project {name:"HSV"})-[r]-(n) RETURN p.name, type(r), labels(n), coalesce(n.name,n.title,n.hostname)'`
- Coding standards:
  - `scripts/query_memory.sh 'MATCH (:StandardSet {name:"Chris Coding Standards"})-[:CONTAINS]->(:StandardSection)-[:CONTAINS]->(r:Rule) RETURN r.title, r.category, r.scope LIMIT 20'`
- Infra/deploy context:
  - `scripts/query_memory.sh 'MATCH (p:Project {name:"HSV"})-[r]-(n) RETURN type(r), labels(n), coalesce(n.name,n.hostname,n.title)'`

### Coding standards source
Read `references/coding-standards-source.md`.

Primary rule:
- Use `carlo_memory` first for standards.
- Use the original wiki only as fallback.

### Project lookup fallback
Read `references/project-registry.md` if the target project is unclear.

Primary rule:
- Resolve repo/host/location from `carlo_memory` first.
- If memory is incomplete, inspect GitHub context.
- If still unclear, ask instead of guessing.

### Failure mode
If `carlo_memory` is unreachable:
1. Say clearly that memory is unavailable.
2. Use bundled references plus current repo context as fallback.
3. Ask the user for missing project/infra details instead of inventing them.

## Standard workflow (all subcommands)

For every `/nexus ...` request:
1. Determine the subcommand and target project.
2. Query `carlo_memory`.
3. Load **Chris Coding Standards**.
4. Resolve where the project lives (GitHub, local repo, or remote host) at runtime.
5. Inspect the target repo and reference repos if relevant.
6. Execute or propose the work.

## Subcommand-specific additions

### `/nexus feature ...`
- Use for new features, logic changes, report/calculation changes, and refactors in an existing project.
- After implementation, review the result against Chris Coding Standards.

### `/nexus cicd ...`
- Use for standard CI/CD stacks, GitHub Actions, build/test/release pipelines, and Docker build/deploy flows.
- Prefer practical defaults and query memory for registry/deploy style before proposing a pipeline.

### `/nexus review ...`
- Use for code review, PR review, and standards-fit review.
- Report findings in this order:
  1. correctness
  2. security
  3. maintainability
  4. standards fit

### `/nexus architecture ...`
- Use for stack choices, project bootstrap, folder structure, service boundaries, and frontend/backend architecture.
- Recommend one best path first; mention alternatives only if they matter.

## Output style

- Be concise.
- Recommend one best path first.
- Ground suggestions in Chris' standards and existing project patterns.
- Avoid generic boilerplate when a project-specific answer is possible.
