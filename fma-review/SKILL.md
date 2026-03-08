---
name: fma-review
description: >
  **FMA Compliance Review**: Spawnt ein Team aus 4 spezialisierten Review-Agents
  (DORA, Security, QA, Data Integrity) die parallel Code-Aenderungen pruefen.
  Verwende diesen Skill immer wenn der User Code-Aenderungen durch spezialisierte
  Reviewer pruefen lassen will — egal ob er "FMA Review", "Compliance Check",
  "DORA Review", "Security Review", "Team Review", "4-Augen-Prinzip", "lass die
  Agents pruefen", "regulatorisches Review", "pruef die Aenderungen", oder einfach
  nur "/fma-review" sagt. Auch triggern bei teilweisen Reviews wie "nur Security
  und DORA pruefen" oder "QA Review der Tests". Der Skill ist der zentrale Einstieg
  fuer jede Art von multi-agent Code-Review im Estably-Kontext.
version: 1.1.0
---

# FMA Compliance Review Team

Spawnt bis zu 4 spezialisierte Review-Agents parallel fuer ein umfassendes Compliance-Review der Estably-Vermoegensverwaltung.

## Verfuegbare Reviewer

| Name | Agent-Datei | Prueft |
|------|-------------|--------|
| `qa-engineer` | `.claude/agents/qa-engineer.md` | Testqualitaet, Assertions, Mocks, Flaky Tests |
| `security-officer` | `.claude/agents/security-officer.md` | OWASP Top 10, Credentials, Auth, Injection |
| `data-integrity-auditor` | `.claude/agents/data-integrity-auditor.md` | DSGVO, Finanzdaten, Schema, PII |
| `dora-compliance-officer` | `.claude/agents/dora-compliance-officer.md` | DORA Art. 5-44, ICT Risk, Resilience |

## Ablauf

### 1. Scope und Reviewer-Auswahl ermitteln

**Reviewer-Auswahl:**
- Default: Alle 4 Reviewer
- Der User kann einschraenken, z.B. "nur Security und DORA" oder "nur QA"
- Bei reinen Test-Aenderungen: QA + Data Integrity empfehlen
- Bei Auth/API-Aenderungen: Security + DORA empfehlen

**Dateien ermitteln (in dieser Reihenfolge):**

a) User hat Dateien/Verzeichnis angegeben? → Diese verwenden.

b) Gibt es Git-Aenderungen?
```bash
git diff --name-only HEAD 2>/dev/null; git diff --name-only --cached 2>/dev/null
```

c) Aenderungen gegenueber Base-Branch?
```bash
git log --oneline -5 --name-only 2>/dev/null
```

d) Nichts gefunden? → User fragen.

**Scope bestaetigen:** Zeige dem User kurz die Dateiliste und ausgewaehlte Reviewer, BEVOR das Team startet. Beispiel:

```
Review-Scope:
- src/e2e/shared-depot-onboarding.cy.ts (geaendert)
- src/support/pages/onboarding-completion.page.ts (geaendert)

Reviewer: QA Engineer, Security Officer, Data Integrity, DORA Compliance
Starten?
```

### 2. Team erstellen und Reviewer spawnen

Erstelle das Team und spawne alle ausgewaehlten Reviewer **in einer einzigen Nachricht** (parallel):

```
TeamCreate: team_name="fma-review", description="FMA Compliance Review"
```

Dann fuer jeden ausgewaehlten Reviewer einen Agent spawnen mit:
- `team_name: "fma-review"`
- `mode: "plan"` (read-only)
- `model: "sonnet"`
- `subagent_type: "general-purpose"`

Jeder Agent bekommt einen Prompt mit:
1. Seiner Rolle (aus der Agent-Datei)
2. Der konkreten Dateiliste
3. Einem kurzen `git diff` Summary (was hat sich geaendert)
4. Seinem spezifischen Review-Auftrag (siehe Prompt-Templates unten)

### 3. Auf Ergebnisse warten

Agents laufen im Hintergrund. Benachrichtigungen kommen automatisch.
Nicht pollen oder schlafen — einfach warten bis alle fertig sind.

### 4. Findings zusammenfassen

Konsolidiere alle Findings in einer Tabelle:

```
## FMA Review Ergebnis

### Zusammenfassung
| Reviewer | Bewertung | Critical | High | Medium | Low |
|----------|-----------|----------|------|--------|-----|

### Actionable Findings (CRITICAL → LOW)
[Jedes Finding mit Datei:Zeile, Beschreibung, Empfehlung]

### Empfohlene Massnahmen
[Top 3-5 priorisierte Aktionen]
```

