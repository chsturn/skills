# Output-Struktur: plan.md und tasks.md

Templates für die Hauptdateien des Refactoring-Plans.

---

## plan.md Template

```markdown
# Refactoring Plan: {feature-name}

**Wiki-Quelle:** {wiki-path} (Seite: "{wiki-title}")
**Erstellt:** {datum}
**Projekt:** {projekt-name}

## Kontext

{2-3 Absätze:
- Was dokumentiert die Wiki-Seite?
- Welche Probleme/Gaps wurden identifiziert?
- Warum ist der Refactor notwendig (regulatorisch, technisch)?}

## Scope

**In Scope:**
- {Auflistung was dieser Refactoring-Plan abdeckt}

**Out of Scope:**
- {Was nicht abgedeckt wird und warum}

## Zusammenfassung

| Priorität | Anzahl Tasks | Beschreibung |
|-----------|-------------|-------------|
| P0 (Kritisch) | {n} | {Kurzbeschreibung} |
| P1 (Hoch) | {n} | {Kurzbeschreibung} |
| P2 (Mittel) | {n} | {Kurzbeschreibung} |
| P3 (Niedrig) | {n} | {Kurzbeschreibung} |
| **Gesamt** | **{total}** | |

## Abhängigkeiten

\`\`\`
{ASCII-Diagramm der Task-Abhängigkeiten, z.B.:

01-audit-service ──────────┐
                           ├──→ 03-audit-fees
02-csrf-middleware ────┐   │
                       ├───┤
                       │   └──→ 04-audit-depotstatus
                       └──→ 05-csrf-fees
}
\`\`\`

## Betroffene Dateien

| Datei | Tasks | Änderungstyp |
|-------|-------|-------------|
| {pfad} | {01, 03} | Modify |
| {pfad} | {02} | Create |
| ... | ... | ... |
```

---

## tasks.md Template

```markdown
# Tasks: {feature-name}

**Wiki-Quelle:** {wiki-path}
**Gesamt:** {n} Tasks | **Erstellt:** {datum}

## P0 – Kritisch

- [ ] **01-{slug}** – {Titel}
  DORA Art. {X} | Ticket: {ID}
  Dateien: \`{datei1}\`, \`{datei2}\`
  Abhängigkeiten: keine
  Prompt: \`prompts/01-{slug}.md\`

- [ ] **02-{slug}** – {Titel}
  DORA Art. {X} | Ticket: {ID}
  Dateien: \`{datei1}\`
  Abhängigkeiten: 01-{slug}
  Prompt: \`prompts/02-{slug}.md\`

## P1 – Hoch

- [ ] **03-{slug}** – {Titel}
  ...

## P2 – Mittel

- [ ] **04-{slug}** – {Titel}
  ...

## P3 – Niedrig

- [ ] **05-{slug}** – {Titel}
  ...

---

## Legende

- **Abhängigkeiten:** Tasks die vorher abgeschlossen sein müssen
- **Prompt:** Pfad zum eigenständigen Umsetzungs-Prompt (relativ zu diesem Verzeichnis)
- Checkboxen können manuell abgehakt werden wenn der Task erledigt ist
```

---

## Verzeichnis-Konvention

Der Output wird im Ziel-Projekt unter folgendem Pfad gespeichert:

```
{projekt-root}/.claude/refactor-plans/{feature-name}/
├── plan.md
├── tasks.md
└── prompts/
    ├── 01-{slug}.md
    ├── 02-{slug}.md
    └── ...
```

Dabei ist `{feature-name}` der Name aus dem Wiki-Pfad (z.B. `fees`, `depotstatus`, `auth`).
Und `{slug}` ist eine URL-sichere Kurzform des Task-Titels (z.B. `audit-logging`, `csrf-middleware`, `rate-limiting`).
