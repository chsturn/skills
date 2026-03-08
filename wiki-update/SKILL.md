---
name: wiki-update
description: >
  Use when the user wants to update an existing wiki page after code changes,
  sync wiki documentation with current code state, or update DORA ticket statuses.
  Triggers: "wiki-update", "wiki aktualisieren", "update wiki", "wiki sync",
  "DORA status update", "dokumentation aktualisieren".
version: 1.0.0
---

# Wiki-Update Skill

Aktualisiert eine bestehende Wiki.js-Seite basierend auf dem aktuellen Code-Stand. Vergleicht Wiki-Inhalt mit Codebase (und optional Refactoring-Plan), identifiziert veraltete Abschnitte und aktualisiert sie gezielt.

**Abgrenzung:**
- `/wiki` erstellt eine **komplett neue Seite** aus dem Code (CREATE)
- `/wiki-refactor` liest eine Wiki-Seite und generiert einen **Refactoring-Plan** (READ)
- `/wiki-update` aktualisiert eine **bestehende Seite** — behält Struktur und unveränderte Abschnitte bei (UPDATE)

## Voraussetzungen prüfen

Vor jeder Ausführung prüfen:

1. **WIKI_API_KEY**: Umgebungsvariable muss gesetzt sein. Falls nicht → User nach dem Key fragen.
2. **Projekt-Erkennung**: Das aktuelle Working Directory gegen die Projekt-Konfiguration in `/Users/chsturn/dev/private/wiki/.claude/wiki-projects.json` matchen. Den CWD-Pfad nach bekannten `pathPatterns` durchsuchen. Falls kein Match → den User fragen welches Projekt gemeint ist.

## Argument-Parsing

Den User-Input nach dem `/wiki-update`-Aufruf parsen:

| Input | Beschreibung |
|-------|-------------|
| `/wiki-update <feature-name>` | Feature-Seite aktualisieren (Kurzname-Auflösung) |
| `/wiki-update <voller-wiki-pfad>` | Wiki-Seite per vollem Pfad aktualisieren |

### Kurzname-Auflösung

Wenn der Input kein `/` enthält, ist es ein Kurzname. Auflösung:
1. Zuerst `{wikiBase}/features/{name}` versuchen
2. Dann `{wikiBase}/architektur/{name}` versuchen
3. Dann `{wikiBase}/compliance/{name}` versuchen
4. Falls keiner funktioniert → User fragen

Wobei `{wikiBase}` aus `wiki-projects.json` kommt (z.B. `projekte/estably`).

## Workflow

### Phase 1: Bestehende Wiki-Seite per GraphQL laden

Die Page-ID aus `wiki-projects.json` nachschlagen und den aktuellen Content direkt aus dem Wiki laden:

```bash
curl -s -X POST http://192.168.178.67:3100/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $WIKI_API_KEY" \
  -d '{ "query": "{ pages { single(id: <page-id>) { content } } }" }'
```

Falls die Page-ID nicht in `wiki-projects.json` steht, die Pages-Liste durchsuchen:

```bash
curl -s -X POST http://192.168.178.67:3100/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $WIKI_API_KEY" \
  -d '{ "query": "{ pages { list(orderBy: TITLE) { id path title } } }" }'
```

Dann die passende Seite per Pfad finden und die ID für Updates verwenden.

Falls keine Seite gefunden → Abbruch mit Hinweis: "Keine Wiki-Seite gefunden. Verwende `/wiki` um eine neue Seite zu erstellen."

### Phase 2: Codebase analysieren (Ist-Zustand)

Die Codebase systematisch analysieren — gleiche Suchstrategie wie beim `/wiki` Skill:

1. **Schemas suchen**: `Glob: server/schemas/*{feature}*`
2. **Routes suchen**: `Glob: server/src/routes/*{feature}*`
3. **Services suchen**: `Glob: server/src/services/{feature}/**/*.js`
4. **Controller suchen**: `Glob: server/src/controllers/{feature}/**/*.js`
5. **Middleware suchen**: `Glob: server/src/routes/middleware/*`
6. **Frontend suchen**: `Glob: web/apps/**/*{feature}*/**/*.ts`
7. **Config prüfen**: `Read: server/config.js` (für Feature-relevante Konfiguration)

