# Memory Curator

Sammlung der aktuellen Dateien rund um den 02:00-Uhr-Memory-Curator.

## Zweck

Der Memory Curator pflegt und prüft die Memory-Schicht rund um:
- FalkorDB (`carlo_memory`)
- Qdrant (`carlo_memory`)
- Ollama Embeddings
- OpenClaw Cron / Nachtbericht

Ziel:
- strukturelle Qualität prüfen
- Drift erkennen
- Sync stabil halten
- kompakte Nachtberichte erzeugen

## Dateien

### `memory-curator.md`
Prompt / Ablaufbeschreibung für den Curator-Run.

### `memory-curator-known-states.yaml`
Bekannte Sonderfälle und Ausnahmen.
Verhindert unnötige Fehlalarme.

### `memory-curator-precheck.py`
Erzeugt strukturierte Findings vor dem eigentlichen Curator-Lauf.
Prüft u. a.:
- fehlende Projektfelder
- TODOs ohne `ABOUT`
- Services ohne Relationen
- Qdrant-Chunks ohne `graph_ref(s)`
- bekannte Sonderfälle

### `memory-curator-report.py`
Baut aus den Findings einen kompakten, priorisierten Bericht.

### `memory-curator-report-guidelines.md`
Regeln für Berichtsstil, Gruppierung und Priorisierung.

### `heartbeat-delta.py`
Prüft Live-/Infra-Deltas und vergleicht sie mit dem bekannten Zustand.

### `graphrag-sync.py`
Synchronisiert Inhalte in FalkorDB/Qdrant.
Enthält das robuste Chunking und die `graph_ref`-Fallbacks.

## Typischer Ablauf

1. `memory-curator-precheck.py`
2. Known-State-Auswertung
3. `heartbeat-delta.py`
4. `graphrag-sync.py --all`
5. `memory-curator-report.py`
6. LLM-Bericht / Telegram-Ausgabe

## Hinweise

- Die eigentliche Source of Truth bleibt auf `.100`
- Diese Dateien sind die aktuell extrahierte Arbeitskopie des Curator-Setups
- `estably_graphrag` wird davon nicht berührt
