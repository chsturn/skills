# Feature-Workflow: Funktionale Analyse

Für Code-Suche siehe `shared-phases.md`. Für Push und Index-Update siehe SKILL.md Push-Workflow.

## Analyse-Fokus

Alle gefundenen Dateien **vollständig** lesen. Dabei erfassen:

### Backend
- **Schema/Model**: Felder, Typen, Validierungen, Indizes
- **Service-Layer**: Geschäftslogik, State-Übergänge, Berechnungen
- **Controller**: Request/Response-Mapping, Validierung
- **Routes**: Endpunkte, HTTP-Methoden, Rollen/Middleware
- **External Integrations**: Aufrufe an externe APIs, Webhooks

### Frontend
- **Components**: UI-Struktur, User-Interaktionen
- **Services**: API-Aufrufe, State Management
- **Models/Interfaces**: TypeScript-Typen

### Übergreifend
- **State Machine**: Zustände und Übergänge
- **Fehlerbehandlung**: Szenarien und Reaktionen
- **Audit/Logging**: Was wird protokolliert?
- **Berechtigungen**: Welche Rollen haben Zugriff?

## Markdown-Struktur

### Pflicht-Abschnitte

1. **Übersicht**
   - 2-3 Sätze: Was macht das Feature?
   - Regulatorischer Rahmen (falls relevant): DORA, FMA, AML, etc.
   - Beteiligte Systeme/Akteure

2. **Verbesserungsvorschläge** (immer, vor "Verwandte Seiten")
   - Priorisierte Verbesserungen aus der Analyse
   - Ticket-Tabelle:

   ```
   | Ticket | Beschreibung | Priorität | Status |
   |--------|-------------|-----------|--------|
   | {PROJ}-{FEAT}-001 | ... | P1 – Hoch | Offen |
   | {PROJ}-{FEAT}-002 | ... | P2 – Mittel | Offen |
   ```

   Ticket-ID-Muster: `{PROJ}-{FEAT}-{NNN}` (z.B. `ESTB-EMAIL-001`)

3. **Verwandte Seiten** (immer, am Ende)
   - Cross-Links zu Security- und DORA-Analyse (liegen unter security/reviews/):
     - `[Sicherheitsanalyse](/{wikiBase}/security/reviews/{feature-name}-security)`
     - `[DORA-Compliance](/{wikiBase}/security/reviews/{feature-name}-dora)`
   - Links zu verwandten Architektur-Seiten

### Optionale Abschnitte (je nach Feature)

- **Prozessdiagramm** – ASCII End-to-End-Ablauf
- **Datenmodell** – Tabelle mit Feldern, Typen, Beschreibungen
- **State Machine** – ASCII-Zustandsdiagramm + Zustandsbeschreibung als Tabelle
- **Ablauf/Workflow** – Nummerierte Schritte oder Flussdiagramm
- **API-Endpunkte** – Tabelle: Endpoint, Methode, Rollen, Zweck
- **Statuscodes/Mapping** – Tabelle mit Codes und Bedeutung
- **Fehlerbehandlung** – Fehlerszenarien und Reaktionen
- **Admin-Funktionen** – Admin-Dashboard-Features
- **Compliance/Audit** – Was wird auditiert, wie
