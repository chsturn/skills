#!/usr/bin/env python3
"""Memory Curator Precheck
Erzeugt strukturierte Findings für den Curator, damit das LLM nicht nur Rohdaten sieht.
"""
import json
import subprocess
import re
from pathlib import Path

KNOWN_STATES_FILE = Path("/home/strunz/.openclaw/workspace/skills/graphrag-memory/scripts/memory-curator-known-states.yaml")


def run(cmd, timeout=20):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.returncode, r.stderr.strip()


def graph(cypher, timeout=20):
    cmd = (
        "ssh chsturn@192.168.178.100 "
        f"'docker exec falkordb redis-cli --raw GRAPH.QUERY carlo_memory \"{cypher}\"'"
    )
    out, code, err = run(cmd, timeout=timeout)
    return out, code, err


def query_rows(cypher, cols, timeout=20):
    raw, _, _ = graph(cypher, timeout=timeout)
    lines = [l for l in raw.splitlines() if l and not l.startswith("Cached") and not l.startswith("Query")]
    if len(lines) >= cols:
        lines = lines[cols:]  # skip header row(s)
    rows = []
    for i in range(0, len(lines), cols):
        chunk = lines[i:i+cols]
        if len(chunk) == cols:
            rows.append(chunk)
    return rows


def qdrant_scroll():
    cmd = """curl -s -X POST http://192.168.178.100:6333/collections/carlo_memory/points/scroll \
-H 'Content-Type: application/json' \
-d '{"limit":250,"with_payload":["graph_ref","graph_refs","source_file","type"]}'"""
    out, _, _ = run(cmd, timeout=30)
    try:
        return json.loads(out)
    except Exception:
        return {}


def parse_known_states(path: Path):
    data = {
        "service_replicas": {},
        "orphan_nodes": set(),
        "qdrant_ref_exceptions": {},
        "project_required_fields": ["status", "last_worked"],
        "todo_should_have_about": True,
        "qdrant_chunk_should_have_graph_ref": True,
    }
    if not path.exists():
        return data

    current_section = None
    current_item = None
    for raw in path.read_text().splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if re.match(r"^\s{2}[a-z_]+:", line):
            current_section = line.strip().rstrip(":")
            current_item = None
            continue
        if re.match(r"^\s{4}- ", line):
            current_item = {}
            if current_section == "orphan_nodes":
                data.setdefault("_orphan_items", []).append(current_item)
            elif current_section == "service_replicas":
                data.setdefault("_service_items", []).append(current_item)
            elif current_section == "qdrant_ref_exceptions":
                data.setdefault("_qdrant_items", []).append(current_item)
            continue
        m = re.match(r"^\s{6}([a-zA-Z0-9_]+):\s*(.+)$", line)
        if m and current_item is not None:
            key, value = m.group(1), m.group(2).strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            if value.isdigit():
                value = int(value)
            current_item[key] = value
            continue
        m = re.match(r"^\s{6}-\s+(.+)$", line)
        if m and current_section == "project_required_fields":
            data["project_required_fields"].append(m.group(1).strip())

    for item in data.pop("_service_items", []):
        if "service" in item and "expected_actual_replicas" in item:
            data["service_replicas"][item["service"]] = item["expected_actual_replicas"]
    for item in data.pop("_orphan_items", []):
        if "label" in item and "name" in item:
            data["orphan_nodes"].add((item["label"], item["name"]))
    for item in data.pop("_qdrant_items", []):
        if "source_file" in item:
            data["qdrant_ref_exceptions"][item["source_file"]] = {
                "severity": item.get("severity", "info"),
                "reason": item.get("reason", "expected")
            }
    data["project_required_fields"] = list(dict.fromkeys(data["project_required_fields"]))
    # lightweight fallback parser for qdrant_ref_exceptions
    lines = path.read_text().splitlines()
    in_qdrant = False
    current = None
    for raw in lines:
        if raw.startswith("  qdrant_ref_exceptions:"):
            in_qdrant = True
            current = None
            continue
        if in_qdrant and re.match(r"^  [a-z_]+:", raw) and not raw.startswith("  qdrant_ref_exceptions:"):
            in_qdrant = False
        if not in_qdrant:
            continue
        m = re.match(r"^    - source_file: (.+)$", raw)
        if m:
            current = m.group(1).strip()
            data["qdrant_ref_exceptions"].setdefault(current, {"severity": "info", "reason": "expected"})
            continue
        m = re.match(r"^      severity: (.+)$", raw)
        if m and current:
            data["qdrant_ref_exceptions"][current]["severity"] = m.group(1).strip()
            continue
        m = re.match(r"^      reason: (.+)$", raw)
        if m and current:
            data["qdrant_ref_exceptions"][current]["reason"] = m.group(1).strip()
            continue

    return data


