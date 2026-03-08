---
name: wiki
description: >
  Use this skill whenever the user wants to create wiki documentation from code analysis,
  document a feature, add architecture docs to the wiki, or generate structured Wiki.js pages.
  Trigger on: "wiki", "/wiki", "dokumentieren", "document", "wiki erstellen", "wiki page",
  "Feature dokumentieren", "Doku erstellen", "Code-Dokumentation", "add to wiki",
  "Architektur dokumentieren", "Security-Analyse", "DORA-Analyse".
  Use this skill even when the user just says "dokumentier das" or "schreib das ins Wiki"
  in the context of code analysis. Also trigger when the user wants to create project-level
  architecture documentation, security analysis, or DORA compliance pages.
version: 2.0.0
---

# Wiki Documentation Skill

Analysiert eine Codebase und generiert strukturierte Wiki.js-Dokumentation. Unterstützt funktionale Analyse, Sicherheitsanalyse und DORA-Compliance-Prüfung.

## Voraussetzungen

Vor jeder Ausführung diese drei Checks durchführen:

### 1. Wiki-Token laden

Den Token **immer** aus der Datei laden — nie auf Env-Vars verlassen:

```bash
WT=$(cat ~/.claude/.wiki-token) && echo "Token geladen (${#WT} Zeichen)"
```

Falls die Datei fehlt → User informieren und abbrechen.

### 2. Wiki erreichbar?

Kurzer Connectivity-Test:

```bash
WT=$(cat ~/.claude/.wiki-token) && curl -s --connect-timeout 5 -X POST 'http://192.168.178.67:3100/graphql' \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $WT" \
  -d '{"query":"{ pages { list(limit: 1) { id } } }"}' | head -c 200
```

Falls Timeout → User informieren: "Wiki unter http://192.168.178.67:3100 nicht erreichbar. VPN/Netzwerk prüfen."

### 3. Projekt-Erkennung

Das CWD gegen die Projekt-Konfiguration in `wiki-projects.json` matchen:

```bash
cat /Users/chsturn/dev/private/wiki/.claude/wiki-projects.json
```

Den CWD-Pfad nach bekannten `pathPatterns` durchsuchen. Falls kein Match → User fragen welches Projekt gemeint ist. Die erkannten Werte (`wikiBase`, `tags`, `title`, Page-IDs) für den Rest des Workflows verwenden.

## Wichtig: Pfad-Aenderungen und interne Links

Wiki.js unterstuetzt Pfad-Aenderungen via Update-Mutation (neuen `path` im Update mitgeben). Wenn Seiten verschoben werden, muessen **alle internen Links auf anderen Seiten** aktualisiert werden, die auf den alten Pfad verweisen. Vor Pfad-Aenderungen immer ein Link-Mapping (alt → neu) erstellen und danach alle betroffenen Seiten durchsuchen und fixen.

## Argument-Parsing

| Input | Modus | Beschreibung |
|-------|-------|-------------|
| `/wiki <feature>` | Feature (functional) | Funktionale Analyse (Default) |
| `/wiki <feature> functional` | Feature (functional) | Funktionale Analyse (explizit) |
| `/wiki <feature> security` | Feature (security) | Sicherheitsanalyse |
| `/wiki <feature> dora` | Feature (dora) | DORA-Compliance-Analyse |
| `/wiki projekt` | Projekt | Gesamtes Projekt analysieren |
| `/wiki projekt dora` | Projekt + DORA | Projekt + DORA-Compliance |

**Parsing-Logik:**
1. Letztes Wort prüfen: ist es `functional`, `security` oder `dora`?
2. Falls Schlüsselwort → Typ setzen, Feature-Name = alles davor
3. Falls nicht → Default = `functional`, Feature-Name = gesamter Input
4. Sonderfall: `projekt` / `projekt dora` → Projekt-Modus
5. Edge Case: `/wiki security` (nur ein Wort = Schlüsselwort) → Feature "security", Typ `functional`

## Modus: Feature

Je nach Analyse-Typ die entsprechende Referenz-Datei laden:

| Analyse-Typ | Referenz-Datei |
|-------------|---------------|
| `functional` | `references/feature-workflow-functional.md` |
| `security` | `references/feature-workflow-security.md` |
| `dora` | `references/feature-workflow-dora.md` |

**Workflow (alle Analyse-Typen):**

1. **Code durchsuchen** → Suchstrategie aus `references/shared-phases.md`
2. **Dateien analysieren** → Analyse-spezifisch (geladene Referenz)
3. **Markdown generieren** → Struktur aus der Referenz, Formatierungsregeln aus `references/shared-phases.md`
4. **Ins Wiki pushen** → Push-Workflow (siehe unten)
5. **Index aktualisieren** → Index-Workflow aus `references/shared-phases.md`

## Modus: Projekt

Referenz `references/projekt-workflow.md` laden.

**Kurzübersicht:**
1. Gesamtes Projekt analysieren (Tech-Stack, Struktur, Dependencies)
2. 6 Standard-Seiten generieren (system-overview, backend, frontend, data-model, security, deployment)
3. Index-Seiten erstellen
4. Alles ins Wiki pushen
5. Projekte-Übersicht aktualisieren

## Push-Workflow

**Markdown nie direkt in curl-JSON einbetten.** Immer diesen Ablauf:

### Schritt 1: Markdown in Temp-Datei schreiben

Per Write-Tool nach `/tmp/wiki-{feature}-{typ}.md` schreiben. Dadurch ist das JSON-Escaping-Problem gelöst — das Push-Script liest die Datei und escaped korrekt.

