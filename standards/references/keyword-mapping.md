# Keyword-Mapping Referenz

Mapping von Keywords zu Wiki.js-Seiten-IDs für den `/standards` Skill.

**Datenquelle:** Wiki.js GraphQL API — NICHT lokale Dateien.

## Einzelne Keywords

| Keyword(s) | Wiki-Seiten-ID | Wiki-Pfad | Titel |
|---|---|---|---|
| `general`, `coding` | **14** | `shared/coding-standards` | Coding Standards |
| `angular`, `frontend`, `fe` | **77** | `shared/coding-standards/angular` | Angular – Coding Standards |
| `node`, `nodejs`, `backend`, `be` | **78** | `shared/coding-standards/nodejs` | Node.js – Coding Standards |
| `testing`, `tests`, `test` | **79** | `shared/coding-standards/testing` | Testing Standards |
| `infra`, `docker`, `deploy`, `ci` | **22** | `shared/infrastructure` | Docker Swarm – Infrastruktur & Auto-Deploy Guide |
| `security`, `sec` | **78** | `shared/coding-standards/nodejs` (Security-Abschnitte) | Node.js – Coding Standards |
| `dora` | **30** | `compliance/dora` | DORA – Übersicht & Compliance-Matrix |
| `compliance` | **29**, **35** | `compliance`, `compliance/gap-analyse` | Compliance + Gap-Analyse |

## Meta-Keywords

Meta-Keywords expandieren zu mehreren Einzel-Keywords. `general` wird immer automatisch mit geladen.

| Meta-Keyword | Expandiert zu | Wiki-IDs |
|---|---|---|
| `all` | `general` + `angular` + `nodejs` + `testing` + `infra` | 14, 77, 78, 79, 22 |
| `fullstack` | `general` + `angular` + `nodejs` + `testing` | 14, 77, 78, 79 |
| `frontend-full` | `general` + `angular` + `testing` | 14, 77, 79 |
| `backend-full` | `general` + `nodejs` + `testing` | 14, 78, 79 |

## Projekt-Keyword

| Keyword | Verhalten |
|---|---|
| `project` | CWD gegen `wiki-projects.json` matchen (`/Users/chsturn/dev/private/wiki/.claude/wiki-projects.json`). Das `pathPatterns`-Array des Projekts gegen den CWD-Pfad prüfen. Bei Match: Projekt-Docs per Wiki-API laden. |

## Laden per GraphQL API

Alle aufgelösten Wiki-IDs in **einem einzigen** Bash-Aufruf laden:

```bash
WT=$(cat ~/.claude/.wiki-token) && for id in <id1> <id2> <id3>; do
  echo "=== PAGE $id ==="
  curl -s -X POST 'http://192.168.178.67:3100/graphql' \
    -H 'Content-Type: application/json' -H "Authorization: Bearer $WT" \
    -d "{\"query\":\"{ pages { single(id: $id) { id title content } } }\"}"
  echo
done
```

**WICHTIG:** Token immer mit `WT=$(cat ~/.claude/.wiki-token)` laden. Nie `source ~/.zshrc`, nie `$WIKI_API_KEY` annehmen.

## Pflege

Wenn neue Wiki-Seiten hinzukommen:
1. Neues Keyword, Wiki-Seiten-ID und Pfad in die Tabelle "Einzelne Keywords" eintragen.
2. Falls sinnvoll, bestehende Meta-Keywords erweitern oder neue anlegen.
3. Die SKILL.md muss nicht angepasst werden — sie referenziert diese Datei dynamisch.
