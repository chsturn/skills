#!/usr/bin/env python3
"""Builds a short, grouped report from memory-curator-precheck JSON."""
import json
import sys
from collections import defaultdict

SEVERITY_ORDER = {"critical": 0, "important": 1, "info": 2, "noise": 3}


def entity_group(entity: str) -> str:
    if not entity:
        return "Allgemein"
    if ":" in entity:
        kind, rest = entity.split(":", 1)
        if kind in {"Project", "Service", "Server", "TODO", "Qdrant"}:
            return rest.strip() or kind
    return entity


def load_input():
    if len(sys.argv) > 1 and sys.argv[1] != "-":
        with open(sys.argv[1]) as f:
            return json.load(f)
    return json.load(sys.stdin)


def main():
    data = load_input()
    findings = data.get("findings", [])
    findings = [f for f in findings if f.get("severity") != "noise"]
    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f.get("severity"), 9), f.get("entity") or ""))

    important = [f for f in findings if f.get("severity") in {"critical", "important"}]
    infos = [f for f in findings if f.get("severity") == "info"]

    if not important and not infos:
        print("Memory-Audit clean ✅")
        return

    grouped = defaultdict(list)
    for f in important:
        grouped[entity_group(f.get("entity"))].append(f)

    lines = []
    highlights = 0
    if important:
        lines.append("Wichtigste Findings:")
        for group, items in sorted(grouped.items(), key=lambda kv: SEVERITY_ORDER.get(kv[1][0].get("severity"), 9)):
            if highlights >= 5:
                break
            if len(items) == 1:
                lines.append(f"- {items[0].get('summary')}")
            else:
                summaries = ", ".join(sorted(set(i.get("type", "finding") for i in items)))
                lines.append(f"- {group}: {len(items)} Themen ({summaries})")
            highlights += 1

    if infos:
        if lines:
            lines.append("")
        lines.append("Housekeeping:")
        for f in infos[:3]:
            lines.append(f"- {f.get('summary')}")

    crit = len([f for f in findings if f.get("severity") == "critical"])
    imp = len([f for f in findings if f.get("severity") == "important"])
    info = len([f for f in findings if f.get("severity") == "info"])
    if lines:
        lines.append("")
    if crit == 0 and imp == 0 and info > 0:
        lines.append(f"Kurzfazit: Insgesamt ruhig, nur {info} bekannte Info-Hinweise.")
    else:
        lines.append(f"Kurzfazit: {crit} kritisch, {imp} wichtig, {info} info.")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
