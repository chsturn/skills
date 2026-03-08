#!/usr/bin/env python3
"""Sync Markdown files → Qdrant (re-embed changed chunks)"""
import os, sys, glob, json, hashlib, requests, time

OLLAMA = "http://192.168.178.100:11434/api/embed"
QDRANT = "http://192.168.178.100:6333"
COLLECTION = "carlo_memory"
WORKSPACE = "/home/strunz/.openclaw/workspace"
MEMORY_DIR = os.path.join(WORKSPACE, "memory")
STATE_FILE = os.path.join(WORKSPACE, ".graphrag-sync-state.json")

def embed(text):
    # Keep a conservative upper bound for embedding input
    text = text.strip()
    if len(text) > 1200:
        text = text[:1200]
    r = requests.post(OLLAMA, json={"model": "mxbai-embed-large", "input": text}, timeout=30)
    data = r.json()
    if "embeddings" in data:
        return data["embeddings"][0]
    raise Exception(f"Embedding error: {data}")

def chunk_file(filepath, max_chars=450):
    with open(filepath) as f:
        content = f.read()
    sections, current = [], ""
    for line in content.split("\n"):
        if line.startswith("## ") and current.strip():
            sections.append(current.strip())
            current = line + "\n"
        else:
            current += line + "\n"
    if current.strip():
        sections.append(current.strip())
    chunks = []
    for section in sections:
        if len(section) > max_chars:
            paras = section.split("\n\n")
            buf = ""
            for p in paras:
                if len(buf) + len(p) > max_chars and buf:
                    chunks.append(buf.strip())
                    buf = p + "\n\n"
                else:
                    buf += p + "\n\n"
            if buf.strip():
                chunks.append(buf.strip())
        elif section:
            chunks.append(section)
    cleaned = []
    for c in chunks:
        c = c.strip()
        if len(c) < 20:
            continue
        # Final hard split safeguard for embedding context
        if len(c) <= 1200:
            cleaned.append(c)
        else:
            start = 0
            step = 1000
            while start < len(c):
                part = c[start:start+step].strip()
                if len(part) >= 20:
                    cleaned.append(part)
                start += step
    return cleaned

def categorize(filepath):
    if "/projects/" in filepath: return "project"
    if "/infra/" in filepath: return "infra"
    if "/daily/" in filepath: return "daily"
    if "MEMORY.md" in filepath: return "index"
    if "TOOLS.md" in filepath: return "tools"
    if "SOUL.md" in filepath: return "identity"
    if "USER.md" in filepath: return "user"
    return "other"

def load_graph_keywords():
    """Fetch active node names + aliases from FalkorDB to build keyword map dynamically."""
    import subprocess
    keywords = {}
    
    try:
        # Named nodes (Project, Service, Database, Software, etc.)
        r = subprocess.run(
            ["ssh", "chsturn@192.168.178.100",
             'docker exec falkordb redis-cli GRAPH.QUERY carlo_memory '
             '"MATCH (n) WHERE n.name IS NOT NULL AND (n.status IS NULL OR n.status <> \\"removed\\") RETURN n.name, ID(n)"'],
            capture_output=True, text=True, timeout=10
        )
        lines = [l for l in r.stdout.strip().split("\n") 
                 if l and not l.startswith("Cached") and not l.startswith("Query") 
                 and not l.startswith("n.") and not l.startswith("ID")]
        for i in range(0, len(lines)-1, 2):
            name = lines[i]
            try:
                node_id = int(lines[i+1])
            except:
                continue
            # Add name as keyword (case-insensitive match)
            keywords[name.lower()] = {"name": name, "node_id": node_id}
        
        # Server nodes (keyed by hostname + IP aliases)
        r = subprocess.run(
            ["ssh", "chsturn@192.168.178.100",
             'docker exec falkordb redis-cli GRAPH.QUERY carlo_memory '
             '"MATCH (s:Server) WHERE s.status IS NULL OR s.status <> \\"removed\\" RETURN s.hostname, s.ip, ID(s)"'],
            capture_output=True, text=True, timeout=10
        )
        lines = [l for l in r.stdout.strip().split("\n")
                 if l and not l.startswith("Cached") and not l.startswith("Query")
                 and not l.startswith("s.") and not l.startswith("ID")]
        for i in range(0, len(lines)-2, 3):
            hostname = lines[i]
            ip = lines[i+1]
            try:
                node_id = int(lines[i+2])
            except:
                continue
            entry = {"name": hostname, "node_id": node_id}
            keywords[hostname.lower()] = entry
            # Add IP suffix as alias (e.g., ".67" → main)
            if ip:
                suffix = "." + ip.split(".")[-1]
                keywords[suffix] = entry
    except Exception as e:
        print(f"  ⚠️ Graph keyword load failed: {e}, using empty map")
    
    # Static aliases for common terms that don't match node names directly
    static_aliases = {
        "sturn.org": "Wine", "dopahopper": "Dopamind", "gb10": "gx10-ee7a",
        "mongo": "MongoDB Replica Set"
    }
    for alias, name in static_aliases.items():
        if alias not in keywords:
            # Find the node_id from already loaded keywords
            target = next((v for v in keywords.values() if v["name"] == name), None)
            if target:
                keywords[alias.lower()] = target
    
    return keywords

# Global: load once at sync start
_graph_keywords = None

