# Wiki-Struktur & Pfad-Regeln

Verbindliche Regeln fuer die Ablage von Wiki-Seiten. Diese Struktur ist DORA-konform und muss bei jeder Seitenerstellung eingehalten werden.

## Pfad-Regeln

### Projekte

Jedes Projekt folgt der gleichen Unterstruktur:

```
projekte/{projekt}/
  architektur/                      <- Technische Architektur-Doku
    system-overview
    backend-services
    frontend-architecture
    data-model
    mobile-app                      <- Falls vorhanden
  features/                         <- Feature-Dokumentation
    {feature}                       <- Einzelseite fuer einfache Features
    {gruppe}/                       <- Gruppierung nach Domaene
      {feature}
  betrieb/                          <- Deployment, CI/CD, Tests, Migration
    deployment
    ci-cd
    migration
    e2e-tests
  security/                         <- Security & DORA pro Projekt
    uebersicht                      <- Gesamtstatus, Findings-Zusammenfassung
    tasks                           <- Offene Security-Tasks
    reviews/                        <- Feature-spezifische Reviews
      {feature}-security            <- Sicherheitsanalyse
      {feature}-dora                <- DORA-Compliance-Analyse
```

### Feature-Gruppen (nur Estably)

Estably-Features werden nach Domaene gruppiert:

| Gruppe | Pfad | Inhalte |
|--------|------|---------|
| Kunden | `features/kunden/` | Onboarding, Dashboard, ITM, Ordermanagement, Dokumenten-Flow, DocumentFill |
| Compliance | `features/compliance-features/` | Riskmap, OFAC, Transaction Monitoring, Contract History |
| Daten | `features/daten/` | Daily Data, CSV-Import, Transaktionsimport, CSV-Export |
| Admin | `features/admin/` | Admin Home, Riskmaps, User Management, Email-Edit, Depotstatus, Fees |
| Top-Level | `features/` | Auth (Querschnitt) |

### Compliance (uebergreifend)

```
compliance/
  uebersicht                        <- Audit-Einstieg: Compliance-Matrix, Links zu allem
  gap-analyse                       <- Priorisierte offene Punkte
  asset-inventar                    <- Art. 7: Alle IKT-Systeme
  dora/                             <- DORA-Theorie & Anforderungen
    ikt-risikomanagement            <- Art. 5-16
    incident-management             <- Art. 17-23
    resilience-testing              <- Art. 24-27
    third-party                     <- Art. 28-44
  incident-management/              <- Operative Umsetzung
    runbook
    fma-meldung
  third-party/                      <- Operative Umsetzung
    register
    exit-strategien
  business-continuity/              <- Art. 11
    backup-strategie
    wiederherstellungstests
  testing/                          <- Art. 24-27 operativ
    testplan
    ergebnisse
  reviews/                          <- Art. 12: Jaehrliche Nachweise
    {jahr}
  kommunikationsplan                <- Art. 13
```

### Standards

```
standards/
  coding-standards                  <- Allgemein (TypeScript)
    angular                         <- Angular-spezifisch
    nodejs                          <- Node.js-spezifisch
    testing                         <- Test-Standards
  infrastructure                    <- Docker Swarm, Traefik, etc.
  wiki-skills                       <- Skill-Dokumentation
```

### Memory (AI-Agent intern)

```
memory/                             <- Nur fuer AI-Agent-Kontext
  security
  dora
  infrastruktur
  entscheidungen
  projekte
  killswitch
```

## Pfad-Aenderungen und interne Links

Wiki.js unterstuetzt Pfad-Aenderungen via Update-Mutation (neuen `path` im Update mitgeben). Wenn Seiten verschoben werden, muessen **alle internen Links auf anderen Seiten** aktualisiert werden, die auf den alten Pfad verweisen. Vor Pfad-Aenderungen immer ein Link-Mapping (alt → neu) erstellen und danach alle betroffenen Seiten durchsuchen und fixen.

## Entscheidungsbaum: Wo gehoert eine neue Seite hin?

```
Ist es eine DORA-Anforderung (Theorie)?
  -> compliance/dora/

Ist es ein operativer Compliance-Prozess (Runbook, Meldeformular, BCP)?
  -> compliance/{bereich}/

Ist es eine Feature-Dokumentation?
  -> projekte/{projekt}/features/{gruppe}/{feature}

Ist es eine Security/DORA-Analyse eines Features?
  -> projekte/{projekt}/security/reviews/{feature}-{typ}

Ist es Projekt-Architektur?
  -> projekte/{projekt}/architektur/{seite}

Ist es Deployment/CI-CD/Tests/Migration?
  -> projekte/{projekt}/betrieb/{seite}

Ist es ein uebergreifender Standard?
  -> standards/{seite}
```

## Abgrenzung: Theorie vs. Operativ

| compliance/dora/* | compliance/{bereich}/* |
|---|---|
| WAS DORA verlangt | WIE WIR es umsetzen |
| Artikel-Referenzen | Runbooks, Checklisten |
| Anforderungs-Mapping | Konkrete Prozesse |
| Aendert sich selten | Wird regelmaessig aktualisiert |

## Pfad-Muster fuer den Wiki-Skill

| Seitentyp | Pfad-Muster |
|-----------|------------|
| Projekt-Index | `projekte/{projekt}` |
| Architektur-Index | `projekte/{projekt}/architektur` |
| Architektur-Seite | `projekte/{projekt}/architektur/{seite}` |
| Feature-Index | `projekte/{projekt}/features` |
| Feature-Gruppe-Index | `projekte/{projekt}/features/{gruppe}` |
| Feature-Seite (functional) | `projekte/{projekt}/features/{gruppe}/{feature}` |
| Betrieb-Index | `projekte/{projekt}/betrieb` |
| Betrieb-Seite | `projekte/{projekt}/betrieb/{seite}` |
| Security-Index | `projekte/{projekt}/security` |
| Security-Uebersicht | `projekte/{projekt}/security/uebersicht` |
| Security-Review | `projekte/{projekt}/security/reviews/{feature}-security` |
| DORA-Review | `projekte/{projekt}/security/reviews/{feature}-dora` |
