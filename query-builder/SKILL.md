---
name: query-builder
description: >
  **Estably MongoDB Query Builder**: Erstellt MongoDB Aggregation Pipelines für die Estably
  Vermögensverwaltungs-Plattform als Few-Shot-Beispiele. Liest die echten JSON-Schemas aus dem
  schemas/samples-Verzeichnis und erzeugt korrekte Pipelines mit collection, pipeline-Array,
  explanation und confidence.
  - MANDATORY TRIGGERS: /query-builder, Query bauen, Pipeline erstellen, Few-Shot Beispiel,
    MongoDB Query, Aggregation Pipeline, Estably Query, Daten-Chat Query
  - Verwende diesen Skill immer wenn der User eine MongoDB Query für Estably erstellen will,
    auch wenn er nur "schreib mir eine Query für..." oder "wie frage ich X ab?" sagt.
    Auch bei Erwähnung von Estably-Collections (users, contracts, ibans, userdailydata,
    dailypositions, banktransactions, brokers, documents, buisnesses) im Query-Kontext triggern.
---

# Estably MongoDB Query Builder

Du hilfst beim Erstellen von MongoDB Aggregation Pipelines für die Estably Vermögensverwaltungs-Plattform. Die Pipelines werden als Few-Shot-Beispiele im NL2MongoDB Daten-Chat verwendet, um die Query-Generierung durch das LLM zu verbessern.

## Erste Aktion – Schemas lesen

Lies **immer zuerst** die relevanten JSON-Schema-Dateien aus dem Projekt, bevor du eine Query erstellst. Die Schemas liegen hier:

```
nl2mongodb-service/schemas/samples/
```

Verfügbare Schema-Dateien (Glob-Pattern `schema-estably_*-{collection}-standardJSON.json`):
- `schema-estably_*-users-standardJSON.json` – Kunden, Berater, Admins
- `schema-estably_*-contracts-standardJSON.json` – Vermögensverwaltungsverträge
- `schema-estably_*-ibans-standardJSON.json` – Depots/Portfolios (BRIDGE-Collection!)
- `schema-estably_*-userdailydata-standardJSON.json` – Tägliche Depotwerte/AuM
- `schema-estably_*-dailypositions-standardJSON.json` – Einzelne Wertpapierpositionen
- `schema-estably_*-banktransactions-standardJSON.json` – Ein-/Auszahlungen
- `schema-estably_*-documents-standardJSON.json` – Plattform-Dokumente
- `schema-estably_*-buisnesses-standardJSON.json` – Wertpapier-Stammdaten
- `schema-estably_*-brokers-standardJSON.json` – Externe Broker
- `schema-estably_*-collaborativepartners-standardJSON.json` – Kooperationspartner

**Workflow:**
1. Analysiere die User-Frage: Welche Collections sind betroffen?
2. Lies die JSON-Schemas der betroffenen Collections (und ggf. der Join-Collections)
3. Prüfe die echten Feldnamen, Typen und Verschachtelungen im Schema
4. Baue die Pipeline basierend auf den echten Daten

Lies bei **jedem** Query-Bau mindestens das Schema der Start-Collection und der Join-Collections. So stellst du sicher, dass Feldnamen, Typen und Strukturen korrekt sind.

Zusätzlich kannst du die Referenz-Datei für Beziehungen und Query-Patterns konsultieren:
```
Read: <skill-directory>/references/estably-schema.md
```

## Ausgabeformat

Jede Query wird als JSON-Block ausgegeben, der direkt im Few-Shot-Dialog des Daten-Chats eingefügt werden kann:

```json
{
  "collection": "<start-collection>",
  "pipeline": [
    // MongoDB Aggregation Pipeline Stages
  ],
  "explanation": "<Was diese Query tut, auf Deutsch>",
  "confidence": 0.95
}
```

Dazu gehört immer die **natürliche Frage** in Deutsch, die ein Berater oder Admin stellen würde.

## Kritische Regeln

Diese Regeln sind der Kern korrekter Estably-Queries. Wenn du sie ignorierst, liefert die Query falsche oder keine Ergebnisse.

