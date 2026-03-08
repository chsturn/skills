# Estably MongoDB Schema Reference

Diese Referenz enthält alle Collections, Felder, Beziehungen und Query-Patterns der Estably-Plattform.

---

## Collection-Übersicht

| Collection | Beschreibung | Wichtigste Felder |
|------------|-------------|-------------------|
| `users` | Kunden, Berater, Admins | name, lastname, email, rol, statuses |
| `contracts` | Vermögensverwaltungsverträge | userId, contractHistory, riskmap, fixedOnboardingStrategy |
| `ibans` | Depots/Portfolios (BRIDGE!) | user, bankName, snr, account, strategyValue |
| `userdailydata` | Tägliche Depotwerte/AuM | userId, ibanId, date (YYYYMMDD), currentValue, strategy, accountClosed |
| `dailypositions` | Einzelne Wertpapierpositionen | ibanId, date (YYYYMMDD), items[] (ISIN, Kurs, Menge) |
| `banktransactions` | Ein-/Auszahlungen | userId, transactionDate (YYYYMMDD), saldo, bankCodeText |
| `brokers` | Externe Broker | token, companyName, brokerTag |
| `collaborativepartners` | Kooperationspartner | token, companyName, partnerTag, strategyGroups |
| `documents` | Plattform-Dokumente | name, type, date (YYYYMMDD), userIds[], contractIds[] |
| `buisnesses` | Wertpapier-Stammdaten | name, isin, sector, asset_class_display |

---

## Kritische Regeln

### Datumsformat
Alle `date`-Felder in `userdailydata`, `dailypositions`, `banktransactions` und `documents` sind **Number im Format YYYYMMDD** (z.B. `20260211` = 11. Februar 2026). Niemals als Date-Objekt oder String matchen!

### ibans ist die Brücke
`dailypositions` hat **kein userId-Feld**. Um Positionen eines Users zu finden:
```
users._id → ibans.user → ibans._id → dailypositions.ibanId
```

### $unwind vor $match/$sort auf Array-Subfelder
Arrays wie `contractHistory`, `items`, `questions` müssen **immer** mit `$unwind` aufgelöst werden, bevor auf Subfelder gematcht oder sortiert wird.

### $sort IMMER vor $group
Wenn `$first` oder `$last` im `$group` verwendet wird, muss vorher `$sort` kommen. Sonst gibt `$first` einen zufälligen Wert zurück statt den neuesten!

### accountClosed-Filter
Bei Fragen nach "aktiven Depots" oder "verwaltetem Vermögen" immer `accountClosed: false` filtern.

### Kein $limit vor $group
`$limit` niemals vor `$group` setzen – das schneidet Daten ab bevor sie gruppiert werden.

---

## Beziehungen (Relationships)

```
users._id ──→ contracts.userId          (1:n)
users._id ──→ userdailydata.userId      (1:n)
users._id ──→ banktransactions.userId   (1:n)
users._id ──→ ibans.user               (1:n)
users.brokerId ──→ brokers._id         (1:1)

contracts._id ──→ ibans.contractId     (1:n)
ibans._id ──→ dailypositions.ibanId    (1:n)
ibans._id ──→ userdailydata.ibanId     (1:n)
```

---

## Collection-Details

### 1. users
Alle Plattform-User: Kunden, Berater, Admins, Compliance.

**Felder:**
- `name` (String) – Vorname
- `lastname` (String) – Nachname
- `email` (String, indexed) – Login-Email
- `rol` (String, indexed) – Enum: ADMIN, BERATER, COMPLIANCE, KUNDE, REVISION, BROKER
- `compliance` (Boolean) – Compliance-Check bestanden
- `soft_delete` (Boolean, indexed) – Soft-Delete Flag
- `depot_ids` (Array) – **DEPRECATED! Nicht verwenden!** Stattdessen $lookup auf userdailydata/ibans.
- `brokerId` (ObjectId) – Verknüpfter Broker
- `isAnalog` (Boolean) – Manuell erstellter Offline-Kunde
- `locked` (Boolean) – Account gesperrt
- `gekundigt` (Date) – Kündigungsdatum
- `clientNumber` (String) – Interne Kundennummer
- `statuses` (Array, indexed) – Status pro Vertrag. Enum: Onboarding, Before ITM, After ITM, After signature, Compliance, After compliance, Renew compliance, Finished, In opening, Cancelled, Broker
- `adminData.contractType` (String) – Vertragstyp aus Admin-Sicht
- `adminData.status` (String) – Gesamtstatus aus Admin-Sicht
- `adminData.bank` (String) – Zugewiesene Bank
- `questions` (Array) – Fragebogen-Antworten pro Vertrag. Struktur: questions[].contractId + questions[].questions[] (QuestionAnswerList mit name, answer, seen)
- `userData` (Array) – Gefilterte Fragebogen-Antworten (User-Level, nicht vertragsgebunden)
- `createdAt`, `updatedAt` (Date)

