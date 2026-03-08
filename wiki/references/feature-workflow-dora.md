# Feature-Workflow: DORA-Compliance-Analyse

Für Code-Suche siehe `shared-phases.md`. Für Push und Index-Update siehe SKILL.md Push-Workflow. Zusätzlich `references/dora-checklist.md` laden für die Prüfpunkte.

## Analyse-Fokus

### Relevante DORA-Artikel identifizieren

Nicht jeder Artikel ist für jedes Feature relevant:

- API-Endpunkte → **Art. 9** (Protection & Prevention)
- Datenverarbeitung → **Art. 9** (Verschlüsselung), **Art. 10** (Detection)
- Externe Integrationen → **Art. 28-30** (Third-Party Risk)
- Logging/Monitoring → **Art. 10** (Detection), **Art. 11** (Response & Recovery)
- Backup/Restore → **Art. 12** (Backup & Restoration)

### Pro Artikel den Code prüfen

1. **Ist-Zustand dokumentieren** — was ist implementiert?
2. **Gap identifizieren** — was fehlt gemäß DORA?
3. **Severity bewerten:**
   - **Kritisch**: Direkte regulatorische Verletzung, sofortiger Handlungsbedarf
   - **Hoch**: Signifikante Lücke, zeitnah schließen
   - **Mittel**: Best Practice fehlt, im nächsten Quartal
   - **Niedrig**: Verbesserungspotenzial, kein unmittelbares Risiko

### Checkliste anwenden

Die Tabellen in `dora-checklist.md` Zeile für Zeile gegen den Feature-Code prüfen.

## Markdown-Struktur

Alle Abschnitte sind Pflicht.

1. **Übersicht**
   - Feature-Kontext (1-2 Sätze)
   - Relevante DORA-Artikel (Auflistung mit Kurzbeschreibung)
   - Regulatorischer Rahmen: Verordnung (EU) 2022/2554, FMA Liechtenstein

2. **DORA-Zusammenfassung** – Gesamtübersicht:

   | Artikel | Beschreibung | Erfüllt | Teilweise | Nicht erfüllt |
   |---------|-------------|---------|-----------|---------------|
   | Art. 9 | Protection & Prevention | 5 | 3 | 2 |

3. **Detail pro Artikel** – Für jeden relevanten Artikel eine Sektion:

   ### Artikel 9 – Protection & Prevention

   | Prüfpunkt | Status | Ist-Zustand | Gap | Empfehlung |
   |-----------|--------|------------|-----|-----------|
   | Authentifizierung | ✅ Erfüllt | Passport.js + JWT | – | – |
   | CSRF-Schutz | ❌ Nicht erfüllt | Nicht implementiert | CSRF-Tokens fehlen | csurf-Middleware |
   | Rate Limiting | ⚠️ Teilweise | Nur Login-Route | Weitere ungeschützt | express-rate-limit |

   Status-Symbole: ✅ Erfüllt, ⚠️ Teilweise, ❌ Nicht erfüllt

4. **DORA-Ticket-Tabelle** – Priorisierte Gaps mit Handlungsempfehlungen:

   | Ticket | DORA Art. | Beschreibung | Priorität | Status |
   |--------|-----------|-------------|-----------|--------|
   | {PROJ}-{FEAT}-DORA-001 | Art. 9 | ... | P1 – Hoch | Offen |

   Ticket-ID: `{PROJ}-{FEAT}-DORA-{NNN}` (z.B. `ESTB-EMAIL-DORA-001`)

5. **Verwandte Seiten** – Cross-Links:
    - `[Funktionale Analyse](/{wikiBase}/features/{gruppe}/{feature})`
    - `[Sicherheitsanalyse](/{wikiBase}/security/reviews/{feature}-security)`