### Datumsformat YYYYMMDD
Alle `date`-Felder in userdailydata, dailypositions, banktransactions und documents sind **Number** im Format YYYYMMDD. Beispiel: 11. Februar 2026 = `20260211`. Niemals ein Date-Objekt oder einen String verwenden.

### Beziehungen zwischen Collections
```
users._id ──→ contracts.userId          (1:n)
users._id ──→ userdailydata.userId      (1:n)
users._id ──→ banktransactions.userId   (1:n)
users._id ──→ ibans.user               (1:n)  ⚠️ Feld heißt "user", nicht "userId"!
users.brokerId ──→ brokers._id         (1:1)

contracts._id ──→ ibans.contractId     (1:n)
ibans._id ──→ dailypositions.ibanId    (1:n)
ibans._id ──→ userdailydata.ibanId     (1:n)
```

### ibans als Brücke
`dailypositions` hat **kein userId-Feld**. Der Weg zum User führt immer über `ibans`:
```
users._id → ibans.user → ibans._id → dailypositions.ibanId
```

### $unwind vor Array-Zugriff
Arrays wie `contractHistory`, `items`, `questions.questions` müssen mit `$unwind` aufgelöst werden, bevor auf Subfelder zugegriffen wird. Ohne $unwind gibt $match auf Array-Subfelder oft unerwartete Ergebnisse.

### $sort VOR $group
Wenn du `$first` oder `$last` in einem `$group`-Stage verwendest, **muss** vorher ein `$sort` kommen. Sonst liefert `$first` einen willkürlichen Wert statt den neuesten/ältesten.

### accountClosed filtern
Bei Fragen nach "aktiven Depots", "verwaltetem Vermögen" oder "AuM" immer `accountClosed: false` als Filter setzen. Geschlossene Konten verfälschen die Summen.

### Kein $limit vor $group
`$limit` vor `$group` schneidet Daten ab, bevor sie aggregiert werden. Das führt zu falschen Ergebnissen. `$limit` gehört nach `$group` und `$sort`.

### Keine Expression-Operatoren in $project
Expression-Operatoren wie `$concat`, `$cond`, `$switch`, `$size`, `$ifNull` im `$project`-Stage werden vom NL2MongoDB-Service nicht unterstützt (MongoDB interpretiert sie als Feldpfade). Stattdessen Felder einzeln projizieren:
```json
// FALSCH:
{ "$project": { "kunde": { "$concat": ["$name", " ", "$lastname"] } } }

// RICHTIG:
{ "$project": { "name": 1, "lastname": 1 } }
```
Für berechnete Felder stattdessen einen `$addFields`-Stage VOR dem `$project` verwenden.

### Sub-Pipelines in $lookup sauber halten
Bei `$lookup` mit `let`/`pipeline`-Syntax:
- **Nur EINE `$match`-Stage** in der Sub-Pipeline, alle Bedingungen mit `$expr` + `$and` kombinieren
- **Keine separaten `$match`-Stages** für verschiedene Filter
- **Leeres Lookup-Ergebnis prüfen** mit `{ "$match": { "$expr": { "$eq": [{ "$size": "$fieldName" }, 0] } } }`

```json
// FALSCH – mehrere $match in Sub-Pipeline:
"pipeline": [
  { "$match": { "$expr": { "$eq": ["$ibanId", "$$ibanId"] } } },
  { "$match": { "date": 20260223 } }
]

// RICHTIG – eine $match mit $expr + $and:
"pipeline": [
  { "$match": { "$expr": { "$and": [
      { "$eq": ["$ibanId", "$$ibanId"] },
      { "$eq": ["$date", 20260223] }
  ]}}}
]

// RICHTIG – Leeres Lookup-Ergebnis prüfen:
{ "$match": { "$expr": { "$eq": [{ "$size": "$positions" }, 0] } } }
```

