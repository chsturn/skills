---
name: nexus
description: >
  Project operating mode for Chris' personal software projects such as HSV,
  Sentinel Trader, Wine, Dopamind, and similar new projects. Use when the user
  invokes /nexus or asks for project work like feature changes, CI/CD setup or
  improvements, code or PR review, and architecture, stack, or project bootstrap
  decisions. Always load Chris Coding Standards from carlo_memory first, then
  check relevant reference projects if needed, and only then fall back to
  generic best practices.
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

## Memory & environment

### Fixed memory endpoint
- Memory / GraphRAG: `192.168.178.100`

### Important rule
- For deploy topics, infra questions, SSH targets, host selection, server roles, and runtime environment details: **query `carlo_memory` first instead of relying on hardcoded host knowledge in the skill**.
- Do not assume a local checkout exists; resolve whether the work should happen via GitHub, a local repo, or a remote host at runtime.
- Prefer read-only inspection first.

## Subcommands

## `/nexus feature ...`

Use for:
- new features
- logic changes
- report/calculation changes
- refactors inside an existing project

Workflow:
1. Identify the target project.
2. Query `carlo_memory` for project context, standards, and previous related work.
3. Check **Chris Coding Standards** relevant to the change.
4. Inspect the target repo and, if useful, similar implementations in reference projects.
5. Propose or implement the change.
6. Review the result against Chris Coding Standards.

## `/nexus cicd ...`

Use for:
- standard CI/CD stacks
- GitHub Actions
- build/test/release pipelines
- Docker build/deploy flows

Workflow:
1. Query `carlo_memory` for infra context, registry, deploy style, and prior CI/CD patterns.
2. Load **Chris Coding Standards** relevant to testing, security, dependencies, and project structure.
3. Inspect existing CI/CD implementations in reference projects if relevant.
4. Propose a standard stack tailored to Chris' environment.
5. Prefer practical defaults over abstract options.

## `/nexus review ...`

Use for:
- code review
- PR review
- “is this clean?”
- “does this fit our standards?”

Workflow:
1. Load **Chris Coding Standards** first.
2. Inspect the changed code.
3. Compare against project style and reference implementations if needed.
4. Report findings in priority order:
   - correctness
   - security
   - maintainability
   - standards fit
5. Be direct and specific.

## `/nexus architecture ...`

Use for:
- standard stack choices
- project bootstrap
- folder structure
- service boundaries
- frontend/backend architecture

Workflow:
1. Query `carlo_memory` for standards, infra, and project preferences.
2. Load **Chris Coding Standards** sections relevant to architecture.
3. Use reference projects to infer the lived standard when useful.
4. Propose one recommended architecture first; mention alternatives only if they matter.

## Minimal operating sequence

For every `/nexus ...` request:
1. Determine the subcommand and target project.
2. Query `carlo_memory`.
3. Load **Chris Coding Standards**.
4. Resolve where the project lives (GitHub, local repo, or remote host) at runtime.
5. Inspect the target repo and reference repos if relevant.
6. Execute or propose the work.

## Memory guidance

Look for these first:
- `Chris Coding Standards`
- project nodes (`HSV`, `Sentinel Trader`, `Wine`, `Dopamind`)
- infra/deploy context
- coding preferences

## Output style

- Be concise.
- Recommend one best path first.
- Ground suggestions in Chris' standards and existing project patterns.
- Avoid generic boilerplate when a project-specific answer is possible.
