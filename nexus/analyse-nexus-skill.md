# Nexus Skill — Analyse & Optimierungsvorschläge

## Was gut funktioniert

- Klare Subcommand-Struktur (`feature`, `cicd`, `review`, `architecture`)
- Konsistenter Workflow-Ablauf (Memory → Standards → Inspect → Execute)
- Guter Output-Style-Abschnitt

---

## Optimierungsvorschläge

### 1. `carlo_memory` ist unklar — wie wird darauf zugegriffen?

Der Skill referenziert `carlo_memory` 10x, aber es gibt keine Anweisung **wie** darauf zugegriffen wird. Der Skill nennt FalkorDB/Qdrant-Endpoints, aber keine Queries, kein Tool, kein CLI-Befehl. Claude wird bei jeder Ausführung raten müssen, was "query carlo_memory" bedeutet.

**Vorschlag:** Einen konkreten Abschnitt hinzufügen:

```markdown
## How to query carlo_memory
- FalkorDB graph query via: `redis-cli -h 192.168.178.100 -p 6379 GRAPH.QUERY carlo_memory "MATCH ..."`
- Oder: konkretes Tool/Script benennen
- Beispiel-Queries für typische Lookups (Standards, Projekt-Context, Infra)
```

### 2. "Chris Coding Standards" — Quelle fehlt

Der Skill sagt "load Chris Coding Standards", aber nicht **wo** sie liegen. In der CLAUDE.md gibt es die Wiki.js-Seiten (IDs 14, 77, 78, 79). Der Nexus-Skill sollte darauf verweisen oder die Standards als `references/`-Datei bundlen.

**Vorschlag:** Entweder direkt referenzieren:

```markdown
## Chris Coding Standards
Load from Wiki.js (see CLAUDE.md for token/endpoint):
- General TypeScript: Page 14
- Angular Frontend: Page 77
- Node.js Backend: Page 78
- Testing: Page 79
```

Oder den `/standards`-Skill aufrufen lassen.

### 3. Referenzprojekte sind nicht auffindbar

Der Skill nennt HSV, Sentinel Trader, Wine, Dopamind — aber keine Pfade, keine GitHub-URLs, keine Repos. Claude kann nicht "inspect the target repo" wenn es nicht weiss, wo das Repo liegt.

**Vorschlag:** Entweder Pfade/URLs in `carlo_memory` speichern (und das Query dafür dokumentieren), oder eine einfache Lookup-Tabelle direkt im Skill:

```markdown
## Reference Projects
| Project | Repo | Stack |
|---------|------|-------|
| HSV | ~/dev/hsv oder github.com/... | Next.js, ... |
| Sentinel Trader | ... | ... |
```

### 4. Subcommands haben viel Redundanz

Alle 4 Subcommands folgen dem gleichen Muster: Memory → Standards → Inspect → Execute. Die Unterschiede sind minimal. Das bläht den Skill auf ~130 Zeilen auf, wo ~80 reichen würden.

**Vorschlag:** Gemeinsamen Workflow einmal definieren, Subcommands nur mit Deltas:

```markdown
## Standard workflow (all subcommands)
1. Identify target project
2. Query carlo_memory for context
3. Load Chris Coding Standards
4. Inspect target repo (+ reference repos if useful)
5. Execute/propose

## Subcommand-specific additions
- **feature**: Review result against standards after implementation
- **review**: Report in priority order: correctness > security > maintainability > standards
- **cicd**: Prefer practical defaults, check registry/deploy style in memory
- **architecture**: Recommend one path first, alternatives only if they matter
```

### 5. Description könnte aggressiver triggern

Aktuell triggert der Skill nur bei `/nexus` oder expliziter Erwähnung von Projektnamen. Wenn z.B. gesagt wird "ich arbeite am Wine-Projekt, bau mir ein Feature" ohne `/nexus`, könnte der Skill nicht triggern.

**Vorschlag:** Description erweitern:

```yaml
description: >
  Project operating mode for Chris' personal software projects (HSV, Sentinel Trader,
  Wine, Dopamind, and similar). Trigger when: user invokes /nexus, mentions one of these
  project names, asks about personal project work (features, CI/CD, reviews, architecture,
  stack decisions, deployments), or works in a repo that belongs to one of these projects.
  Even if the user just says "deploy the app" or "set up CI" in a personal project context,
  use this skill.
```

### 6. Kein Fallback wenn `carlo_memory` nicht erreichbar ist

Was passiert wenn FalkorDB down ist? Der Skill hat keinen Plan B.

**Vorschlag:**

```markdown
If carlo_memory is unreachable, fall back to:
1. Local .claude/MEMORY.md files in the project
2. Wiki.js pages (standards, decisions)
3. Ask the user for context
Never silently skip the memory step — inform the user.
```

### 7. Bundled Resources fehlen

Der Skill ist eine einzelne SKILL.md ohne `references/` oder `scripts/`. Nützliche Ergänzungen wären:

- `references/coding-standards.md` — gecachte Version der Standards (offline-fähig)
- `scripts/query_memory.sh` — Wrapper für carlo_memory-Queries
- `references/project-registry.md` — Projekt-Übersicht

---

## Zusammenfassung nach Priorität

| Prio | Problem | Impact |
|------|---------|--------|
| **1** | carlo_memory Zugriff undokumentiert | Skill funktioniert nicht zuverlässig |
| **2** | Coding Standards Quelle fehlt | Kernfeature nicht nutzbar |
| **3** | Referenzprojekte nicht auffindbar | Kontextlose Empfehlungen |
| **4** | Redundanz in Subcommands | Unnötig lang, schwerer wartbar |
| **5** | Description zu konservativ | Undertriggering |
| **6** | Kein Fallback-Plan | Fragil bei Ausfällen |