**Persönliche Daten (in questions.questions.answer):**
vorname, nachname, geburtsdatum, geburtsort, geburtsland, staatsangehorigkeit, strasse, hausnummer, plz, wohnort, land, anrede, familienstand, beruf, branche, arbeitgeber, einkommen, barvermogen, mobile, mobilePrefix

**Pattern für Adress-Abfrage:**
```json
[
  { "$unwind": "$questions" },
  { "$unwind": "$questions.questions" },
  { "$match": { "questions.questions.name": "personal-data" } },
  { "$project": {
      "questions.questions.answer.strasse": 1,
      "questions.questions.answer.hausnummer": 1,
      "questions.questions.answer.plz": 1,
      "questions.questions.answer.wohnort": 1,
      "questions.questions.answer.land": 1
  }}
]
```

---

### 2. contracts
Vermögensverwaltungsverträge.

**Felder:**
- `type` (String) – Enum: regular, shared
- `userId` (ObjectId, indexed) – Hauptkunde
- `secondaryUserId`, `thirdUserId` (ObjectId) – Weitere Kontoinhaber
- `contractNumber` (Number) – Vertragsnummer
- `createdDate` (Date) – Erstelldatum
- `fixedOnboardingStrategy` (String) – Vorausgewählte Anlagestrategie
- `contractHistory` (Array) – **MUSS $unwind werden!** Chronologisch, neuester Eintrag = aktueller Stand.
  - `state` – Enum: contract_in_progress, contract_released_for_customer_signature, contract_released_for_all_signatures, contract_initial, contract_released (= "freigegeben"/"aktiv"), contract_cancelled, contract_obsolete
  - `stateDate` (Date) – Statusänderung (Sort-Feld!)
  - `contractVersion` (String) – z.B. "1.0", "2.0"
  - `relatedAccounts` (Array) – bankName, iban, portfolio_number, snr, strategy
- `riskmap` (Object) – Eingebettetes Risikoprofil
- `contractData` (Array) – Vertragsdaten als QuestionAnswerList

**Pattern für Vertrags-Queries (von users aus):**
```json
[
  { "$match": { "name": "Max", "lastname": "Muster" } },
  { "$lookup": { "from": "contracts", "localField": "_id", "foreignField": "userId", "as": "userContracts" } },
  { "$unwind": "$userContracts" },
  { "$unwind": "$userContracts.contractHistory" },
  { "$sort": { "userContracts.contractHistory.stateDate": -1 } },
  { "$limit": 1 },
  { "$project": { "..." : 1 } }
]
```

**Pattern für Strategie-Abfragen:**
Die Strategie steht in `contractHistory.relatedAccounts[].strategy` oder in `ibans.strategyValue[].value` oder in `userdailydata.strategy`.

---

### 3. ibans (Depots/Portfolios)
Bank-Depots und Konten. **Brücke** zwischen Users und Positionen/Tageswerten!

**Felder:**
- `bankName` (String, indexed) – z.B. "baader", "llb"
- `snr` (Number, indexed) – Kundennummer bei Bank
- `iban` (String, indexed)
- `account` (String, indexed) – Interne Kontonummer
- `portfolio_number` (String, indexed) – Portfolionummer (default: "01")
- `contractId` (ObjectId, indexed) – Verknüpfter Vertrag
- `user` (ObjectId, indexed) – Verknüpfter Kunde (**Achtung: heißt "user", nicht "userId"!**)
- `strategyValue` (Array) – Strategie mit value, bindingDays, startDate
- `managementFee`, `performanceFee` (Array) – Gebühren (time-staged)
- `soft_delete.is_deleted` (Boolean)

---

### 4. userdailydata (Tägliche Depotwerte)
Täglicher Snapshot aller Portfolios. **Primärquelle für AuM und Vermögenswerte!**