Biete dem User an, Findings direkt umzusetzen.

### 5. Team aufraeumen

Shutdown-Requests an alle Agents → Warten auf Bestaetigungen → TeamDelete.

---

## Prompt-Templates fuer Reviewer

### qa-engineer
```
Du bist der QA Engineer im Review-Team. Pruefe diese Dateien:
{DATEILISTE}

Aenderungen: {GIT_DIFF_SUMMARY}

Pruefe auf:
- Assertion-Qualitaet: Sind Assertions spezifisch genug? Finden sie echte Bugs oder sind sie Theater?
- Test-Isolation: State-Leaks? Cleanup korrekt? Tests voneinander unabhaengig?
- Mock-Korrektheit: Realistisch? Verstecken sie Bugs?
- Anti-Patterns: Flaky Tests, tote Assertions, hardcoded Waits, `failOnStatusCode: false` ohne Check
- Timing: Assertions an richtiger Stelle? Keine Race Conditions?

Gib strukturierte Findings mit Severity, Datei:Zeile und konkreter Empfehlung.
```

### security-officer
```
Du bist der Security Officer im Review-Team. Pruefe diese Dateien:
{DATEILISTE}

Aenderungen: {GIT_DIFF_SUMMARY}

Pruefe auf:
- OWASP Top 10 (A01-A10): Auth, Injection, Misconfiguration, Crypto
- Credential Leaks: Secrets, Tokens, Passwoerter in Code/Tests/Logs
- Auth/AuthZ: IDOR, Privilege Escalation, CSRF
- Input Validation: NoSQL Injection, XSS, ReDoS, Path Traversal
- Referenz: 24 bekannte Findings im CLAUDE.md — sind neue/bestehende betroffen?
- Test-Sicherheit: Keine echten Credentials, `x-disable-rate-limit` nur in Test

Gib strukturierte Findings mit Severity, CVSS, Datei:Zeile und konkreter Empfehlung.
```

### data-integrity-auditor
```
Du bist der Data Integrity Auditor im Review-Team. Pruefe diese Dateien:
{DATEILISTE}

Aenderungen: {GIT_DIFF_SUMMARY}

Pruefe auf:
- Schema-Konsistenz: Assertions vs. echtes DB-Schema (schemas/ Verzeichnis pruefen)
- Datenintegritaet: Atomare Operationen, keine Partial Updates, referenzielle Integritaet
- DSGVO/DSG: PII-Handling, Loeschrecht (cleanupUser), Datenminimierung
- Finanzdaten: Decimal-Handling, Rundung, konsistente Berechnungen
- Test-Daten: Keine echten PII, Cleanup vollstaendig, realistische Testdaten

Gib strukturierte Findings mit Severity, Rechtsgrundlage, Datei:Zeile und konkreter Empfehlung.
```

### dora-compliance-officer
```
Du bist der DORA Compliance Officer im Review-Team. Pruefe diese Dateien:
{DATEILISTE}

Aenderungen: {GIT_DIFF_SUMMARY}

Pruefe im DORA-Kontext (EU 2022/2554):
- Art. 5-16: ICT Risk Management — Risiken identifiziert und adressiert?
- Art. 17-23: Incident Management — Fehlerszenarien getestet? Recovery-Pfade?
- Art. 24-27: Resilience Testing — Tests als Resilienz-Nachweis geeignet?
- Art. 28-44: Third-Party Risk — ITM/Baader/LLB-Interaktionen korrekt getestet?
- Audit Trail: Logging, Nachvollziehbarkeit, Reproduzierbarkeit

Gib strukturierte Findings mit DORA-Artikelreferenz, Severity und konkreter Empfehlung.
```

---

## Fehlerbehandlung

- **TeamCreate fehlschlaegt:** Pruefen ob bereits ein Team "fma-review" existiert. Falls ja, erst TeamDelete, dann neu erstellen.
- **Agent-Spawn fehlschlaegt:** User informieren, restliche Agents weiterlaufen lassen.
- **Keine Git-Aenderungen:** User fragen welche Dateien/Features reviewed werden sollen — nicht einfach abbrechen.
- **User will abbrechen:** Shutdown-Requests an alle laufenden Agents, TeamDelete.