### Feld-Zuordnung nach $lookup + $unwind beachten!
Nach einem `$lookup` + `$unwind` gehören die Felder zu verschiedenen Dokumenten. Im `$project` muss klar sein, welches Feld woher kommt:
- **Root-Felder** (z.B. aus `userdailydata`): direkt mit `1` oder Feldname referenzieren
- **Gejointe Felder** (z.B. aus `users` nach `$lookup as "user"`): mit `$user.feldname` referenzieren

```json
// FALSCH – allTimePerformance, bankName, strategy gehören zu userdailydata, NICHT zu user:
{ "$project": {
    "name": "$user.name",
    "allTimePerformance": "$user.allTimePerformance",
    "bankName": "$user.bankName"
}}

// RICHTIG – Root-Felder direkt, nur name/lastname vom gejointen user:
{ "$project": {
    "name": "$user.name",
    "lastname": "$user.lastname",
    "allTimePerformance": 1,
    "bankName": 1,
    "strategy": 1,
    "currentValue": 1
}}
```

**Faustregel:** Prüfe im JSON-Schema der Start-Collection, welche Felder dort definiert sind. Diese sind Root-Felder (mit `1` projizieren). Nur Felder die im Schema der gejointen Collection stehen, werden mit `$alias.feldname` referenziert.

### Collection-Wahl
- **Vermögenswerte/AuM/Portfoliowerte** → `userdailydata` (Feld: `currentValue`)
- **Einzelne Wertpapiere/Positionen** → `dailypositions` (Array: `items`)
- **Kundendaten/Persönliches** → `users`
- **Verträge/Strategien/History** → `contracts`
- **Transaktionen** → `banktransactions`
- **Depot-Metadaten/Brücke** → `ibans`

### Strategie-Suche
Strategienamen sind spezifisch (z.B. "value100gold", "value80gold", "value60gold"). Bei generischen Anfragen wie "Gold-Strategie" immer `$regex` mit case-insensitive Flag verwenden:
```json
{ "$regex": "gold", "$options": "i" }
```

### Persönliche Daten (Adresse, Geburtsdatum)
Liegen verschachtelt in `users.questions.questions.answer`. Pattern:
```
$unwind "$questions" → $unwind "$questions.questions" → $match "questions.questions.name": "personal-data" → $project auf answer-Subfelder
```

## Confidence-Bewertung

- **0.95-1.0**: Exakte Abfrage auf bekannte Felder, einfache Struktur
- **0.85-0.94**: Mehrere Joins, komplexere Logik, aber alle Felder bekannt
- **0.70-0.84**: Annahmen über Datenstruktur nötig, Regex-Matching
- **< 0.70**: Unsicher ob die Query korrekt ist, mehrere Interpretationen möglich

## Beispiel-Interaktion

**User:** "Welcher Kunde hat das höchste Gesamtvermögen?"

**Antwort:**

Frage: *Welcher Kunde hat das höchste Gesamtvermögen gruppiert über alle Depots am 11.02.2026?*

```json
{
  "collection": "userdailydata",
  "pipeline": [
    { "$match": { "date": 20260211, "accountClosed": false } },
    { "$group": { "_id": "$userId", "totalValue": { "$sum": "$currentValue" } } },
    { "$sort": { "totalValue": -1 } },
    { "$limit": 1 },
    { "$lookup": { "from": "users", "localField": "_id", "foreignField": "_id", "as": "user" } },
    { "$unwind": "$user" },
    { "$project": { "_id": 0, "name": "$user.name", "lastname": "$user.lastname", "totalValue": 1 } }
  ],
  "explanation": "Summiert die aktuellen Depotwerte aller aktiven Depots pro User am 11.02.2026 und gibt den Kunden mit dem höchsten Gesamtvermögen zurück.",
  "confidence": 0.95
}
```

## Tipps

- Wenn der User kein Datum nennt, frag nach oder verwende "aktuellstes Datum" (höchster date-Wert).
- Gib immer eine deutsche Erklärung der Pipeline-Logik mit, damit der User die Query nachvollziehen kann.
- Wenn mehrere Interpretationen möglich sind, nenne sie und lass den User wählen.
- Bei Unsicherheit über Feldnamen: **Immer im JSON-Schema nachschlagen** – die echten Schemas sind die einzige Wahrheit.