**Felder:**
- `currentValue` (Number) – **Aktueller Depotwert in EUR** (Hauptfeld für AuM!)
- `date` (Number, indexed) – YYYYMMDD Format
- `account` (String, indexed) – Kontonummer
- `accountClosed` (Boolean) – **Konto geschlossen? Immer filtern bei "aktiven" Abfragen!**
- `bankName` (String, indexed)
- `contractId`, `ibanId`, `userId` (ObjectId, indexed)
- `strategy` (String) – Anlagestrategie
- `allTimePerformance` (Number) – Gesamt-Performance als Dezimalzahl
- `contractStart` (Number) – Vertragsbeginn YYYYMMDD
- `managementFee`, `bankFee`, `estbFee` (Number) – Gebühren in %
- `holdingsRatio` (Object) – Asset Allocation: stocks, cash, bonds, metal, crypto (jeweils 0-1)
- `transactions` (Array) – Tages-Transaktionen

**Pattern: Gesamtvermögen eines Users:**
```json
[
  { "$match": { "userId": { "$toObjectId": "..." }, "accountClosed": false } },
  { "$sort": { "date": -1 } },
  { "$group": { "_id": "$ibanId", "latestValue": { "$first": "$currentValue" }, "latestDate": { "$first": "$date" } } },
  { "$group": { "_id": null, "totalValue": { "$sum": "$latestValue" } } }
]
```

**Pattern: Gesamtes AuM aller aktiven Depots an einem Datum:**
```json
[
  { "$match": { "date": 20250110, "accountClosed": false } },
  { "$group": { "_id": null, "totalAuM": { "$sum": "$currentValue" }, "depotCount": { "$sum": 1 } } }
]
```

**Pattern: Vermögen pro Depot eines Users (via $lookup):**
```json
[
  { "$match": { "name": "Max", "lastname": "Muster" } },
  { "$lookup": { "from": "userdailydata", "localField": "_id", "foreignField": "userId", "as": "depots" } },
  { "$unwind": "$depots" },
  { "$sort": { "depots.date": -1 } },
  { "$group": {
      "_id": "$depots.ibanId",
      "currentValue": { "$first": "$depots.currentValue" },
      "account": { "$first": "$depots.account" },
      "bankName": { "$first": "$depots.bankName" },
      "strategy": { "$first": "$depots.strategy" },
      "date": { "$first": "$depots.date" }
  }},
  { "$group": {
      "_id": null,
      "portfolios": { "$push": { "ibanId": "$_id", "currentValue": "$currentValue", "account": "$account", "bankName": "$bankName", "strategy": "$strategy" } },
      "totalValue": { "$sum": "$currentValue" }
  }}
]
```

---

### 5. dailypositions (Einzelpositionen)
Tägliche Einzelpositionen (Aktien, Anleihen, ETFs) pro Depot.

**Felder:**
- `bank` (String, indexed)
- `contractId`, `ibanId` (ObjectId, indexed)
- `date` (Number, indexed) – YYYYMMDD
- `items` (Array) – **MUSS $unwind werden!** Subfelder pro Position:
  - `name` (String) – Wertpapiername
  - `isin` (String) – ISIN-Code
  - `type` (String) – "fund", "bond", "stock"
  - `typeDe` (String) – "Fonds", "Anleihe", "Aktie"
  - `quantity` (Number) – Stückzahl
  - `aktkurs` (Number) – Aktueller Kurs
  - `einkurs` (Number) – Kaufkurs
  - `valueCurrent` (Number) – Aktueller Gesamtwert
  - `valuePurchase` (Number) – Kaufwert
  - `winLosePercent` (Number) – Gewinn/Verlust in %
  - `percentOfTotal` (Number) – Anteil am Portfolio

**Achtung:** Kein userId-Feld! Immer über ibans joinen:
```json
[
  { "$match": { "date": 20260211 } },
  { "$lookup": { "from": "ibans", "localField": "ibanId", "foreignField": "_id", "as": "iban" } },
  { "$unwind": "$iban" },
  { "$lookup": { "from": "users", "localField": "iban.user", "foreignField": "_id", "as": "user" } },
  { "$unwind": "$user" },
  { "$match": { "user.name": "Max", "user.lastname": "Muster" } },
  { "$unwind": "$items" },
  { "$project": { "user.name": 1, "user.lastname": 1, "date": 1, "items.name": 1, "items.isin": 1, "items.valueCurrent": 1, "items.quantity": 1, "items.winLosePercent": 1, "items.type": 1 } }
]
```

---

### 6. banktransactions
Ein- und Auszahlungen.