def graph_refs(text):
    global _graph_keywords
    if _graph_keywords is None:
        _graph_keywords = load_graph_keywords()
    
    refs = []
    ref_ids = []
    text_lower = text.lower()
    seen = set()
    
    for kw, entry in _graph_keywords.items():
        if kw in text_lower and entry["name"] not in seen:
            seen.add(entry["name"])
            refs.append(entry["name"])
            ref_ids.append(entry["node_id"])
    
    return refs, ref_ids

def file_hash(filepath):
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"files": {}, "next_id": 1}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def collect_files(specific_files=None):
    if specific_files:
        return [os.path.join(WORKSPACE, f) if not f.startswith("/") else f for f in specific_files]
    files = [os.path.join(WORKSPACE, f) for f in ["MEMORY.md", "SOUL.md", "USER.md", "TOOLS.md"]]
    files += sorted(glob.glob(f"{MEMORY_DIR}/*.md"))
    files += sorted(glob.glob(f"{MEMORY_DIR}/**/*.md", recursive=True))
    seen = set()
    unique = []
    for f in files:
        rp = os.path.realpath(f)
        if rp not in seen and os.path.exists(f):
            seen.add(rp)
            unique.append(f)
    return unique

def sync(specific_files=None, force_all=False):
    state = load_state()
    files = collect_files(specific_files)
    
    total_new, total_updated, total_skipped, errors = 0, 0, 0, 0
    
    for filepath in files:
        relpath = os.path.relpath(filepath, WORKSPACE)
        fhash = file_hash(filepath)
        
        if not force_all and relpath in state["files"] and state["files"][relpath]["hash"] == fhash:
            total_skipped += 1
            continue
        
        # Delete old points for this file
        old_ids = state["files"].get(relpath, {}).get("point_ids", [])
        if old_ids:
            requests.post(f"{QDRANT}/collections/{COLLECTION}/points/delete", json={"points": old_ids})
            total_updated += 1
            print(f"  ♻️  {relpath} — replacing {len(old_ids)} chunks")
        else:
            total_new += 1
            print(f"  ➕ {relpath} — new file")
        
        chunks = chunk_file(filepath)
        category = categorize(filepath)
        date = ""
        basename = os.path.basename(filepath)
        if basename.startswith("2026-"):
            date = basename.replace(".md", "")
        
        point_ids = []
        points = []
        
        for i, chunk in enumerate(chunks):
            refs, ref_ids = graph_refs(chunk)
            if not refs:
                # Fallback: use filename/category hints so every chunk has some structural handle
                hints = []
                rel_lower = relpath.lower()
                basename = os.path.basename(rel_lower)
                mapping = {
                    "hsv": "HSV",
                    "wine": "Wine",
                    "sentinel": "Sentinel Trader",
                    "sentinel-trader": "Sentinel Trader",
                    "trading": "Sentinel Trader",
                    "dora": "DORA Compliance",
                    "dopamind": "Dopamind",
                    "lisa": "Lisa",
                    "estably": "Estably-GraphRAG",
                    "nexus": "Estably-GraphRAG",
                    "firmen-graphrag": "Estably-GraphRAG",
                    "swarm-ha": "traefik",
                    "swarm": "traefik",
                    "ha-plan": "traefik",
                    "wiki": "wiki",
                    "ai-server": "aimonster",
                    "lm studio": "aimonster",
                    "gb10": "aimonster",
                    "gpu": "aimonster",
                    "soul.md": "Carlo",
                    "tools.md": "Carlo",
                }
                for key, target in mapping.items():
                    if key in rel_lower or key == basename:
                        hints.append(target)
                refs = list(dict.fromkeys(hints))
            try:
                embedding = embed(chunk)
            except Exception as e:
                print(f"    ERROR chunk {i}: {e}")
                errors += 1
                continue
            
            pid = state["next_id"]
            state["next_id"] += 1
            point_ids.append(pid)
            
            points.append({
                "id": pid,
                "vector": embedding,
                "payload": {
                    "text": chunk,
                    "source_file": relpath,
                    "category": category,
                    "chunk_index": i,
                    "graph_refs": refs,
                    "graph_node_ids": ref_ids,
                    "date": date,
                    "char_count": len(chunk),
                    "synced_at": time.strftime("%Y-%m-%dT%H:%M:%S")
                }
            })
            
            if len(points) >= 20:
                requests.put(f"{QDRANT}/collections/{COLLECTION}/points", json={"points": points})
                points = []
        
        if points:
            requests.put(f"{QDRANT}/collections/{COLLECTION}/points", json={"points": points})
        
        state["files"][relpath] = {"hash": fhash, "point_ids": point_ids, "chunks": len(point_ids)}
    
    save_state(state)
    
    r = requests.get(f"{QDRANT}/collections/{COLLECTION}")
    total_points = r.json()["result"]["points_count"]
    
    print(f"\n✅ Sync complete: {total_new} new, {total_updated} updated, {total_skipped} unchanged, {errors} errors")
    print(f"📊 Total points in Qdrant: {total_points}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sync memory files to Qdrant")
    parser.add_argument("--files", nargs="+", help="Specific files to sync")
    parser.add_argument("--all", action="store_true", help="Force re-sync all files")
    args = parser.parse_args()
    
    sync(specific_files=args.files, force_all=args.all)
