---
name: wiki-refactor
description: >
  Use when the user asks to create a refactoring plan from wiki documentation,
  generate implementation prompts, uses "/wiki-refactor", or wants DORA remediation planning.
  Triggers: "wiki-refactor", "refactor plan", "remediation plan", "DORA plan",
  "Umsetzungsplan aus Wiki", "implementation prompts from wiki".
version: 1.0.0
---

# Wiki-Refactor Skill

Liest eine Wiki.js-Seite, extrahiert Actionable Items (DORA-Tickets, Security-Findings, Gaps) und generiert einen strukturierten Refactoring-Plan mit eigenständigen Umsetzungs-Prompts.

## Voraussetzungen prüfen

Vor jeder Ausführung prüfen:

1. **WIKI_API_KEY**: Umgebungsvariable muss gesetzt sein. Falls nicht → Fehler ausgeben und abbrechen.
2. **Projekt-Erkennung**: Das aktuelle Working Directory gegen die Projekt-Konfiguration in `/Users/chsturn/dev/private/wiki/.claude/wiki-projects.json` matchen. Den CWD-Pfad nach bekannten `pathPatterns` durchsuchen. Falls kein Match → den User fragen welches Projekt gemeint ist.
3. **Output-Verzeichnis**: Das Ziel-Verzeichnis ist `{projekt-root}/.claude/refactor-plans/{feature-name}/`. Erstelle es falls nötig.

## Argument-Parsing

Den User-Input nach dem `/wiki-refactor`-Aufruf parsen:

| Input | Beschreibung |
|-------|-------------|
| `/wiki-refactor <name>` | Feature-Seite laden und Plan generieren |
| `/wiki-refactor <voller-pfad>` | Wiki-Seite per vollem Pfad laden |
| `/wiki-refactor security` | Zentrale Security/DORA-Compliance-Seite analysieren |

### Kurzname-Auflösung

Wenn der Input kein `/` enthält, ist es ein Kurzname. Auflösung:
1. Zuerst `{wikiBase}/features/{name}` versuchen
2. Dann `{wikiBase}/architektur/{name}` versuchen
3. Dann `{wikiBase}/compliance/{name}` versuchen
4. Falls keiner funktioniert → User fragen

Wobei `{wikiBase}` aus `wiki-projects.json` kommt (z.B. `projekte/estably`).

## Workflow

### Phase 1: Wiki-Seite abrufen

Das Fetch-Script aufrufen:

```bash
WIKI_API_KEY="$WIKI_API_KEY" node /Users/chsturn/.claude/skills/wiki-refactor/scripts/wiki-fetch.mjs \
  --path "<aufgelöster-wiki-pfad>"
```

Das Script gibt JSON auf stdout aus. Prüfe `ok: true/false`.

Bei **Fehler** (ok: false):
- "Page not found" → Kurzname-Auflösung versuchen (nächsten Pfad probieren)
- Anderer Fehler → User informieren und abbrechen

**Hinweis:** Das Script verwendet die Wiki.js GraphQL-Methode `singleByPath(path, locale)` (nicht `single`). Falls das API-Schema sich ändert, muss `wiki-fetch.mjs` angepasst werden.

Bei **Erfolg** (ok: true):
- `page.content` enthält den Markdown-Inhalt der Wiki-Seite
- `page.title` enthält den Seitentitel
- Weiter mit Phase 2

### Phase 2: Content parsen – Actionable Items extrahieren

Den Markdown-Content der Wiki-Seite analysieren und strukturierte Items extrahieren.

#### 2a: DORA-Ticket-Übersicht

Suche nach der Sektion `### DORA-Ticket-Übersicht` oder `## DORA-Ticket-Übersicht`. Parse die Markdown-Tabelle darunter.

**Erwartete Spalten (2 Varianten):**

Variante 1: `| Ticket | DORA Art. | Beschreibung | Priorität | Status |`
Variante 2: `| Ticket | DORA Art. | Beschreibung | Priorität |` (ohne Status → default "Offen")

**Filter:** Nur Tickets mit Status "Offen" oder fehlendem Status.
**Sortierung:** P0 → P1 → P2 → P3.

Jedes Ticket wird ein `ActionableItem`:
```
{
  ticketId: "ESTB-SEC-FEE-001",
  doraArticle: "Art. 9",
  description: "Audit-Logging für manuelle Fee-Konfigurationsänderungen",
  priority: "P0",
  status: "Offen"
}
```

#### 2b: DORA-Detail-Tabellen

