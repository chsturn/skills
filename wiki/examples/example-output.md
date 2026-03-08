# Beispiel-Ausgaben nach Analyse-Typ

Dieses Dokument zeigt die erwartete Ausgabe für die drei Analyse-Typen am Beispiel des Features `transaction-monitoring` im Estably-Projekt.

---

# Beispiel 1: Funktionale Analyse (`/wiki transaction-monitoring` oder `/wiki transaction-monitoring functional`)

**Datei:** `docs/estably/features/transaction-monitoring-functional.md`
**Wiki-Pfad:** `projekte/estably/features/transaction-monitoring/functional`

---

# Estably – Transaction Monitoring (Funktionale Analyse)

## Übersicht

AML/KYC-konformes Monitoring aller Ein- und Auszahlungen auf der Estably-Plattform. Jede Transaktion durchläuft automatische Regelprüfungen und wird bei Bedarf an manuelle Prüfer oder die Compliance-Abteilung eskaliert.

**Regulatorischer Rahmen:**

| Anforderung | Beschreibung |
|-------------|-------------|
| DORA Art. 9 | Protection & Prevention – automatisierte Überwachung von Finanztransaktionen |
| FMA Liechtenstein | AML/KYC-Pflichten gemäß Sorgfaltspflichtgesetz (SPG) |

---

## Datenfluss (End-to-End)

```
Baader Bank (SFTP)                    LLB Bank (FTP)
       │                                    │
       ▼                                    ▼
   baaderRKK                            llbTRANS
       │                                    │
       └──────────────┬─────────────────────┘
                      ▼
             bankTransactions
            (normalisiert, bankübergreifend)
                      │
                      ▼
            Monitoring Rules (Rule Set 2.1.0)
                      │
           ┌──────────┴──────────┐
           ▼                     ▼
   Auto-Release            Manuelle Prüfung
  (Referenzkonto +           │
   innerhalb Limits)   ┌─────┴──────┐
                       ▼            ▼
                  FINISHED    COMPLIANCE
```

---

## State Machine

```
              NOT_STARTED
                    │
                    ▼
              IN_PROGRESS
                    │
          ┌────────┼────────┐
          ▼        ▼        ▼
      FINISHED  FINISHED  COMPLIANCE
              WITH_CHECK     │
                    ┌────────┴────────┐
                    ▼                 ▼
           COMPLIANCE_RELEASE  COMPLIANCE_REJECTED
```

---

## Verbesserungsvorschläge

| Ticket | Beschreibung | Priorität | Status |
|--------|-------------|-----------|--------|
| ESTB-TXMON-001 | Rule-Set-Versionierung in DB statt Hardcoded-Konstante | P2 – Mittel | Offen |
| ESTB-TXMON-002 | Retry-Mechanismus für fehlgeschlagene SFTP-Imports | P2 – Mittel | Offen |
| ESTB-TXMON-003 | Batch-Size für Massenimport konfigurierbar machen | P3 – Niedrig | Offen |

---

## Verwandte Seiten

- [Backend-Architektur](/projekte/estably/architektur/backend-services)
- [Datenmodell](/projekte/estably/architektur/data-model)
- [Sicherheitsanalyse](/projekte/estably/features/transaction-monitoring/security)
- [DORA-Compliance](/projekte/estably/features/transaction-monitoring/dora)

---
---

# Beispiel 2: Sicherheitsanalyse (`/wiki transaction-monitoring security`)

**Datei:** `docs/estably/features/transaction-monitoring-security.md`
**Wiki-Pfad:** `projekte/estably/features/transaction-monitoring/security`

---

# Estably – Transaction Monitoring (Sicherheitsanalyse)

## Übersicht

Sicherheitsanalyse des Transaction-Monitoring-Features. Dieses Feature verarbeitet sensible Finanztransaktionsdaten und kommuniziert mit externen Banksystemen via SFTP/FTP.

**Security-Scope:** Authentifizierung, Input-Validierung, Verschlüsselung, Third-Party-Kommunikation

---

## Authentifizierung & Autorisierung