def add(findings, **kwargs):
    base = {
        "type": "unknown",
        "entity": None,
        "source": "precheck",
        "severity": "info",
        "confidence": "medium",
        "known_state": False,
        "action": "inspect",
        "summary": "",
    }
    base.update(kwargs)
    findings.append(base)


def main():
    known = parse_known_states(KNOWN_STATES_FILE)
    findings = []

    # 1. Orphan nodes
    for label_raw, name, status in query_rows(
        'MATCH (n) WHERE NOT (n)--() AND NOT n:Event RETURN labels(n), coalesce(n.name, n.title, n.hostname), coalesce(n.status, "")', 3
    ):
        label = label_raw.strip("[]")
        is_known = (label, name) in known["orphan_nodes"]
        add(
            findings,
            type="orphan_node",
            entity=f"{label}:{name}",
            severity="info" if is_known else "important",
            known_state=is_known,
            action="ignore" if is_known else "link_or_classify",
            summary=f"Orphan node gefunden: {label}:{name}",
        )

    # 2. Services with 0 replicas
    for name, replicas_raw, _last_checked in query_rows(
        'MATCH (s:Service) RETURN s.name, coalesce(s.actual_replicas, -1), coalesce(s.last_checked, "")', 3
    ):
        try:
            replicas = int(replicas_raw)
        except Exception:
            continue
        if replicas == 0:
            expected = known["service_replicas"].get(name)
            is_known = expected == 0
            add(
                findings,
                type="service_zero_replicas",
                entity=f"Service:{name}",
                severity="info" if is_known else "important",
                known_state=is_known,
                action="ignore" if is_known else "inspect_replicas",
                summary=f"Service {name} hat 0 Replicas",
            )

    # 3. Project completeness
    for (name,) in query_rows('MATCH (p:Project) WHERE p.status IS NULL RETURN p.name', 1):
        add(findings, type="missing_project_status", entity=f"Project:{name}", severity="important", action="add_status", summary=f"Projekt {name} hat keinen status")

    for (name,) in query_rows('MATCH (p:Project) WHERE p.last_worked IS NULL RETURN p.name', 1):
        add(findings, type="missing_project_last_worked", entity=f"Project:{name}", severity="important", action="add_last_worked", summary=f"Projekt {name} hat kein last_worked")

    # 4. TODO completeness
    for title, status in query_rows('MATCH (t:TODO) WHERE NOT (t)-[:ABOUT]->() RETURN t.title, coalesce(t.status, "")', 2):
        sev = "info" if status == "done" else "important"
        add(findings, type="todo_without_about", entity=f"TODO:{title}", severity=sev, action="link_about", summary=f"TODO ohne ABOUT-Relation: {title}")

    # 5. Unlinked services
    for (name,) in query_rows('MATCH (s:Service) WHERE NOT (s)--() RETURN s.name', 1):
        add(findings, type="service_without_relations", entity=f"Service:{name}", severity="info", action="classify_service", summary=f"Service ohne Relationen: {name}")

    # 6. Qdrant completeness
    q = qdrant_scroll()
    points = q.get("result", {}).get("points", [])
    missing_refs = 0
    ignored_missing_refs = 0
    for p in points:
        payload = p.get("payload", {}) or {}
        if payload.get("graph_ref") or payload.get("graph_refs"):
            continue
        source_file = payload.get("source_file", "")
        exc = known["qdrant_ref_exceptions"].get(source_file)
        if exc:
            ignored_missing_refs += 1
            continue
        missing_refs += 1
    if missing_refs:
        add(findings, type="qdrant_missing_graph_refs", entity="Qdrant:carlo_memory", severity="important", action="investigate_sync", summary=f"{missing_refs} Chunks ohne graph_ref/graph_refs gefunden")
    if ignored_missing_refs:
        add(findings, type="qdrant_missing_graph_refs_known", entity="Qdrant:carlo_memory", severity="info", known_state=True, action="ignore", summary=f"{ignored_missing_refs} fehlende graph_refs aus bekannten Meta-/Legacy-Dateien ignoriert")

    counts = {k: 0 for k in ["critical", "important", "info", "noise"]}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1

    result = {
        "generated_at": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
        "counts": counts,
        "findings": findings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
