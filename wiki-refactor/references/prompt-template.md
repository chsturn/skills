# Prompt-Template für Umsetzungs-Prompts

Jeder generierte Prompt muss **eigenständig** sein – er enthält alles was ein Claude Code Agent braucht um die Aufgabe ohne zusätzlichen Kontext auszuführen.

## Template

```markdown
# {task-title}

**Ticket:** {ticket-id} | **DORA:** Art. {article} | **Priorität:** {priority}
**Wiki-Quelle:** {wiki-path} (Seite: "{wiki-title}")

## Kontext

{2-3 Sätze: Warum ist diese Änderung nötig? Welche regulatorische Anforderung (DORA-Artikel, FMA, AML)
erfordert sie? Was passiert wenn sie nicht umgesetzt wird?}

## Aktueller Zustand

{Beschreibung des aktuellen Code-Zustands. Referenziere spezifische Dateien und was sie tun.
Füge relevante Code-Ausschnitte ein die den Ist-Zustand zeigen.}

**{dateipfad}:**
\`\`\`{sprache}
{relevanter Code-Ausschnitt}
\`\`\`

{Falls es Referenz-Implementierungen gibt die als Muster dienen:}

**Referenz-Muster (aus {andere-datei}):**
\`\`\`{sprache}
{Code der zeigt wie es anderswo im Projekt gelöst ist}
\`\`\`

## Was du tun musst

### Schritt 1: Lies die betroffenen Dateien
{Liste aller Dateien die gelesen werden müssen, mit Hinweis worauf zu achten ist.
Falls Dateien umbenannt worden sein könnten, Suchmuster angeben.}

### Schritt 2: {Aktion}
{Detaillierte Anweisung. Referenziere Muster aus der Codebase.
Gib Code-Beispiele wo hilfreich (aber keine Copy-Paste-Lösungen).}

### Schritt 3: {Aktion}
{...}

### Schritt N: Verifikation
{Wie die Änderung verifiziert wird:
- Grep-Suchen um zu bestätigen dass die Änderung überall angewandt wurde
- Test-Befehle falls vorhanden
- Manuelle Prüfschritte}

## Definition of Done
- [ ] {Kriterium 1 – direkt abgeleitet aus der DORA-Anforderung}
- [ ] {Kriterium 2}
- [ ] {Kriterium 3}
- [ ] Keine neuen Sicherheitslücken eingeführt
- [ ] Code folgt den bestehenden Patterns im Projekt

## Betroffene Dateien
| Datei | Änderung |
|-------|----------|
| {pfad} | {was sich ändert} |
| {pfad} | {was sich ändert} |

## Hinweise
{Gotchas, Warnungen, verwandte Tickets die beachtet werden sollten.
Falls die Änderung andere Module betrifft, hier erwähnen.}
```

## Regeln für die Prompt-Generierung

1. **Sprache:** Deutsch (konsistent mit Wiki und bestehenden Prompts)
2. **Code-Ausschnitte:** Nur aktuellen Zustand und Referenz-Muster zeigen, keine fertigen Lösungen
3. **Dateipfade:** Relativ zum Projekt-Root (z.B. `server/src/routes/fees.routes.js`)
4. **Keine Secrets:** Keine API-Keys, Tokens, Passwörter oder interne IPs in Prompts
5. **Kontext-Vollständigkeit:** Jeder Prompt muss den regulatorischen Hintergrund erklären
6. **Verifikation:** Jeder Prompt muss einen Verifikationsschritt haben
7. **Definition of Done:** Mindestens 3 Kriterien, davon mindestens eines aus der DORA-Anforderung
