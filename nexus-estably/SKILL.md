---
name: nexus-estably
description: >
  Use this skill when the user wants to query, analyze, evaluate, or improve
  the Estably Nexus knowledge system on 192.168.178.100, including search,
  impact, dora, pii, retrieval profiles, FalkorDB/Qdrant data quality,
  mappings, goldensets, or agent usage. Also use it when the user asks where
  code, wiki, DORA, standards, or feature context can be found via Nexus.
---

# Nexus

Use Nexus as the team knowledge layer for `server`, `web`, `broker`, wiki, DORA,
and coding standards.

## Core rules

- Prefer the Nexus API first; use raw graph access only when API behavior or data modeling must be inspected.
- Treat `server` as source of truth for generic technical questions unless the user explicitly asks for `broker` or `web`.
- Use the right retrieval profile:
  - `implementation`: code-first, entrypoints, services, routes, tests
  - `analysis`: balanced technical overview
  - `compliance`: wiki, controls, DORA, standards
  - `bundle_overview`: intentionally mixed top results
- For coding-standards questions, include the `standards` layer alongside code/wiki context.
- Do not touch local MongoDB. Work against Nexus on `.100` only.

## Fixed Nexus endpoints

- API base: `http://192.168.178.100:8080`
- API key: `nexus-estably-2026`
- FalkorDB browser: `http://192.168.178.100:3000`
- Qdrant: `http://192.168.178.100:6333`

## Helper scripts

Use scripts relative to this skill:

- API helper: [`scripts/query_nexus.sh`](scripts/query_nexus.sh)
- Raw graph helper: [`scripts/query_memory.sh`](scripts/query_memory.sh)

Examples:

```bash
./scripts/query_nexus.sh search '{
  "query":"Wo wird estbFeeCalculated berechnet und eingetragen?",
  "profile":"analysis",
  "limit":6
}'
```

```bash
./scripts/query_nexus.sh impact '{
  "path":"broker/packages/backend/src/features/auth/auth.service.ts",
  "profile":"implementation"
}'
```

```bash
./scripts/query_nexus.sh dora '{
  "article":"Article 11",
  "profile":"compliance"
}'
```

For direct graph inspection:

```bash
./scripts/query_memory.sh 'MATCH (f:Feature) RETURN f.id LIMIT 10'
```

## Endpoint selection

### `search`

Use for:
- "where is X implemented?"
- "how is Y built?"
- "what do I need to change?"
- open feature questions that need code + wiki candidates

Guidance:
- Default to `implementation` for coding tasks
- Default to `analysis` for architecture / "how is it built?" questions
- Use `bundle_overview` when the user wants a quick mixed overview

### `impact`

Use for:
- "what is affected by this file?"
- "which wiki, DORA, standards, and data types relate to this path?"
- code review context and security/compliance context

Guidance:
- `implementation` for code-neighbor impact
- `compliance` when DORA/standards matter

### `dora`

Use for:
- article-centric questions
- "what code/wiki is relevant for Art.9 / Article 11?"
- compliance-oriented feature impact

Default profile: `compliance`

### `pii`

Use for:
- finding paths with PII-related handling
- scoping privacy / security review surfaces

## When to use raw graph access

Use raw FalkorDB queries only when you need to inspect or debug:
- node / edge coverage
- duplicate `WikiPage` or `Feature` relationships
- mapping-ingest quality
- why API output is missing a relationship

Prefer API output for normal user-facing answers.

## Working style

- For user questions, return the best answer, not just raw JSON.
- For Nexus improvement work, verify with the endpoint-specific eval scripts in the repo.
- If you change Nexus ranking or ingestion, test against `.100` and report the observed effect.
