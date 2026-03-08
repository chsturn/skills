# Feature-Workflow: Sicherheitsanalyse

Für Code-Suche siehe `shared-phases.md`. Für Push und Index-Update siehe SKILL.md Push-Workflow.

## Analyse-Fokus

Alle gefundenen Dateien mit Sicherheitsfokus analysieren:

### Authentifizierung & Autorisierung
- Welche Auth-Middleware ist auf den Routes?
- Welche Rollen haben Zugriff?
- Ownership-Checks vorhanden (User darf nur eigene Daten)?
- Sind alle Endpunkte geschützt?

### Input-Validierung
- Werden Body, Query-Params und URL-Params validiert?
- Welches Validierungstool (Zod, Joi, etc.)?
- XSS-Schutz bei User-generierten Inhalten?
- SQL/NoSQL-Injection-Vektoren abgesichert?

### CSRF & Session-Sicherheit
- Ist CSRF-Schutz implementiert?
- Cookie-Flags (HttpOnly, Secure, SameSite)?
- Session-Fixation-Schutz?

### Rate Limiting
- Öffentliche Endpunkte rate-limited?
- Sensible Endpunkte (Login, Passwort-Reset) besonders geschützt?

### Fehlerbehandlung & Information Disclosure
- Stack Traces an Client zurückgegeben?
- Interne Pfade oder Systemdetails exponiert?
- Fehlermeldungen generisch genug?

### Verschlüsselung
- Sensible Daten verschlüsselt gespeichert (at-rest)?
- TLS für alle externe Kommunikation (in-transit)?
- PII-Daten besonders geschützt?

### Dependencies & CVEs
- Bekannte Schwachstellen in Dependencies?
- Versionen exakt gepinnt?
- Veraltete oder nicht-gewartete Dependencies?

### Audit Trail
- Sicherheitsrelevante Aktionen protokolliert?
- Sensible Daten in Logs vermieden?
- Audit-Trail manipulationssicher?

## Markdown-Struktur

Alle Abschnitte sind Pflicht. Falls ein Aspekt nicht relevant → explizit vermerken.

1. **Übersicht**
   - Feature-Kontext (1-2 Sätze)
   - Security-Scope: Welche Sicherheitsaspekte relevant?
   - Beteiligte Systeme aus Sicherheitsperspektive

2. **Authentifizierung & Autorisierung**

   | Endpunkt | Methode | Middleware | Rollen | Ownership-Check |
   |----------|---------|-----------|--------|-----------------|

3. **Input-Validierung**

   | Endpunkt | Validierung | Lücken |
   |----------|------------|--------|

4. **Session & CSRF** – Konfiguration, Cookie-Flags, Mechanismus

5. **Rate Limiting** – Endpunkte und Limits

6. **Fehlerbehandlung & Information Disclosure** – Error-Handler-Analyse

7. **Verschlüsselung & Datenschutz** – At-rest, in-transit, PII

8. **Dependency-Analyse** – Dependencies mit Sicherheitsstatus

9. **Security-Ticket-Tabelle**

   | Ticket | Beschreibung | Priorität | Status |
   |--------|-------------|-----------|--------|
   | {PROJ}-{FEAT}-SEC-001 | ... | P0 – Kritisch | Offen |

   Ticket-ID: `{PROJ}-{FEAT}-SEC-{NNN}` (z.B. `ESTB-EMAIL-SEC-001`)

   Prioritäten:
   - **P0 – Kritisch**: Sofort beheben (aktiv ausnutzbar)
   - **P1 – Hoch**: Zeitnah beheben (signifikantes Risiko)
   - **P2 – Mittel**: Nächster Sprint (Best Practice fehlt)
   - **P3 – Niedrig**: Backlog (Verbesserungspotenzial)

10. **Verwandte Seiten** – Cross-Links:
    - `[Funktionale Analyse](/{wikiBase}/features/{gruppe}/{feature})`
    - `[DORA-Compliance](/{wikiBase}/security/reviews/{feature}-dora)`