| Endpunkt | Methode | Middleware | Rollen | Ownership-Check |
|----------|---------|-----------|--------|-----------------|
| /api/transactions | GET | authMiddleware | admin, compliance | Nein (alle sehen alle) |
| /api/transactions/:id/review | PUT | authMiddleware | compliance | Nein |
| /api/transactions/import | POST | authMiddleware, cronGuard | system | N/A (System-Job) |

---

## Input-Validierung

| Endpunkt | Validierung | Lücken |
|----------|------------|--------|
| PUT /api/transactions/:id/review | Zod-Schema (body: status, comment) | ID-Parameter nicht als ObjectId validiert |
| POST /api/transactions/import | Keine (interner Cronjob) | Fehlende Validierung der SFTP-Daten |

---

## Session & CSRF

CSRF-Schutz ist global via `csurf`-Middleware implementiert. Cronjob-Endpunkte sind per `cronGuard`-Middleware exemptiert (kein Browser-Zugriff).

---

## Rate Limiting

| Endpunkt | Limit | Anmerkung |
|----------|-------|-----------|
| /api/transactions | 100/min | Standard-Rate-Limit |
| /api/transactions/:id/review | 30/min | Erhöhter Schutz für Statusänderungen |

---

## Fehlerbehandlung & Information Disclosure

Error-Handler gibt generische Fehlermeldungen zurück. Stack Traces werden nur serverseitig geloggt. SFTP-Verbindungsfehler werden mit internem Pfad geloggt – Pfad enthält keine Credentials.

---

## Verschlüsselung & Datenschutz

- **In-Transit:** SFTP (SSH-verschlüsselt) für Baader Bank, FTP-over-TLS für LLB
- **At-Rest:** Transaktionsdaten in MongoDB ohne Feld-Level-Encryption
- **PII:** Kontonummern im Klartext gespeichert (IBAN, BIC)

---

## Dependency-Analyse

| Package | Version | Status |
|---------|---------|--------|
| ssh2-sftp-client | 9.1.0 | Aktuell, keine CVEs |
| basic-ftp | 5.0.3 | Aktuell, keine CVEs |

---

## Security-Ticket-Tabelle

| Ticket | Beschreibung | Priorität | Status |
|--------|-------------|-----------|--------|
| ESTB-TXMON-SEC-001 | Kontonummern (IBAN) verschlüsselt speichern (Feld-Level-Encryption) | P1 – Hoch | Offen |
| ESTB-TXMON-SEC-002 | ObjectId-Validierung für `:id`-Parameter ergänzen | P2 – Mittel | Offen |
| ESTB-TXMON-SEC-003 | SFTP-Import-Daten vor Verarbeitung validieren | P2 – Mittel | Offen |

---

## Verwandte Seiten

- [Funktionale Analyse](/projekte/estably/features/transaction-monitoring/functional)
- [DORA-Compliance](/projekte/estably/features/transaction-monitoring/dora)
- [Sicherheitsanalyse (Projekt)](/projekte/estably/architektur/security)

---
---

# Beispiel 3: DORA-Compliance-Analyse (`/wiki transaction-monitoring dora`)

**Datei:** `docs/estably/features/transaction-monitoring-dora.md`
**Wiki-Pfad:** `projekte/estably/features/transaction-monitoring/dora`

---

# Estably – Transaction Monitoring (DORA-Compliance)

## Übersicht

DORA-Compliance-Analyse des Transaction-Monitoring-Features. Dieses Feature ist regulatorisch besonders relevant, da es direkt Finanztransaktionen verarbeitet und mit externen IKT-Dienstleistern (Banken) kommuniziert.

**Relevante DORA-Artikel:**
- Art. 9 – Protection & Prevention
- Art. 10 – Detection
- Art. 11 – Response & Recovery
- Art. 28-30 – Third-Party Risk Management

**Regulatorischer Rahmen:** Verordnung (EU) 2022/2554, FMA Liechtenstein

---

## DORA-Zusammenfassung

| Artikel | Beschreibung | Erfüllt | Teilweise | Nicht erfüllt |
|---------|-------------|---------|-----------|---------------|
| Art. 9 | Protection & Prevention | 5 | 3 | 2 |
| Art. 10 | Detection | 1 | 1 | 1 |
| Art. 11 | Response & Recovery | 0 | 1 | 2 |
| Art. 28-30 | Third-Party Risk | 2 | 1 | 1 |