**Felder:**
- `userId`, `contractId` (ObjectId, indexed)
- `transactionDate`, `transactionValuta` (Number, YYYYMMDD, indexed)
- `saldo` (Number) – Betrag
- `inOut` (String) – Ein- oder Auszahlung
- `bankCodeText` (String, indexed) – Buchungstext
- `currency` (String)
- `spgScore` (Number) – Risiko-Score (Default: 200)
- `monitoring` (Object) – AML-Monitoring Flags
- `verified` (Object) – Verifizierungsstatus

---

### 7. brokers
Externe Broker/Maklerbüros.

**Felder:**
- `token` (String, indexed) – Eindeutiger Broker-Token
- `companyName` (String)
- `brokerTag` (String, indexed) – Kürzel
- `visible` (Boolean) – Im Onboarding sichtbar
- `brokerageFee`, `brokeragePerformanceFee` (Array) – Gebühren

---

### 8. collaborativepartners
Kooperationspartner mit eigenen Strategiegruppen.

**Felder:**
- `token` (String, indexed)
- `companyName` (String)
- `partnerTag` (String, indexed) – Kürzel
- `active` (Boolean)
- `strategyGroups` (Array) – groupName, Gebührenaufteilung

---

### 9. documents
Plattform-Dokumente (Depotauszüge, Quartalsberichte, Verträge).

**Felder:**
- `name` (String, indexed) – Dokumentname (DE)
- `type` (String, indexed) – Technischer Typ-Code
- `date` (Number, indexed) – YYYYMMDD
- `userIds` (Array, indexed) – Verknüpfte User-IDs
- `contractIds`, `ibanIds` (Array, indexed)
- `issuedBy` (String) – Ersteller (z.B. "baader", "estably")

---

### 10. buisnesses (Wertpapier-Stammdaten)
Stammdaten handelbarer Wertpapiere. Achtung: Historischer Typo im Collection-Namen!

**Felder:**
- `name` (String, indexed) – Wertpapiername
- `isin` (String, indexed) – ISIN
- `sector` (String, indexed) – Branche
- `asset_class_display` (String) – Enum: cash, bonds, stocks, precious_metals, crypto
- `buisness_profile.de`, `buisness_profile.en` (String) – Firmenprofil

---

## Häufige Query-Patterns

### Höchstes Gesamtvermögen (gruppiert über Depots)
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
  ]
}
```

### Kontaktdaten der ersten N Kunden
```json
{
  "collection": "users",
  "pipeline": [
    { "$match": { "rol": "KUNDE", "soft_delete": false } },
    { "$sort": { "createdAt": 1 } },
    { "$limit": 10 },
    { "$unwind": "$questions" },
    { "$unwind": "$questions.questions" },
    { "$match": { "questions.questions.name": "personal-data" } },
    { "$project": {
        "name": 1, "lastname": 1, "email": 1,
        "strasse": "$questions.questions.answer.strasse",
        "hausnummer": "$questions.questions.answer.hausnummer",
        "plz": "$questions.questions.answer.plz",
        "wohnort": "$questions.questions.answer.wohnort",
        "mobile": "$questions.questions.answer.mobile"
    }}
  ]
}
```

### Erste Strategie eines Typs (z.B. Gold)
```json
{
  "collection": "contracts",
  "pipeline": [
    { "$unwind": "$contractHistory" },
    { "$unwind": "$contractHistory.relatedAccounts" },
    { "$match": { "contractHistory.relatedAccounts.strategy": { "$regex": "gold", "$options": "i" } } },
    { "$sort": { "contractHistory.stateDate": 1 } },
    { "$limit": 1 },
    { "$lookup": { "from": "users", "localField": "userId", "foreignField": "_id", "as": "user" } },
    { "$unwind": "$user" },
    { "$project": {
        "_id": 0,
        "strategy": "$contractHistory.relatedAccounts.strategy",
        "stateDate": "$contractHistory.stateDate",
        "state": "$contractHistory.state",
        "name": "$user.name",
        "lastname": "$user.lastname"
    }}
  ]
}
```

### Gesamt-AuM an einem Datum (nur aktive Depots)
```json
{
  "collection": "userdailydata",
  "pipeline": [
    { "$match": { "date": 20250110, "accountClosed": false } },
    { "$group": { "_id": null, "totalAuM": { "$sum": "$currentValue" }, "depotCount": { "$sum": 1 } } },
    { "$project": { "_id": 0, "totalAuM": 1, "depotCount": 1 } }
  ]
}
```
