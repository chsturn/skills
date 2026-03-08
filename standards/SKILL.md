---
name: standards
description: >
  Use when the user wants to load coding standards, testing guidelines, infrastructure docs,
  or compliance references from the wiki. Trigger on: "/standards", "standards laden",
  "coding standards", "load standards", "Richtlinien laden", "welche Regeln gelten",
  "Coding-Regeln", "Testing-Richtlinien", "DORA standards", "compliance standards".
  Also trigger when the user asks about coding conventions, best practices, or guidelines
  before starting implementation work, or says things like "was sind unsere Standards"
  or "zeig mir die Richtlinien".
version: 3.0.0
---

# Standards Skill

Lade Coding Standards, Testing-Richtlinien, Infrastruktur-Docs und Compliance-Referenzen direkt aus Wiki.js als verbindlichen Kontext.

## Datenquelle

- **Source of Truth:** Wiki.js GraphQL API (`http://192.168.178.67:3100/graphql`)
- **Auth:** Token aus `~/.claude/.wiki-token`
- **WICHTIG:** Standards werden IMMER aus dem Wiki geladen, NIEMALS von lokalen Dateien.
- **Keyword-Mapping:** `references/keyword-mapping.md` laden für das Mapping von Keywords zu Wiki-Seiten-IDs.

## Voraussetzungen

Vor dem Laden prüfen:

### 1. Token verfügbar

```bash
WT=$(cat ~/.claude/.wiki-token) && echo "Token geladen (${#WT} Zeichen)"
```

Falls die Datei fehlt → User informieren und abbrechen.

### 2. Wiki erreichbar

```bash
WT=$(cat ~/.claude/.wiki-token) && curl -s --connect-timeout 5 -X POST 'http://192.168.178.67:3100/graphql' \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $WT" \
  -d '{"query":"{ pages { list(limit: 1) { id } } }"}' | head -c 200
```

Falls Timeout → User informieren: "Wiki nicht erreichbar. Netzwerk/VPN prüfen."

## Workflow

1. **Argumente parsen**: User-Input nach `/standards` in Keywords aufteilen (Leerzeichen-getrennt).
2. **Keyword-Mapping laden**: `references/keyword-mapping.md` aus dem Skill-Verzeichnis lesen.
3. **Keywords auflösen**:
   - Meta-Keywords (`all`, `fullstack`, `frontend-full`, `backend-full`) zu Einzel-Keywords expandieren.
   - `general` wird bei allen Meta-Keywords automatisch mit geladen.
   - Duplikate entfernen.
4. **Sonderfall `project`**: CWD gegen `wiki-projects.json` matchen (Pfad: `/Users/chsturn/dev/private/wiki/.claude/wiki-projects.json`). Falls Match → Projekt-Docs laden. Falls kein Match → User fragen.
5. **Sonderfall `security`**: Security-relevante Abschnitte aus Node.js Standards laden (Wiki-ID 78).
6. **Seiten aus Wiki laden**: Alle gemappten Wiki-IDs in einem Bash-Aufruf laden:

```bash
WT=$(cat ~/.claude/.wiki-token) && for id in <id1> <id2> <id3>; do
  echo "=== PAGE $id ==="
  curl -s -X POST 'http://192.168.178.67:3100/graphql' \
    -H 'Content-Type: application/json' -H "Authorization: Bearer $WT" \
    -d "{\"query\":\"{ pages { single(id: $id) { id title content } } }\"}"
  echo
done
```

**WICHTIG:** Token immer aus File laden mit `WT=$(cat ~/.claude/.wiki-token)`. Nie hardcoden, nie `source ~/.zshrc` verwenden.

7. **Ausgabe**: Geladene Standards als verbindliche Richtlinien zusammenfassen, dem User bestätigen welche Standards geladen wurden.

## Ohne Argumente (`/standards`)

Falls ohne Argumente aufgerufen, den Hilfe-Text ausgeben:

```
/standards — Coding Standards laden (aus Wiki.js)

Verfügbare Keywords:
  general, coding          → Allgemeine TypeScript/Coding Standards
  angular, frontend, fe    → Angular Frontend Standards
  node, nodejs, backend, be → Node.js Backend Standards
  testing, tests, test     → Testing-Richtlinien
  infra, docker, deploy, ci → Infrastruktur & Deployment
  security, sec            → Security-Standards (aus Node.js)
  dora                     → DORA-Compliance
  compliance               → Compliance Overview + Gap-Analyse
  project                  → Projekt-spezifische Docs (CWD-Erkennung)

Meta-Keywords (laden mehrere Bereiche):
  all                      → general + angular + nodejs + testing + infra
  fullstack                → general + angular + nodejs + testing
  frontend-full            → general + angular + testing
  backend-full             → general + nodejs + testing

Beispiele:
  /standards angular testing     → Angular + Testing + General
  /standards backend-full        → Node.js + Testing + General
  /standards all                 → Alle Shared Standards
  /standards infra               → Infrastruktur/Docker/CI-CD
  /standards project             → Projekt-Docs (CWD-Erkennung)
```

## Fehlerbehandlung

| Fehler | Aktion |
|--------|--------|
| Token-Datei fehlt | User: "`~/.claude/.wiki-token` nicht gefunden" |
| Wiki nicht erreichbar | User: "Wiki nicht erreichbar. Netzwerk/VPN prüfen." |
| Seite nicht gefunden (404/null) | Warnung ausgeben, restliche Seiten trotzdem laden |
| Unbekanntes Keyword | User darauf hinweisen, Hilfe-Text anzeigen |

## Ausgabe-Format

Nach dem Laden:

1. **Bestätigung**: Welche Standards geladen wurden (Bereiche + Wiki-Seiten-IDs)
2. **Zusammenfassung**: Kurze Übersicht der wichtigsten Regeln
3. **Hinweis**: "Diese Standards gelten als verbindliche Richtlinien für die aktuelle Konversation."

## Sicherheitsregeln

- Keine Secrets oder API-Keys aus den Standards-Seiten exponieren
- Standards nur lesen, nie über die API modifizieren
- Token niemals hardcoden oder in Ausgaben anzeigen
