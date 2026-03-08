# Projekt-Workflow

Gesamtanalyse und Dokumentation eines Projekts. Für Push-Workflow siehe SKILL.md.

## Phase 1: Projekt-Überblick gewinnen

Systematisch erfassen:

### Grundlagen
- `package.json` (Root + Unterverzeichnisse): Tech-Stack, Dependencies, Scripts
- `README.md`: Projektbeschreibung
- `docker-compose.yml` / `Dockerfile`: Deployment-Setup
- `.env.example`: Konfigurationsparameter
- Ordnerstruktur: `ls -la` auf Root, `src/`, `apps/`

### Backend
- **Framework**: Express, Fastify, NestJS, etc.
- **Schemas/Models**: Alle Dateien in `schemas/`, `models/`, `entities/`
- **Routes**: Alle Route-Definitionen
- **Middleware**: Auth, Rate Limiting, CORS, etc.
- **Services**: Geschäftslogik-Layer
- **External Integrations**: API-Clients, Webhooks, SFTP, etc.

### Frontend
- **Framework**: Angular, React, Vue, etc.
- **Routing**: App-Routing-Module
- **Komponenten-Struktur**: Hauptkomponenten und Feature-Module
- **State Management**: NgRx, Signals, Context, etc.
- **UI-Library**: Material, PrimeNG, Tailwind, etc.

### Infrastruktur
- **Datenbank**: MongoDB, PostgreSQL, etc.
- **Caching**: Redis, in-memory, etc.
- **Message Queue**: BullMQ, RabbitMQ, etc.
- **File Storage**: SFTP, S3, etc.

## Phase 2: Standard-Seiten generieren

6 Seiten erstellen. Für jede: Markdown generieren, in `/tmp/wiki-{seite}.md` schreiben, per wiki-push.mjs pushen.

### 2.1 System Overview

**Wiki-Pfad:** `{wikiBase}/architektur/system-overview`

Inhalt:
- Systemkontext und Zweck (2-3 Absätze)
- Akteure und ihre Rollen (Tabelle)
- Komponentendiagramm (ASCII)
- Tech-Stack-Tabelle (Komponente | Technologie | Version)
- Externe Abhängigkeiten (Tabelle: System | Typ | Zweck)

### 2.2 Backend Services

**Wiki-Pfad:** `{wikiBase}/architektur/backend-services`

Inhalt:
- API-Struktur (Route-Module mit Verantwortung und Rollen)
- Authentifizierung & Autorisierung (Pattern, Rollen, Route-Schutz)
- Middleware-Stack (Tabelle: Package | Version | Zweck)
- Externe Integrationen (APIs, Webhooks, File-Transfer)
- Dependencies mit Handlungsbedarf (veraltete, unsichere Packages)

### 2.3 Frontend Architecture

**Wiki-Pfad:** `{wikiBase}/architektur/frontend-architecture`

Inhalt:
- Komponenten-Hierarchie (ASCII-Baum oder Tabelle)
- Routing-Struktur (Route | Component | Guard)
- State Management (Pattern, Store-Struktur)
- UI-Bibliothek und Design-System
- Build-Konfiguration

### 2.4 Data Model

**Wiki-Pfad:** `{wikiBase}/architektur/data-model`

Inhalt:
- Kernmodelle (Tabelle mit Feld-Kategorien)
- Collection-Übersicht (Name | Felder-Anzahl | Beschreibung)
- Relationen und Referenzen (ASCII-Diagramm)
- Indizes (Collection | Index | Typ | Zweck)

### 2.5 Security

**Wiki-Pfad:** `{wikiBase}/security/uebersicht`

Inhalt:
- Authentifizierung (Mechanismus, Session/Token-Management)
- Autorisierung (Rollen, Permissions, Route-Schutz)
- Bestaetigte Sicherheitskontrollen (Tabelle: Kontrolle | Status | Details)
- Bekannte Schwachstellen (falls vorhanden)
- Dependency-Risiken

### 2.6 Deployment

**Wiki-Pfad:** `{wikiBase}/betrieb/deployment`

Inhalt:
- Infrastruktur-Uebersicht (ASCII-Diagramm)
- Deployment-Prozess (Schritte)
- Umgebungen (Tabelle: Umgebung | URL | Zweck)
- Monitoring und Logging
- Backup-Strategie

## Phase 3: Index-Seiten erstellen

### Projekt-Index

**Wiki-Pfad:** `{wikiBase}`

```markdown
# {Projektname}

{Kurze Projektbeschreibung}

## Architektur

- [Systemuebersicht](/{wikiBase}/architektur/system-overview) – {Kurzbeschreibung}
- [Backend-Architektur](/{wikiBase}/architektur/backend-services) – {Kurzbeschreibung}
- [Frontend-Architektur](/{wikiBase}/architektur/frontend-architecture) – {Kurzbeschreibung}
- [Datenmodell](/{wikiBase}/architektur/data-model) – {Kurzbeschreibung}

## Betrieb

- [Deployment & Infrastructure](/{wikiBase}/betrieb/deployment) – {Kurzbeschreibung}

## Security

- [Sicherheitsanalyse](/{wikiBase}/security/uebersicht) – {Kurzbeschreibung}

## Tech-Stack

| Komponente | Technologie |
|-----------|-------------|
| Frontend | ... |
| Backend | ... |
| Datenbank | ... |
| ... | ... |
```

### Architektur-Index

**Wiki-Pfad:** `{wikiBase}/architektur`

```markdown
# {Projektname} – Architektur

Architektur-Dokumentation der {Projektname}-Plattform.

## Seiten

- [Systemuebersicht](/{wikiBase}/architektur/system-overview) – {Kurzbeschreibung}
- [Backend-Architektur](/{wikiBase}/architektur/backend-services) – {Kurzbeschreibung}
- [Frontend-Architektur](/{wikiBase}/architektur/frontend-architecture) – {Kurzbeschreibung}
- [Datenmodell](/{wikiBase}/architektur/data-model) – {Kurzbeschreibung}
```

### Betrieb-Index

**Wiki-Pfad:** `{wikiBase}/betrieb`

```markdown
# {Projektname} – Betrieb

- [Deployment & Infrastructure](/{wikiBase}/betrieb/deployment) – {Kurzbeschreibung}
```

### Security-Index

**Wiki-Pfad:** `{wikiBase}/security`

```markdown
# {Projektname} – Security & DORA

- [Sicherheitsanalyse](/{wikiBase}/security/uebersicht) – Gesamtstatus und Findings
```

## Phase 4: Push-Reihenfolge

1. Projekt-Index per wiki-push.mjs create -> Page-ID merken
2. Architektur-Index per wiki-push.mjs create -> Page-ID merken
3. Betrieb-Index per wiki-push.mjs create -> Page-ID merken
4. Security-Index per wiki-push.mjs create -> Page-ID merken
5. 6 Standard-Seiten per wiki-push.mjs create -> Page-IDs merken
6. Projekte-Uebersicht per wiki-push.mjs update (neuen Projekt-Link ergaenzen)
7. `wiki-projects.json` mit den neuen Page-IDs aktualisieren (inkl. betriebIndexPageId, securityIndexPageId)

## Phase 5: Projekte-Übersicht aktualisieren

Falls eine Projekte-Übersicht existiert, per GraphQL Read laden, neuen Eintrag ergänzen:

```markdown
---

## [{Projektname}](/projekte/{projekt})

{Kurze Projektbeschreibung}

**Tech-Stack:** {Framework}, {Backend}, {DB}, ...
```

In `/tmp/wiki-projekte-uebersicht.md` schreiben und per wiki-push.mjs update zurückschreiben.