Alle gefundenen Dateien lesen und den **aktuellen Implementierungsstand** erfassen.

### Phase 3: Refactoring-Plan lesen (optional)

Prüfe ob ein Refactoring-Plan existiert unter:
`{projekt-root}/.claude/refactor-plans/{feature-name}/`

Falls vorhanden:
- `tasks.md` lesen → Welche Tasks wurden umgesetzt (Checkbox checked)?
- `plan.md` lesen → Was war der Plan?
- Diese Informationen als zusätzlichen Kontext für das Diff verwenden

### Phase 4: Diff bestimmen

Für **jeden Abschnitt** der Wiki-Seite prüfen:

1. Stimmt der dokumentierte Zustand noch mit dem Code überein?
2. Gibt es neue Konzepte im Code die nicht dokumentiert sind?
3. Gibt es dokumentierte Konzepte die im Code nicht mehr existieren?

Die Update-Regeln aus `references/update-rules.md` laden und beachten.

**Typische Änderungskategorien:**
- **Konfigurationswerte**: Timeout-Werte, Salt-Runden, Token-Lebensdauer geändert
- **Architektur-Änderungen**: Neue Middleware, geänderter Stack, neues Auth-Verfahren
- **Neue Features**: Audit-Logging, Token Rotation, Passwort-Historie
- **Entfernte Features**: Session-basierte Auth, veraltete Endpoints
- **Dependency-Updates**: Neue Versionen, ersetzte Packages
- **DORA-Status**: Tickets von "Offen" auf "Erledigt" setzen

### Phase 5: Wiki-Content aktualisieren

Den in Phase 1 geladenen Markdown-Content im Speicher bearbeiten. Die Änderungen basierend auf dem Code-Diff (Phase 4) vornehmen:

1. **Bestehende Abschnitte aktualisieren**: Veraltete Werte, Konfigurationen, Beschreibungen anpassen
2. **Neue Abschnitte einfügen**: Nur wenn der Code ein komplett neues Konzept einführt
3. **Veraltete Abschnitte entfernen/ersetzen**: Nur wenn die dokumentierte Funktionalität nicht mehr existiert
4. **DORA-Ticket-Status aktualisieren**: "Offen" → "Erledigt" für umgesetzte Tickets
5. **Tabellen aktualisieren**: Zusammenfassungstabellen mit aktuellem Status

### Phase 6: Per GraphQL ins Wiki pushen

Den aktualisierten Content per GraphQL Update-Mutation ins Wiki schreiben:

```bash
curl -s -X POST http://192.168.178.67:3100/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $WIKI_API_KEY" \
  -d '{
    "query": "mutation($id: Int!, $content: String!, $tags: [String]!) { pages { update(id: $id, content: $content, tags: $tags, isPublished: true) { responseResult { succeeded message } } } }",
    "variables": { "id": <page-id>, "content": "<aktualisierter-markdown-inhalt>", "tags": ["tag1", "tag2"] }
  }'
```

**Wichtig:** `isPublished: true` immer mitsenden. Antwort auf `responseResult.succeeded` prüfen.

### Phase 7: Ausgabe an den User

Dem User mitteilen:

1. **Welche Seite aktualisiert wurde** (Titel, Wiki-URL, Page-ID)
2. **Was geändert wurde** (Liste der aktualisierten Abschnitte)
3. **DORA-Tickets** die auf "Erledigt" gesetzt wurden (falls zutreffend)
4. **GraphQL-Status** (Erfolg/Fehler)

## Sicherheitsregeln

- NIEMALS WIKI_API_KEY in generierten .md-Dateien
- Keine internen IP-Adressen oder Hostnamen in Output-Dateien (Wiki-Pfade statt volle URLs)
- Keine exploitbaren Endpunkt-Details (keine Auth-Payloads, keine Token-Formate)
- Keine Secrets, Passwörter oder Tokens aus dem Quellcode in die Wiki-Seite kopieren
- Sensible Datenfelder nur als Konzept erwähnen, nicht mit Beispielwerten
