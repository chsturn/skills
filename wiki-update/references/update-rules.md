# Update-Regeln

Regeln für den Wiki-Update-Prozess. Diese Regeln stellen sicher, dass Updates konsistent und minimal-invasiv sind.

## Grundprinzipien

1. **Struktur beibehalten**: Abschnitte nicht umsortieren, keine Hauptabschnitte umbenennen
2. **Gezielt ändern**: Nur Abschnitte aktualisieren die sich tatsächlich geändert haben
3. **Sprache beibehalten**: Deutsch (wenn die Seite deutsch ist), gleicher Schreibstil
4. **Kein Over-Engineering**: Keine zusätzlichen Abschnitte "weil sie nützlich wären"

## Wann Abschnitte aktualisieren

| Situation | Aktion |
|-----------|--------|
| Konfigurationswert hat sich geändert (z.B. Salt-Runden 8→12) | Wert in Tabelle aktualisieren |
| Bibliothek wurde ersetzt (z.B. bcrypt-nodejs → bcrypt) | Name und Version aktualisieren |
| Architektur hat sich geändert (z.B. Session → JWT) | Abschnitt komplett ersetzen |
| Neues Konzept eingeführt (z.B. Audit-Logging) | Neuen Abschnitt hinzufügen |
| Feature wurde entfernt | Abschnitt entfernen oder als "Entfernt" markieren |
| DORA-Ticket wurde umgesetzt | Status auf "Erledigt" setzen |

## Wann NICHT ändern

| Situation | Aktion |
|-----------|--------|
| Abschnitt beschreibt etwas das sich nicht geändert hat | Nicht anfassen |
| Kosmetische Verbesserungen möglich | Nicht anfassen (nur inhaltliche Änderungen) |
| Code wurde refactored aber Verhalten ist gleich | Nicht anfassen |
| Abschnitt hat andere Formatierung als gewünscht | Nicht anfassen |

## Neue Abschnitte

Nur hinzufügen wenn:
- Der Code ein **komplett neues Konzept** einführt (z.B. Audit-Logging, Token Rotation)
- Das Konzept für das Verständnis des Features wichtig ist
- Es nicht in einen bestehenden Abschnitt integriert werden kann

Platzierung:
- Neue Abschnitte nach dem thematisch nächsten bestehenden Abschnitt einfügen
- Nicht am Ende der Seite anhängen (außer es gibt keinen passenden Kontext)

## DORA-Ticket-Status

Bei DORA-Ticket-Tabellen:
1. Falls keine Status-Spalte vorhanden → Status-Spalte ergänzen
2. Umgesetzte Tickets: Status auf `✅ Erledigt` setzen
3. Ticket-Beschreibung aktualisieren falls die Umsetzung vom Original abweicht
4. Zusammenfassungstabelle ebenfalls aktualisieren (⚠️/❌ → ✅)
5. Detail-Tabellen: "Ist-Zustand" und "Status" aktualisieren

## Diagramme

- Nur aktualisieren wenn sich der dokumentierte **Flow tatsächlich geändert** hat
- Bei Architektur-Änderungen (z.B. Session → JWT): Diagramm anpassen
- ASCII-Diagramme beibehalten (kein Wechsel zu Mermaid o.ä.)

## Datenmodell

- Neue Felder/Collections dokumentieren
- Entfernte Felder markieren oder entfernen
- Feld-Typen und Beschreibungen aktualisieren
- Neue Indices dokumentieren (besonders TTL-Indices)

## Keine Code-Snippets

- Weiterhin abstrakt dokumentieren (Konzepte, nicht Implementation)
- Konfigurationswerte als Tabelle, nicht als Code-Block
- Algorithmen beschreiben, nicht zeigen
