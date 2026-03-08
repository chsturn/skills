---
name: vvv-abgleich
description: |
  **VVV-Abgleich**: Automatischer Abgleich von Vermögensverwaltungsverträgen (PDFs) mit den zugehörigen JSON-Daten (questionnaire-data.json, broker-data.json, partner-data.json) aus E2E-Onboarding-Tests.
  - MANDATORY TRIGGERS: VVV, Vermögensverwaltungsvertrag, Abgleich, Onboarding-Test, questionnaire-data, should_onboard
  - Verwende diesen Skill immer wenn der User Testdaten aus Onboarding-Runs mit generierten PDFs vergleichen will, auch wenn er nur "vergleich die Daten" oder "stimmt das PDF?" sagt.
---

# VVV-Abgleich Skill

## Zweck

Dieser Skill gleicht die Daten aus E2E-Onboarding-Test-Outputs mit den generierten Vermögensverwaltungsverträgen (PDFs) ab. Er prüft ob alle Kundendaten, Strategie-Auswahl, Bank-Wahl, Broker- und Partner-Daten korrekt ins PDF übernommen wurden.

## Verzeichnisstruktur der Test-Outputs

Jeder Onboarding-Test erzeugt einen Ordner mit diesem Aufbau:

```
should_onboard_successfully_with_<Testname>_<Timestamp>/
├── questionnaire-data.json    # Alle Kundendaten, Strategie, Risikoprofil etc.
├── broker-data.json           # Tippgeber/Vermittler-Daten (optional)
├── partner-data.json          # Partner-Daten bei Partnerstrategien (optional)
├── estably/
│   └── Vermögensverwaltungsvertrag Estably.pdf
└── bank/
    └── (Bankdokumente - nicht Teil dieses Abgleichs)
```

## Workflow

1. **Batch-Erkennung**: Finde alle `should_onboard_*` Verzeichnisse im angegebenen Pfad
2. **PDF-Extraktion**: Nutze `pdftotext -layout` (nicht pdfplumber!) um Text aus den PDFs zu extrahieren. pdfplumber übersieht überlagerte Textlayer, pdftotext erfasst sie zuverlässig.
3. **JSON-Parsing**: Lade alle drei JSON-Dateien pro Testordner
4. **Abgleich**: Prüfe ob die JSON-Werte im PDF-Text vorkommen
5. **Report**: Erstelle einen Markdown-Report mit Ergebnissen

## Wichtig: PDF-Textextraktion

Verwende IMMER `pdftotext -layout` statt Python-Libraries wie pdfplumber oder PyPDF. Der Grund: Die Estably-PDFs haben überlagerte Textlayer für die befüllten Felder, die von Python-Libraries oft nicht erkannt werden. `pdftotext` ist hier der einzige zuverlässige Weg.

```bash
pdftotext -layout "<pdf_path>" "<output_txt_path>"
```

## Abzugleichende Felder

### Aus questionnaire-data.json

**Persönliche Daten** (Frage `angabe`):
- `vorname` → Im PDF als Vorname des Kunden
- `nachname` → Im PDF als Name des Kunden
- `geburtsdatum` → Format im PDF: DD.MM.YYYY (ISO → umwandeln!)
- `familienstand` → Im Kundenprofil (Anhang 2)
- `geburtsort` → Steht NICHT im VVV (nur in Bankdokumenten) → ignorieren

**Adressdaten** (Frage `personlichen-daten`):
- `strasse` + `hausnummer` → zusammen als Adresse
- `plz` + `wohnort` → zusammen als PLZ und Ort
- `mobile` → Telefonnummer
- `land` → Länderkürzel (DE, AT etc.) wird im PDF als Klartext dargestellt (Deutschland, Österreich)

**E-Mail**: Top-Level-Feld `email` im JSON

**Berufliche Daten** (Frage `angabe-person`):
- `employments[0].job` → Beruf im Kundenprofil
- `educationDescriptionOther` → Erlernter Beruf
- `employments[0].employer` → Steht NICHT im VVV → ignorieren

**Strategie** (Frage `strategie-auswahl`):
- `strategie` → Mapping auf PDF-Text:
  - `value20fund` → "Value 20"
  - `value40fund` → "Value 40"
  - `value60fund` → "Value 60"
  - `value80fund` → "Value 80"
  - `value100fund` → "Value 100"
  - `value100millercrypto` → "Miller Krypto-Strategie" oder "CRYPTOSTRATEGIE"
  - `value100secure` → "Sicherungsstrategie" oder "SECURE"
  - `valueGreen` → "Value Green"

**Bank** (Frage `bank-wahl`):
- `bank` → Mapping:
  - `baader` → "Baader Bank"
  - `llb` → "Liechtensteinische Landesbank"

**Risikoprofil** (Frage `wertminerung`):
- `wertminerung: "0%"` → "Sehr gering" / "0-3"
- `wertminerung: "10%"` → "Gering" / "4-7"
- `wertminerung: "20%"` → "Eher gering" / "8-11"
- `wertminerung: "30%"` → "Mittel" / "12-15"
- `wertminerung: "40%"` → "Hoch" / "16-19"
- `wertminerung: "50%"` → "Sehr hoch" / "20-24"

**Nachhaltigkeit** (Frage `sustainable`):
- `interested: "no"` → "keine Nachhaltigkeitspräferenz"
- `interested: "yes"` → Nachhaltigkeitspräferenz vorhanden

**Anlageziele** (Frage `geldanlage-ziel`):
- `aufbau: true` → "Vermögensaufbau"
- `preserveAssets: true` → "Vermögenserhalt"

### Aus broker-data.json

Nur relevant wenn `generateBrokerAttachment: true`:
- `companyName` → Im Tippgeber-Anhang
- `street`, `postalCode`, `city`, `country` → In der Informationsvollmacht

### Aus partner-data.json

Array von Partnern. Relevant ist der Partner, dessen `strategyGroups` die gewählte Strategie enthält (z.B. `groupName: "millercrypto"`). Felder:
- `companyName` → Im Partner-Anhang
- `street`, `postalCode`, `city`, `country` → In der Informationsvollmacht

**Felder die bewusst NICHT im VVV stehen** (keine Fehler melden):
- Geburtsort
- Arbeitgeber
- IBAN
- Steuernummer
- Ausweisnummer

## Ausführung

Führe das Script `scripts/vvv_compare.py` aus:

```bash
python3 <skill-path>/scripts/vvv_compare.py [verzeichnis] [--format html] [--output <report-pfad>]
```

### Standard-Verzeichnis

Wenn kein Verzeichnis angegeben wird, wird automatisch `web/apps/fe-web-e2e/cypress/downloads` relativ zum CWD verwendet. Das ist der Standard-Output-Pfad der E2E-Onboarding-Tests.

### Parameter

- `directory` (optional): Verzeichnis mit `should_onboard_*` Ordnern. Default: `<CWD>/web/apps/fe-web-e2e/cypress/downloads`
- `--format` / `-f`: Report-Format, `html` (Standard) oder `md`
- `--output` / `-o`: Pfad für den Report (Standard: `<verzeichnis>/vvv-abgleich-report.<format>`)

### HTML-Report (Standard)
- Aufklappbare Sektionen pro Test (fehlgeschlagene Tests sind automatisch aufgeklappt)
- Summary-Cards mit Gesamtstatistik oben
- Sauberes, responsives Layout
- Direkt im Browser öffenbar

### Markdown-Report
- Klassisches tabellarisches Format mit Emoji-Status

Falls das Script nicht vorhanden ist oder Fehler wirft, folge der Logik manuell nach dem oben beschriebenen Workflow.
