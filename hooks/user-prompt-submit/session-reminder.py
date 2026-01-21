#!/usr/bin/env python3
import json, sys, os, re, subprocess
from pathlib import Path
HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HOOK_DIR, '..', 'lib'))
from session_state import write_state

def get_default_owner():
    """Get default owner from config file or environment variable.
    Owner prefix is REQUIRED for Graphiti group_ids to avoid namespace collisions.
    """
    # 1. Environment variable
    owner = os.environ.get("GRAPHITI_OWNER")
    if owner: return owner
    # 2. Config file in HOME
    config_file = Path.home() / ".graphiti-owner"
    if config_file.exists():
        try:
            return config_file.read_text().strip()
        except: pass
    # 3. Fallback - should be configured!
    return None

def find_git_root(p):
    path = Path(p)
    while path != path.parent:
        if (path / ".git").exists(): return str(path)
        path = path.parent
    return None

def get_github_repo(root):
    try:
        r = subprocess.run(["git","-C",root,"remote","get-url","origin"],capture_output=True,text=True,timeout=3)
        if r.returncode != 0: return None
        url = r.stdout.strip()
        if url.startswith("git@github.com:"): return url[15:].removesuffix(".git")
        if url.startswith("https://github.com/"): return url[19:].removesuffix(".git")
    except: pass
    return None

def detect_group_id(cwd):
    if not cwd: return "main","",None
    p = Path(cwd)
    # Check for explicit config files
    for cp in [p]+list(p.parents):
        gf = cp / ".graphiti-group"
        if gf.exists():
            try:
                c = gf.read_text().strip()
                if c:
                    if ":" in c: g,n = c.split(":",1); return g.strip(),n.strip(),None
                    return c, cp.name, None
            except: pass
        cf = cp / "CLAUDE.md"
        if cf.exists():
            try:
                m = re.search(r'graphiti_group_id:\s*(\S+)', cf.read_text())
                if m: return m.group(1).strip(), cp.name, None
            except: pass
    # Try GitHub remote
    gr = find_git_root(cwd)
    if gr:
        pn = Path(gr).name
        repo = get_github_repo(gr)
        if repo:
            # Replace slash with hyphen (Owner/Repo -> Owner-Repo)
            group_id = repo.replace("/", "-")
            return group_id, pn, None
        # No GitHub remote - need default owner
        default_owner = get_default_owner()
        if default_owner:
            return f"{default_owner}-{pn.lower()}", pn, None
        # No owner configured - return warning
        return f"project-{pn.lower()}", pn, "⚠️ Kein Owner-Präfix! Erstelle ~/.graphiti-owner mit deinem GitHub-Username"
    return "main", "", None

def main():
    try: hi = json.load(sys.stdin)
    except:
        print(json.dumps({"continue": True}))
        return
    write_state("graphiti_searched", False)
    write_state("memory_saved", False)
    gid, pn, warning = detect_group_id(hi.get("cwd",""))
    # Store group_id for other hooks to use
    write_state("project_group_id", gid)
    # Explicit: Graphiti group_id
    msg = f"💡 Graphiti group_id: {gid}"
    if warning:
        msg += f" | {warning}"
    print(json.dumps({"continue": True, "systemMessage": msg}))

if __name__ == "__main__": main()
