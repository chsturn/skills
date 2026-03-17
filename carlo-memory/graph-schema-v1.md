# carlo_memory Graph Schema v1

_Definiert am 2026-03-17. Gilt als verbindliches Schema für alle Schreib-Operationen._

---

## Kern-Labels (aktiv nutzen)

### Person
Pflicht: `name`
Optional: `telegram_id`, `email`, `timezone`, `language`

### Agent
Pflicht: `name`, `type`
Optional: `born`, `model_default`, `model_heartbeat`

### Server
Pflicht: `hostname`, `ip`, `ssh_user`, `role`
Optional: `cpu`, `ram_gb`, `disk_gb`, `disk_tb`, `gpu`, `vram_gb`, `cuda`, `engine`, `always_on`, `os`, `models`, `available_for`

### Cluster
Pflicht: `name`
Optional: `quorum`, `manager_count`, `worker_count`

### Project
Pflicht: `name`, `status`
Optional: `domain`, `repo`, `tech`, `description`, `last_worked`, `last_update`, `access`, `local_path`, `public`, `github_url`
Status-Werte: `active`, `in_progress`, `paused`, `done`, `archived`, `unknown`

### Service
Pflicht: `name`
Optional: `replicas`, `image`, `type`, `port`, `swarm_name`, `actual_replicas`, `last_checked`, `standalone`, `pinned_to`

### Database
Pflicht: `name`, `type`
Optional: `replica_set`, `tls` + beliebige Collection-Counts (z.B. `users`, `wines`)

### Software
Pflicht: `name`, `installed`
Optional: `latest`, `latest_checked`, `version`, `last_updated`

### Todo
Pflicht: `title`, `done`
Optional: `priority`, `context`, `project`, `created_date`, `completed_date`
Priority-Werte: `high`, `medium`, `low`

### Decision
Pflicht: `what`, `reason`, `date`
Optional: `decided_by`, `context`

### Correction
Pflicht: `what_was_wrong`, `correct_answer`, `date`
Optional: `context`, `acknowledged`

### Preference
Pflicht: `key`, `value`
Optional: `details`, `date`, `scope`

### Conversation
Pflicht: `date`, `summary`
Optional: `start`, `end`

### Topic
Pflicht: `name`, `date`
Optional: `time`, `details`

### Event
Pflicht: `name`, `date`, `type`
Optional: `details`, `severity`

### CronJob
Pflicht: `name`, `schedule`
Optional: `id`, `target`, `model`, `delivery`, `task`, `script`, `status`, `disabled_date`, `disabled_reason`

### WeeklyReview
Pflicht: `date`, `summary`
Optional: `corrections_count`, `patterns_found`, `stale_entries`

---

## Beziehungstypen (erlaubt)

### Struktur
| Beziehung | Von | Nach | Bedeutung |
|---|---|---|---|
| `RUNS_ON` | Service | Server | Service läuft auf Server |
| `HAS_SERVICE` | Project | Service | Projekt hat diesen Service |
| `USES_DB` | Service | Database | Service nutzt diese DB |
| `PART_OF` | Server | Cluster | Server gehört zum Cluster |
| `MEMBER_OF` | Database | Database | DB ist Teil eines Replica Sets |

### Ownership / Verantwortung
| Beziehung | Von | Nach | Bedeutung |
|---|---|---|---|
| `OWNS` | Person | Project | Person besitzt Projekt |
| `RUNS_JOB` | Agent | CronJob | Agent führt Cron-Job aus |
| `USES` | CronJob | Service | Cron-Job nutzt diesen Service |

### Conversations / Wissen
| Beziehung | Von | Nach | Bedeutung |
|---|---|---|---|
| `DISCUSSED` | Conversation | Topic | In dieser Conversation besprochen |
| `ABOUT` | Topic | Project/Service/Server | Topic handelt von dieser Entity |
| `LED_TO` | Topic | Event/CronJob/Decision | Topic führte zu diesem Ergebnis |
| `PARTICIPATED` | Person/Agent | Conversation | Hat an Conversation teilgenommen |
| `DECIDED_BY` | Decision | Person | Entscheidung von dieser Person |

### Software / Tools
| Beziehung | Von | Nach | Bedeutung |
|---|---|---|---|
| `DEPENDS_ON` | Service | Software | Service hängt von Software ab |

---

## Deprecated Labels (nicht mehr neu anlegen!)

Diese Labels existieren noch im Graph, sollen aber **nicht mehr für neue Nodes** verwendet werden:

| Label | Grund | Migration |
|---|---|---|
| `System` | → `Software` verwenden | mergen |
| `TODO` | → `Todo` verwenden (Groß/Klein) | mergen |
| `Task` | → `Todo` verwenden | mergen |
| `Config` | Properties direkt am Server/Service Node | löschen |
| `TempTest` | Testdaten | löschen |
| `Rule` | zu generisch, war DORA-Import | in estably_graphrag verschieben |
| `StandardSection` | DORA-Import | in estably_graphrag verschieben |
| `StandardSet` | DORA-Import | in estably_graphrag verschieben |
| `PracticeArea` | DORA-Import | in estably_graphrag verschieben |
| `Language` | zu generisch | prüfen ob nötig |
| `Framework` | zu generisch | prüfen ob nötig |
| `DeploymentPattern` | DORA-Import | in estably_graphrag verschieben |
| `InfrastructurePattern` | DORA-Import | in estably_graphrag verschieben |
| `Device` | → Properties am Server | mergen |
| `Plan` | → Todo oder Project | mergen |
| `Milestone` | → Event mit type="milestone" | mergen |
| `ConversationMemory` | alt, ersetzt durch Conversation+Topic | löschen |

---

## Deprecated Beziehungstypen (nicht mehr neu anlegen!)

| Beziehung | Grund | Ersatz |
|---|---|---|
| `CONTAINS` | zu generisch | spezifischere Beziehung verwenden |
| `APPLIES_TO` | DORA-Import | nur in estably_graphrag |
| `HAS_TOPIC` | → `DISCUSSED` verwenden | mergen |
| `USES_PATTERN` | DORA-Import | nur in estably_graphrag |
| `BELONGS_TO` | zu generisch | `PART_OF` oder `MEMBER_OF` |
| `DEPLOYS` | → `RUNS_ON` | mergen |
| `DESCRIBED_BY` | → `ABOUT` | mergen |
| `PREFERS` | → `Preference` Node | mergen |
| `RELATED_TO` | zu generisch | spezifischere Beziehung |
| `SHOULD_USE_PATTERN` | DORA-Import | nur in estably_graphrag |
| `USES_DEVICE` | → Properties am Server | entfernen |
| `VERIFIED_BY` | DORA-Import | nur in estably_graphrag |
| `REACHED` | unklar | prüfen |
| `INCLUDES` | zu generisch | spezifischere Beziehung |

---

## Regeln

1. **Neue Nodes nur mit Kern-Labels anlegen** — keine neuen Labels erfinden ohne Schema-Update
2. **Pflichtfelder immer setzen** — sonst lehnt der Curator den Node ab
3. **Soft-Delete statt Hard-Delete** — `status: "removed"`, `removed_date`
4. **Estably-Daten gehören in `estably_graphrag`** — nie in `carlo_memory`
5. **Deprecated Labels** werden vom Curator schrittweise migriert