Suche nach Sektionen `### Detail: Artikel X`. Parse die Tabelle darunter.

**Erwartete Spalten:** `| Prüfpunkt | Status | Ist-Zustand | Gap | Empfehlung |`

**Status-Werte:**
- `✅ Erfüllt` → überspringen
- `⚠️ Teilweise` → als ActionableItem erfassen (mittel)
- `❌ Fehlt` oder `❌ Mangelhaft` → als ActionableItem erfassen (hoch)

**Nutze diese Items als Kontext-Anreicherung** für die DORA-Tickets aus 2a. Sie liefern Details zu Gap und Empfehlung.

#### 2c: Weitere Sektionen (optional)

Falls vorhanden, auch folgende Sektionen auswerten:
- **Fehlerbehandlung**: Notierte Lücken oder Probleme
- **API-Endpunkte**: Betroffene Endpoints für Kontext

#### 2d: Konsolidierung

- Merge Detail-Infos (Gap, Empfehlung) mit den zugehörigen Tickets
- Entferne Duplikate (gleiches Ticket kann in Detail und Übersicht erscheinen)
- Sortiere final: P0 → P1 → P2 → P3

### Phase 3: Codebase analysieren

Für **jeden** extrahierten ActionableItem die Codebase des aktuellen Projekts durchsuchen.

#### 3a: Betroffene Dateien identifizieren

Basierend auf dem Feature-Name und der Ticket-Beschreibung suchen:

```
# Routes finden
Glob: server/src/routes/*{feature}*
Glob: server/routes/*{feature}*

# Controller finden
Glob: server/src/controllers/{feature}/**/*.js
Glob: server/controller/{feature}*.js

# Services finden
Glob: server/src/services/{feature}/**/*.js
Glob: server/src/services/**/*{feature}*

# Schemas finden
Glob: server/schemas/*{feature}*
Grep: "{feature}" in server/schemas/

# Frontend (nur wenn Ticket Frontend betrifft)
Glob: web/apps/**/*{feature}*/**/*.ts
```

#### 3b: Relevante Dateien lesen

Die gefundenen Dateien lesen und den **aktuellen Zustand** erfassen:
- Welcher Code muss geändert werden?
- Welche Patterns werden aktuell verwendet?
- Wo fehlt etwas (z.B. kein Audit-Logging, keine Validierung)?

#### 3c: Referenz-Implementierungen finden

Suche nach **bestehenden Implementierungen** des gewünschten Musters:
- Für Audit-Logging: `Grep: "audit" oder "history" oder "changedBy" in server/src/`
- Für CSRF: `Grep: "csrf" oder "csurf" in server/src/`
- Für Rate Limiting: `Grep: "rateLimit" in server/src/`
- Für Input-Validierung: `Grep: "zod\|joi\|validate" in server/src/`
- Für Strukturiertes Logging: `Grep: "winston\|pino\|logger" in server/src/`

Falls ein Muster bereits im Projekt existiert, verwende es als Referenz im Prompt.

#### 3d: Datei-Manifest erstellen

Pro ActionableItem ein Manifest:
```
{
  ticketId: "ESTB-SEC-FEE-001",
  affectedFiles: [
    { path: "server/src/controllers/fees/onSetStrategy.js", change: "Audit-Logging ergänzen" },
    { path: "server/src/controllers/fees/onSetPerformanceFee.js", change: "Audit-Logging ergänzen" }
  ],
  referenceFiles: [
    { path: "server/src/services/depot/depotStatusService.js", pattern: "History-Pattern mit changedBy" }
  ],
  codeSnippets: {
    "server/src/controllers/fees/onSetStrategy.js": "// relevanter Code-Ausschnitt..."
  }
}
```

### Phase 4: Priorisieren & Abhängigkeiten

#### 4a: Task-Reihenfolge

1. **Primär:** Nach Priorität (P0 → P1 → P2 → P3)
2. **Sekundär:** Innerhalb gleicher Priorität: Infrastruktur vor Konsumenten

#### 4b: Abhängigkeiten erkennen

Prüfe für jedes Task-Paar:

1. **Shared Infrastructure:** Erstellt Task A eine Infrastruktur (Middleware, Service) die Task B nutzt?
   - Beispiel: "CSRF-Middleware implementieren" → vor "CSRF auf Fee-Endpoints anwenden"
   - Beispiel: "Audit-Service erstellen" → vor "Audit-Logging in Fees"
