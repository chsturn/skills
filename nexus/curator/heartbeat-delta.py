#!/usr/bin/env python3
"""Heartbeat Delta Check — vergleicht Live-State mit Known State im Graph.
Gibt nur Änderungen/Probleme aus. Exit 0 = alles wie bekannt, Exit 1 = Deltas gefunden."""
import subprocess, json, sys, re

def run(cmd, timeout=15):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()

def graph(cypher):
    r = subprocess.run(
        ["ssh", "chsturn@192.168.178.100",
         f'docker exec falkordb redis-cli GRAPH.QUERY carlo_memory "{cypher}"'],
        capture_output=True, text=True, timeout=10
    )
    return r.stdout.strip()

def graph_set(cypher):
    """Execute a SET/UPDATE query"""
    graph(cypher)

deltas = []

# --- 1. OpenClaw Version ---
npm_out = run("npm view openclaw dist-tags --json 2>/dev/null")
try:
    tags = json.loads(npm_out)
    npm_latest = tags.get("latest", "unknown")
except:
    npm_latest = "unknown"

known = graph('MATCH (s:Software {name:\\"OpenClaw\\"}) RETURN s.installed, s.latest')
lines = [l for l in known.split("\n") if l and not l.startswith("Cached") and not l.startswith("Query") and not l.startswith("s.")]
installed = lines[0] if len(lines) > 0 else "unknown"
prev_latest = lines[1] if len(lines) > 1 else "unknown"

if npm_latest != "unknown" and npm_latest != installed:
    deltas.append(f"🆕 **OpenClaw Update verfügbar:** {installed} → {npm_latest}")
    graph_set(f'MATCH (s:Software {{name:\\"OpenClaw\\"}}) SET s.latest = \\"{npm_latest}\\", s.latest_checked = \\"{__import__("time").strftime("%Y-%m-%d")}\\"')
elif npm_latest != "unknown":
    graph_set(f'MATCH (s:Software {{name:\\"OpenClaw\\"}}) SET s.latest_checked = \\"{__import__("time").strftime("%Y-%m-%d")}\\"')

# --- 2. Swarm Nodes ---
node_out = run('ssh chsturn@192.168.178.67 "docker node ls --format \'{{.Hostname}}|{{.Status}}|{{.Availability}}|{{.ManagerStatus}}\'"')
for line in node_out.split("\n"):
    if not line.strip():
        continue
    parts = line.split("|")
    if len(parts) < 4:
        continue
    hostname, status, avail, mgr_status = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
    if status != "Ready":
        deltas.append(f"🔴 **{hostname}** Status: {status} (erwartet: Ready)")
    if avail != "Active":
        deltas.append(f"⚠️ **{hostname}** Availability: {avail}")
    # Check leader change
    if mgr_status == "Leader":
        known_leader = graph(f'MATCH (s:Server)-[r:MEMBER_OF {{status:\\"Leader\\"}}]->(c:Cluster) RETURN s.hostname')
        known_lines = [l for l in known_leader.split("\n") if l and not l.startswith("Cached") and not l.startswith("Query") and not l.startswith("s.")]
        if known_lines and known_lines[0] != hostname:
            deltas.append(f"👑 **Leader gewechselt:** {known_lines[0]} → {hostname}")
            graph_set(f'MATCH (s:Server)-[r:MEMBER_OF]->(c:Cluster) WHERE r.status = \\"Leader\\" SET r.status = \\"Reachable\\"')
            graph_set(f'MATCH (s:Server {{hostname:\\"{hostname}\\"}})-[r:MEMBER_OF]->(c:Cluster) SET r.status = \\"Leader\\"')

# --- 3. Service Replica Deltas ---
svc_out = run('ssh chsturn@192.168.178.67 "docker service ls --format \'{{.Name}}|{{.Replicas}}\'"')
for line in svc_out.split("\n"):
    if not line.strip():
        continue
    parts = line.split("|")
    if len(parts) < 2:
        continue
    svc_name = parts[0].strip()
    replicas_str = parts[1].strip()
    
    # Parse "1/2" format
    match = re.match(r"(\d+)/(\d+)", replicas_str)
    if not match:
        continue
    actual, desired = int(match.group(1)), int(match.group(2))
    
    # Match by swarm_name property in graph
    known_raw = graph(f'MATCH (s:Service {{swarm_name:\\"{svc_name}\\"}}) RETURN s.name, s.actual_replicas')
    known_lines = [l for l in known_raw.split("\n") if l and not l.startswith("Cached") and not l.startswith("Query") and not l.startswith("s.")]
    
    if len(known_lines) < 2:
        continue
    
    graph_name = known_lines[0]
    try:
        known_actual = int(known_lines[1])
    except:
        continue
    
    if actual != known_actual:
        if actual < known_actual:
            deltas.append(f"⚠️ **{graph_name}** Replicas: {known_actual} → {actual}/{desired}")
        elif actual > known_actual and known_actual == 0:
            deltas.append(f"✅ **{graph_name}** wieder online: {actual}/{desired}")
        else:
            deltas.append(f"📊 **{graph_name}** Replicas geändert: {known_actual} → {actual}/{desired}")
        
        graph_set(f'MATCH (s:Service {{name:\\"{graph_name}\\"}}) SET s.actual_replicas = {actual}, s.last_checked = \\"{__import__("time").strftime("%Y-%m-%d")}\\"')

# --- 4. Disk & Memory (nur bei Problemen) ---
disk_out = run('ssh chsturn@192.168.178.67 "df -h / --output=pcent | tail -1"')
try:
    disk_pct = int(disk_out.strip().replace("%", ""))
    if disk_pct > 80:
        deltas.append(f"💾 **Disk main:** {disk_pct}% belegt!")
except:
    pass

mem_out = run('ssh chsturn@192.168.178.67 "free | grep Mem | awk \'{printf \\"%.0f\\", \\$3/\\$2*100}\'"')
try:
    mem_pct = int(mem_out.strip())
    if mem_pct > 85:
        deltas.append(f"🧠 **RAM main:** {mem_pct}% belegt!")
except:
    pass

# --- 5. Fail2ban (nur bei Bans) ---
f2b_out = run('ssh chsturn@192.168.178.67 "docker exec $(docker ps -q -f name=shared-services_prometheus) wget -qO- \'http://localhost:9090/api/v1/query?query=f2b_jail_banned_current\' 2>/dev/null"')
try:
    f2b_data = json.loads(f2b_out)
    for r in f2b_data.get("data", {}).get("result", []):
        jail = r["metric"]["jail"]
        banned = int(r["value"][1])
        if banned > 0:
            deltas.append(f"🚫 **Fail2ban {jail}:** {banned} IPs gebannt")
except:
    pass

# --- Output ---
if deltas:
    print("DELTAS_FOUND")
    for d in deltas:
        print(d)
    sys.exit(1)
else:
    print("NO_CHANGES")
    sys.exit(0)
