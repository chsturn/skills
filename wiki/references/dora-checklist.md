# DORA-Compliance-Checkliste

Prüfkategorien gemäß Digital Operational Resilience Act (DORA) – Verordnung (EU) 2022/2554.
Anwendbar auf regulierte Finanzunternehmen (FMA Liechtenstein).

## Prüfvorgehen

Für jede Kategorie:
1. Den Code gezielt nach relevanten Implementierungen durchsuchen
2. Ist-Zustand dokumentieren (was ist vorhanden)
3. Gap identifizieren (was fehlt)
4. Severity bewerten (Kritisch / Hoch / Mittel / Niedrig)

## Artikel 5 – IKT-Governance

| Prüfpunkt | Wo im Code suchen | Fragestellung |
|-----------|-------------------|---------------|
| IKT-Risikomanagement-Verantwortung | Organisationsstruktur, Rollenmodell | Sind Verantwortlichkeiten für IKT-Risiken definiert? |
| Schulung & Awareness | Konfiguration, Docs | Gibt es Security-Awareness-Maßnahmen? |

## Artikel 6 – IKT-Risikomanagement-Rahmenwerk

| Prüfpunkt | Wo im Code suchen | Fragestellung |
|-----------|-------------------|---------------|
| Dokumentation | README, CLAUDE.md, Wiki | Sind IKT-Risiken dokumentiert? |
| Regelmäßige Überprüfung | CI/CD, Scanning | Werden Risiken regelmäßig geprüft? |

## Artikel 7 – IKT-Systeme, -Protokolle und -Tools

| Prüfpunkt | Wo im Code suchen | Fragestellung |
|-----------|-------------------|---------------|
| Systemlandschaft | package.json, docker-compose | Sind alle IKT-Systeme inventarisiert? |
| Versionierung | Lock-Files, Dependency-Pinning | Sind Versionen exakt gepin? |
| Patch-Management | Dependencies | Gibt es einen Prozess für Updates? |

## Artikel 8 – Identification (Erkennung)

| Prüfpunkt | Wo im Code suchen | Fragestellung |
|-----------|-------------------|---------------|
| Asset-Inventar | Infrastruktur-Doku, Config | Sind alle IKT-Assets identifiziert? |
| Risikobewertung | Security-Docs, Scores | Werden Risiken pro Asset bewertet? |
| Schwachstellenmanagement | Scanning, Audit-Logs | Werden Schwachstellen identifiziert und getrackt? |

## Artikel 9 – Protection & Prevention

| Prüfpunkt | Wo im Code suchen | Fragestellung |
|-----------|-------------------|---------------|
| Authentifizierung | Auth-Middleware, Passport/JWT | Sind alle Endpunkte geschützt? |
| Autorisierung (RBAC) | Rollen-Guards, Middleware | Principle of Least Privilege umgesetzt? |
| Verschlüsselung (Data-at-Rest) | DB-Config, Encryption-Utils | Sind sensible Daten verschlüsselt? |
| Verschlüsselung (Data-in-Transit) | HTTPS, TLS-Config | Wird TLS 1.2+ verwendet? |
| Input-Validierung | Zod, Joi, Validators | Werden alle Eingaben validiert? |
| CSRF-Schutz | Middleware, Tokens | Ist CSRF-Schutz implementiert? |
| Rate Limiting | express-rate-limit, etc. | Sind öffentliche Endpoints rate-limited? |
| Security Headers | Helmet, CSP, HSTS | Werden Security-Header gesetzt? |
| Session Management | Cookie-Flags, Session-Config | Sichere Session-Konfiguration? |
| Audit Trail | Logging, History-Arrays | Werden Änderungen protokolliert? |
| Integritätsschutz | Hashing, Checksums | Ist Datenintegrität gewährleistet? |

## Artikel 10 – Detection (Erkennung)

| Prüfpunkt | Wo im Code suchen | Fragestellung |
|-----------|-------------------|---------------|
| Monitoring | Logger, APM, Alerting | Werden Anomalien erkannt? |
| Log-Management | Logger-Config, Log-Rotation | Sind Logs zentral und geschützt? |
| Intrusion Detection | Middleware, WAF | Werden Angriffe erkannt? |
| Information Disclosure | Error-Handler, Stack Traces | Werden interne Details exponiert? |

## Artikel 11 – Response & Recovery

| Prüfpunkt | Wo im Code suchen | Fragestellung |
|-----------|-------------------|---------------|
| Incident-Response-Plan | Docs, Runbooks | Gibt es einen IR-Plan? |
| Eskalationsprozess | Rollen, Benachrichtigungen | Ist ein Eskalationsprozess definiert? |
| Recovery-Verfahren | Backup, Restore-Scripts | Können Systeme wiederhergestellt werden? |
| Root-Cause-Analyse | Post-Mortem, Audit-Logs | Werden Ursachen analysiert? |

## Artikel 12 – Backup & Restoration

| Prüfpunkt | Wo im Code suchen | Fragestellung |
|-----------|-------------------|---------------|
| Backup-Strategie | Docker, Cron, Scripts | Werden regelmäßig Backups erstellt? |
| Backup-Integrität | Checksums, Validation | Werden Backups auf Integrität geprüft? |
| Restore-Tests | Docs, Scripts | Werden Restores getestet? |
| Aufbewahrungsfristen | Config, Policy | Werden Aufbewahrungsfristen eingehalten? |

## Artikel 13 – Kommunikation

| Prüfpunkt | Wo im Code suchen | Fragestellung |
|-----------|-------------------|---------------|
| Incident-Kommunikation | E-Mail, Alerting | Werden Stakeholder benachrichtigt? |
| Regulatorische Meldung | Compliance-Workflows | Werden FMA-Meldepflichten erfüllt? |

## Artikel 28-30 – Third-Party Risk Management

| Prüfpunkt | Wo im Code suchen | Fragestellung |
|-----------|-------------------|---------------|
| IKT-Dienstleister-Register | Config, Integration-Code | Sind alle IKT-Drittanbieter erfasst? |
| Vertragliche Anforderungen | API-Integrationen | Erfüllen Verträge DORA-Anforderungen? |
| Konzentrationsrisiko | Dependencies, Vendor Lock-in | Gibt es kritische Abhängigkeiten? |
| Exit-Strategie | Abstractions, Interfaces | Sind Anbieter austauschbar? |
| Überwachung | Webhooks, Health-Checks | Werden Drittanbieter überwacht? |

## Output-Format

Die DORA-Analyse als eigenständige Wiki-Seite oder als Erweiterung der Security-Seite erstellen:

```markdown
## DORA-Compliance-Analyse

### Zusammenfassung

| Kategorie | Erfüllt | Teilweise | Nicht erfüllt |
|-----------|---------|-----------|---------------|
| Art. 9 – Protection | X | Y | Z |
| ... | ... | ... | ... |

### Detail: Artikel 9 – Protection & Prevention

| Prüfpunkt | Status | Ist-Zustand | Gap | Empfehlung |
|-----------|--------|------------|-----|-----------|
| Authentifizierung | ✅ Erfüllt | Passport.js + RBAC | – | – |
| CSRF-Schutz | ❌ Fehlt | Nicht implementiert | DORA Art. 9 | csrf-Token implementieren |
| ... | ... | ... | ... | ... |

### DORA-Ticket-Übersicht

| Ticket | DORA Art. | Beschreibung | Priorität | Status |
|--------|-----------|-------------|-----------|--------|
| {PROJ}-SEC-001 | Art. 9 | ... | P0 | Offen |
```