2. **Service-Erstellung:** Erstellt Task A einen neuen Service den Task B importiert?
3. **Datei-Überlappung:** Ändern Task A und B die gleiche Datei, und macht A eine strukturelle Änderung?

#### 4c: Deduplizierung

Prüfe ob Tickets Cross-Feature-Duplikate sind:
- CSRF-Tickets erscheinen oft in mehreren Feature-Seiten
- Rate-Limiting-Tickets erscheinen oft in mehreren Feature-Seiten
- Bei Duplikaten: Einen konsolidierten Task erstellen der alle betroffenen Routen abdeckt

#### 4d: Task-Nummerierung

Vergebe aufsteigende Nummern: `01-{slug}`, `02-{slug}`, etc.
Der Slug wird aus dem Task-Titel abgeleitet (lowercase, Bindestriche, URL-sicher).

### Phase 5: Output-Dateien generieren

Lade die Templates aus den Referenz-Dateien:
- `references/prompt-template.md` → Template für jeden einzelnen Prompt
- `references/output-structure.md` → Templates für plan.md und tasks.md

#### 5a: plan.md generieren

Erstelle `{projekt-root}/.claude/refactor-plans/{feature-name}/plan.md` nach dem Template in `references/output-structure.md`.

Fülle die Platzhalter:
- `{feature-name}`: Name aus dem Wiki-Pfad
- `{wiki-path}`: Voller Wiki-Pfad
- `{wiki-title}`: Seitentitel aus der API
- `{datum}`: Heutiges Datum
- `{projekt-name}`: Projektname aus wiki-projects.json
- Zusammenfassungs-Tabelle mit Anzahl pro Priorität
- Abhängigkeitsgraph als ASCII
- Betroffene-Dateien-Tabelle

#### 5b: tasks.md generieren

Erstelle `{projekt-root}/.claude/refactor-plans/{feature-name}/tasks.md` nach dem Template.

Gruppiert nach Priorität, pro Task:
- Checkbox (unchecked)
- Task-ID und Titel
- DORA-Artikel und Ticket-ID
- Betroffene Dateien
- Abhängigkeiten
- Verweis auf den Prompt-Datei

#### 5c: Prompts generieren

Erstelle `{projekt-root}/.claude/refactor-plans/{feature-name}/prompts/NN-{slug}.md` für **jeden Task**.

Für die Prompt-Qualität das Beispiel in `examples/example-prompt.md` als Referenz verwenden.

Jeder Prompt muss **eigenständig** sein (siehe `references/prompt-template.md`):
- Vollständiger Kontext (kein Verweis auf "siehe plan.md")
- Aktueller Code-Zustand (aus Phase 3)
- Schrittweise Anleitung
- Referenz-Muster aus der Codebase (aus Phase 3c)
- Verifikationsschritte
- Definition of Done
- Betroffene Dateien

### Phase 6: Claude Code Tasks erstellen

Für **jeden** generierten Task:

```
TaskCreate:
  subject: "[{ticket-id}] {task-title}"
  description: |
    DORA Art. {article} | Priorität: {priority}

    {Kurzbeschreibung aus dem Ticket}

    Prompt: {projekt-root}/.claude/refactor-plans/{feature}/prompts/NN-{slug}.md

    Betroffene Dateien:
    - {datei1}
    - {datei2}
  activeForm: "Implementing {task-title}"
```

Nach dem Erstellen aller Tasks: Abhängigkeiten setzen via `TaskUpdate` mit `addBlockedBy`.

### Phase 7: Ausgabe an den User

Dem User mitteilen:

1. **Welche Seite analysiert wurde** (Titel, Pfad)
2. **Anzahl extrahierter Items** nach Priorität
3. **Erstellte Dateien:**
   - `plan.md` Pfad
   - `tasks.md` Pfad
   - Anzahl Prompts und Verzeichnis
4. **Erstellte Claude Code Tasks** mit IDs
5. **Abhängigkeiten** die erkannt wurden
6. **Hinweis:** "Die Prompts können 1:1 als Input für Claude Code verwendet werden"

## Sicherheitsregeln

- NIEMALS WIKI_API_KEY in generierten .md-Dateien
- Keine internen IP-Adressen oder Hostnamen in Output-Dateien (Wiki-Pfade statt volle URLs)
- Keine exploitbaren Endpunkt-Details (keine Auth-Payloads, keine Token-Formate)
- Keine Secrets, Passwörter oder Tokens aus dem Quellcode in die Prompts kopieren
- Sensible Datenfelder nur als Konzept erwähnen, nicht mit Beispielwerten
