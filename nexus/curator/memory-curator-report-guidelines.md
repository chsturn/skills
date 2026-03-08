# Memory Curator Report Guidelines

## Ziel
Nachtberichte sollen kurz, priorisiert und handlungsorientiert sein.

## Reihenfolge
1. critical
2. important
3. housekeeping/info

## Format
- maximal 5 Highlights
- wenn mehrere Findings dasselbe Projekt/Service betreffen: zusammenfassen
- bekannte / erwartete Zustände nicht dramatisieren
- wenn alles sauber ist: `Memory-Audit clean ✅`

## Gruppierungsregeln
- Gleicher `entity`-Prefix (z. B. `Project:HSV`, `Service:hsv`) -> zusammenfassen
- Mehrere Completeness-Themen zu Projekten -> als Sammelpunkt nennen
- Qdrant-/Graph-Hygiene-Themen als eigener Block

## Gute Formulierungen
- "X strukturelle Lücken gefunden" statt Rohdatenliste
- "bekannter Sonderfall, kein Handlungsbedarf" statt Alarmton
- "Sync stabil, aber Y Legacy-Hinweise bleiben" statt unkommentierter Zahlen

## Schlechte Formulierungen
- reine Query-Rohdaten
- jede Kleinigkeit als eigener Bullet
- bekannte Sonderfälle als Warnung
