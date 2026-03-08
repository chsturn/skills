# Gemeinsame Workflow-Phasen

Wiederverwendbare Phasen für alle Analyse-Typen (functional, security, dora).

## Phase: Code im Projekt finden

Den Feature-Namen als Suchbegriff verwenden:

```
# Schema/Model
Glob: **/schemas/*{feature}*
Glob: **/models/*{feature}*

# Backend-Services
Glob: **/services/**/*{feature}*
Glob: **/controllers/**/*{feature}*
Glob: **/modules/**/*{feature}*

# Routes
Grep: "{feature}" in routes/
Glob: **/routes/*{feature}*

# Frontend-Components
Glob: **/{feature}/**/*.ts
Glob: **/{feature}/**/*.html
```

Falls kein direkter Match über den Dateinamen:
- In `package.json` nach verwandten Dependencies suchen
- In Route-Definitionen nach URL-Patterns suchen
- In Schema-Dateien nach Feldern suchen die zum Feature gehören
- Grep mit Varianten des Feature-Namens (camelCase, kebab-case, etc.)

## Phase: Index-Seiten aktualisieren

Nach dem Push einer Feature-Seite die Index-Seiten aktualisieren.

### Welchen Index aktualisieren?

| Analyse-Typ | Index-Seite | Page-ID Feld |
|-------------|------------|--------------|
| `functional` | Features-Index | `featuresIndexPageId` |
| `security` | Security-Index | `securityIndexPageId` |
| `dora` | Security-Index | `securityIndexPageId` |

### Ablauf

1. **Index laden** (Page-ID aus `wiki-projects.json`):

```bash
WT=$(cat ~/.claude/.wiki-token) && curl -s -X POST 'http://192.168.178.67:3100/graphql' \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $WT" \
  -d '{"query":"{ pages { single(id: <pageId>) { id title content } } }"}'
```

2. **Link ergaenzen** falls das Feature noch nicht gelistet ist:

Fuer functional (unter der passenden Gruppe):
```markdown
- [{Feature-Titel}](/{wikiBase}/features/{gruppe}/{feature}) – {Kurzbeschreibung}
```

Fuer security/dora:
```markdown
- [{Feature-Titel} (Security)](/{wikiBase}/security/reviews/{feature}-security)
- [{Feature-Titel} (DORA)](/{wikiBase}/security/reviews/{feature}-dora)
```

3. **Aktualisierten Index in /tmp schreiben und per wiki-push.mjs updaten:**

```bash
WIKI_API_KEY=$(cat ~/.claude/.wiki-token) node /Users/chsturn/.claude/skills/wiki/scripts/wiki-push.mjs \
  update --id <pageId> \
  --file /tmp/wiki-index.md \
  --title "<Index-Titel>" \
  --tags "<tags>"
```

Falls die Page-ID null ist -> Index-Update ueberspringen.

## Formatierungsregeln

Gelten für alle Analyse-Typen:

- **Sprache**: Deutsch (wie die bestehenden Wiki-Seiten)
- **Tabellen** bevorzugen für strukturierte Daten
- **ASCII-Diagramme** für Prozessflüsse und State Machines (kein Mermaid — Wiki.js rendert es nicht zuverlässig)
- **Code-Blöcke** nur für Datenstrukturen, nie für tatsächlichen Quellcode
- **Keine Zeilennummern** oder Dateiverweise im Markdown (Doku soll unabhängig vom Code lesbar sein)
- Trennlinien (`---`) zwischen Hauptabschnitten
- **Keine Secrets/IPs** — siehe Sicherheitsregeln in SKILL.md