---

## Detail: Artikel 9 – Protection & Prevention

| Prüfpunkt | Status | Ist-Zustand | Gap | Empfehlung |
|-----------|--------|------------|-----|-----------|
| Authentifizierung | ✅ Erfüllt | Passport.js + JWT auf allen Endpunkten | – | – |
| Autorisierung (RBAC) | ✅ Erfüllt | Rollenbasiert (admin, compliance) | – | – |
| Verschlüsselung (in-transit) | ✅ Erfüllt | SFTP + FTP-over-TLS | – | – |
| Verschlüsselung (at-rest) | ❌ Nicht erfüllt | Kontonummern im Klartext | IBAN/BIC unverschlüsselt | Feld-Level-Encryption implementieren |
| Input-Validierung | ⚠️ Teilweise | Zod auf Review-Endpoint | SFTP-Import ohne Validierung | Schema-Validierung für Import-Daten |
| Rate Limiting | ✅ Erfüllt | 100/min bzw. 30/min | – | – |
| Audit Trail | ⚠️ Teilweise | Status-Änderungen geloggt | Import-Vorgänge nicht auditiert | Audit-Log für Imports ergänzen |

---

## Detail: Artikel 10 – Detection

| Prüfpunkt | Status | Ist-Zustand | Gap | Empfehlung |
|-----------|--------|------------|-----|-----------|
| Monitoring | ✅ Erfüllt | Rule-basiertes Transaction Monitoring | – | – |
| Log-Management | ⚠️ Teilweise | Winston-Logger, kein zentrales Log-Management | Logs nur lokal | Zentrales Log-Management (ELK/Loki) |
| Information Disclosure | ❌ Nicht erfüllt | SFTP-Pfade in Fehlerlogs | Interne Pfade exponiert | Pfade in Logs maskieren |

---

## Detail: Artikel 28-30 – Third-Party Risk Management

| Prüfpunkt | Status | Ist-Zustand | Gap | Empfehlung |
|-----------|--------|------------|-----|-----------|
| IKT-Dienstleister-Register | ✅ Erfüllt | Baader Bank, LLB in Config dokumentiert | – | – |
| Überwachung | ✅ Erfüllt | Health-Checks bei SFTP-Verbindung | – | – |
| Exit-Strategie | ⚠️ Teilweise | Bank-Abstraktion vorhanden | Kein dokumentierter Wechselprozess | Exit-Strategie dokumentieren |
| Konzentrationsrisiko | ❌ Nicht erfüllt | Keine Analyse | Konzentrationsrisiko nicht bewertet | Risikobewertung für Bankabhängigkeiten |

---

## DORA-Ticket-Tabelle

| Ticket | DORA Art. | Beschreibung | Priorität | Status |
|--------|-----------|-------------|-----------|--------|
| ESTB-TXMON-DORA-001 | Art. 9 | Feld-Level-Encryption für Kontonummern | P1 – Hoch | Offen |
| ESTB-TXMON-DORA-002 | Art. 9 | Schema-Validierung für SFTP-Import-Daten | P1 – Hoch | Offen |
| ESTB-TXMON-DORA-003 | Art. 9 | Audit-Log für Import-Vorgänge | P2 – Mittel | Offen |
| ESTB-TXMON-DORA-004 | Art. 10 | Zentrales Log-Management einrichten | P2 – Mittel | Offen |
| ESTB-TXMON-DORA-005 | Art. 10 | Interne Pfade in Fehlerlogs maskieren | P2 – Mittel | Offen |
| ESTB-TXMON-DORA-006 | Art. 28-30 | Exit-Strategie für Bankanbindungen dokumentieren | P3 – Niedrig | Offen |
| ESTB-TXMON-DORA-007 | Art. 28-30 | Konzentrationsrisiko-Bewertung erstellen | P3 – Niedrig | Offen |

---

## Verwandte Seiten

- [Funktionale Analyse](/projekte/estably/features/transaction-monitoring/functional)
- [Sicherheitsanalyse](/projekte/estably/features/transaction-monitoring/security)
- [DORA-Compliance (Projekt)](/projekte/estably/architektur/security)
