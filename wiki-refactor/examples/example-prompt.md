# Beispiel: Generierter Umsetzungs-Prompt

Dieses Beispiel zeigt einen generierten Prompt für das DORA-Ticket ESTB-SEC-FEE-001 aus der Fees-Wiki-Seite.

---

# Audit-Logging für manuelle Fee-Konfigurationsänderungen

**Ticket:** ESTB-SEC-FEE-001 | **DORA:** Art. 9 | **Priorität:** P0
**Wiki-Quelle:** projekte/estably/features/fees (Seite: "Estably – Gebührenberechnung & Fee-Management")

## Kontext

DORA Art. 9 (Protection & Prevention) erfordert die vollständige Nachvollziehbarkeit aller Änderungen an Finanzdaten. Manuelle Änderungen an der Gebührenkonfiguration (Strategie-Zuweisung, Performance-Fee-Aktivierung, Referenzwährung) werden aktuell ohne Audit-Trail durchgeführt. Bei einer FMA-Prüfung wäre nicht nachweisbar, wer wann welche Gebührenparameter geändert hat.

## Aktueller Zustand

Die Fee-Controller führen Änderungen direkt aus, ohne Audit-Logging:

**server/src/controllers/fees/onSetStrategy.js:**
```javascript
module.exports = async (req, res) => {
  const { iban, strategy, bank } = req.body;
  // ... Validierung ...
  await IbanModel.updateOne({ iban }, { $set: { strategy } });
  res.json({ success: true });
};
```

Kein Audit-Eintrag wird geschrieben. Es ist nicht nachvollziehbar wer die Strategie geändert hat.

**Referenz-Muster (aus server/src/services/depot/depotStatusService.js):**
```javascript
// Im Depotstatus-Modul existiert bereits ein History-Pattern:
iban.depotStatus.push({
  status: newStatus,
  changedBy: userId,
  changedAt: new Date(),
  reason: reason
});
```

## Was du tun musst

### Schritt 1: Lies die betroffenen Dateien
Lies folgende Dateien und verstehe die aktuelle Implementierung:
- `server/src/controllers/fees/onSetStrategy.js` – Strategie-Zuweisung
- `server/src/controllers/fees/onSetPerformanceFee.js` – Performance-Fee-Aktivierung
- `server/src/controllers/fees/onSetReferenceCurrency.js` – Referenzwährung setzen
- `server/src/controllers/fees/onDeleteReferenceCurrency.js` – Referenzwährung löschen
- `server/schemas/iban.js` – IBAN-Schema (dort könnten Fee-History-Felder ergänzt werden)

Falls die Dateien umbenannt wurden, suche mit:
```
Glob: server/src/controllers/fees/**/*.js
Grep: "onSet" in server/src/controllers/fees/
```

### Schritt 2: Audit-Log-Einträge in die Controller einbauen
Ergänze in jedem der 4 Controller (onSetStrategy, onSetPerformanceFee, onSetReferenceCurrency, onDeleteReferenceCurrency) einen Audit-Log-Eintrag **vor** der Antwort an den Client.

Der Audit-Eintrag sollte folgende Informationen enthalten:
- `action`: Was wurde geändert (z.B. `"fee.strategy.changed"`)
- `userId`: Wer hat die Änderung durchgeführt (`req.user._id`)
- `iban`: Welches Depot betroffen ist
- `previousValue`: Alter Wert (vor der Änderung lesen)
- `newValue`: Neuer Wert
- `timestamp`: Zeitpunkt der Änderung

Orientiere dich am bestehenden History-Pattern im Depot-Status-Modul.

### Schritt 3: Verifikation
Verifiziere durch Suche, dass alle Fee-Mutations-Endpunkte Audit-Logging haben:
```
Grep: "audit" in server/src/controllers/fees/
```

Prüfe, dass der alte Wert **vor** dem Update gelesen wird (nicht danach).

## Definition of Done
- [ ] Alle 4 Fee-Mutations-Controller schreiben Audit-Log-Einträge
- [ ] Alter und neuer Wert werden protokolliert
- [ ] User-ID des Ausführenden wird erfasst
- [ ] Keine sensiblen Daten in den Audit-Logs (keine Passwörter, Tokens)
- [ ] Code folgt den bestehenden Patterns im Projekt

## Betroffene Dateien
| Datei | Änderung |
|-------|----------|
| server/src/controllers/fees/onSetStrategy.js | Audit-Logging ergänzen |
| server/src/controllers/fees/onSetPerformanceFee.js | Audit-Logging ergänzen |
| server/src/controllers/fees/onSetReferenceCurrency.js | Audit-Logging ergänzen |
| server/src/controllers/fees/onDeleteReferenceCurrency.js | Audit-Logging ergänzen |

## Hinweise
- Das Depotstatus-Modul hat bereits ein History-Pattern das als Vorlage dient
- Prüfe ob ein zentraler Audit-Service existiert oder ob einer erstellt werden muss
- Verwandtes Ticket: ESTB-SEC-FEE-002 (Legacy-Controller Fehlerbehandlung) betrifft teilweise dieselben Dateien