### Schritt 2: Per wiki-push.mjs hochladen

**Pfade je nach Analyse-Typ:**

| Typ | Pfad-Muster |
|-----|------------|
| `functional` | `{wikiBase}/features/{gruppe}/{feature}` |
| `security` | `{wikiBase}/security/reviews/{feature}-security` |
| `dora` | `{wikiBase}/security/reviews/{feature}-dora` |

Die {gruppe} ergibt sich aus den Feature-Gruppen in `references/wiki-structure.md`.

**Neue Seite erstellen:**
```bash
WIKI_API_KEY=$(cat ~/.claude/.wiki-token) node /Users/chsturn/.claude/skills/wiki/scripts/wiki-push.mjs \
  create \
  --file /tmp/wiki-{feature}-{typ}.md \
  --path "{pfad-aus-tabelle-oben}" \
  --title "{projektTitle} – {Feature} ({Analyse-Typ})" \
  --tags "{projektTags},{feature},{typ}"
```

**Bestehende Seite aktualisieren (per ID):**
```bash
WIKI_API_KEY=$(cat ~/.claude/.wiki-token) node /Users/chsturn/.claude/skills/wiki/scripts/wiki-push.mjs \
  update \
  --id <page-id> \
  --file /tmp/wiki-{feature}-{typ}.md \
  --title "{projektTitle} – {Feature} ({Analyse-Typ})" \
  --tags "{projektTags},{feature},{typ}"
```

**Bestehende Seite aktualisieren (per Pfad):**
```bash
WIKI_API_KEY=$(cat ~/.claude/.wiki-token) node /Users/chsturn/.claude/skills/wiki/scripts/wiki-push.mjs \
  update \
  --path "{pfad-aus-tabelle-oben}" \
  --file /tmp/wiki-{feature}-{typ}.md \
  --title "{projektTitle} – {Feature} ({Analyse-Typ})" \
  --tags "{projektTags},{feature},{typ}"
```

### Schritt 3: Ergebnis prüfen

Das Script gibt JSON auf stdout aus:
- Erfolg: `{"ok": true, "action": "create", "id": 123, "path": "...", "url": "..."}`
- Fehler: `{"ok": false, "error": "..."}`

Bei `ok: false` → Fehlermeldung dem User anzeigen.

### Schritt 4: Page-ID merken

Bei `create` die zurückgegebene `id` in `wiki-projects.json` unter `featurePages` eintragen.

## Seite lesen (per GraphQL)

Zum Laden einer bestehenden Seite (z.B. für Index-Updates):

```bash
WT=$(cat ~/.claude/.wiki-token) && curl -s -X POST 'http://192.168.178.67:3100/graphql' \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $WT" \
  -d '{"query":"{ pages { single(id: <page-id>) { id title content } } }"}'
```

## Fehlerbehandlung

| Fehler | Aktion |
|--------|--------|
| Token-Datei fehlt | User informieren: "`~/.claude/.wiki-token` nicht gefunden" |
| Wiki nicht erreichbar | User informieren: "Wiki-Server nicht erreichbar. Netzwerk/VPN prüfen." |
| Push fehlgeschlagen | Fehlermeldung aus Script anzeigen, ggf. nochmal versuchen |
| Seite existiert bereits (Create) | Auf Update wechseln — Page-ID per Pfad-Lookup ermitteln |
| wiki-push.mjs nicht gefunden | Direkt per curl (als Fallback, Content vorher JSON-safe machen) |

## Wiki-Struktur

**Vor jeder Seitenerstellung** die Strukturregeln laden:

```
references/wiki-structure.md
```

Diese Datei definiert verbindlich wo welche Seiten abgelegt werden. Kurzfassung:

| Seitentyp | Pfad-Muster |
|-----------|------------|
| Projekt-Index | `projekte/{projekt}` |
| Architektur-Index | `projekte/{projekt}/architektur` |
| Architektur-Seite | `projekte/{projekt}/architektur/{seite}` |
| Feature-Index | `projekte/{projekt}/features` |
| Feature-Gruppe-Index | `projekte/{projekt}/features/{gruppe}` |
| Feature (functional) | `projekte/{projekt}/features/{gruppe}/{feature}` |
| Betrieb-Index | `projekte/{projekt}/betrieb` |
| Betrieb-Seite | `projekte/{projekt}/betrieb/{seite}` |
| Security-Index | `projekte/{projekt}/security` |
| Security-Uebersicht | `projekte/{projekt}/security/uebersicht` |
| Security-Review | `projekte/{projekt}/security/reviews/{feature}-security` |
| DORA-Review | `projekte/{projekt}/security/reviews/{feature}-dora` |
| Compliance (uebergreifend) | `compliance/{bereich}/{seite}` |
| Standards | `standards/{seite}` |

## Sicherheitsregeln

- NIEMALS API-Keys, Credentials oder Secrets in Markdown schreiben
- Keine internen IPs/Hostnamen exponieren (außer Wiki-interne Links)
- Keine exploitbaren Endpunkt-Details (Auth-Payloads, Token-Formate)
- Sensible Datenfelder nur als Typ/Konzept erwähnen, nicht mit Beispielwerten

## Ausgabe an den User

Nach Abschluss dem User mitteilen:
1. Welche Seiten erstellt/aktualisiert wurden (mit Wiki-URLs und Page-IDs)
2. Falls Fehler auftraten: welche und warum
