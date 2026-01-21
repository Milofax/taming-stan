#!/usr/bin/env python3
import json, sys, os, hashlib, re
HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HOOK_DIR, '..', 'lib'))
from session_state import register_hook, read_state, write_state, append_to_list
from secret_patterns import detect_secret, has_keyword_with_value

# Legacy patterns kept for reference - now using format-based detection in secret_patterns.py
CRED_PATTERNS = ["password","api_key","api-key","apikey","token","secret","pin","credentials","private_key","private-key","privatekey","access_token","access-token","accesstoken","auth_token","auth-token","authtoken"]

# Technische Keywords für Versions-Pflicht (Phase 23)
TECH_KEYWORDS = [
    # Frameworks & Libraries
    "react","vue","angular","svelte","next.js","nextjs","nuxt","remix","astro",
    "django","flask","fastapi","express","nest.js","nestjs","rails","laravel",
    "spring","hibernate","pytorch","tensorflow","langchain","langgraph",
    # Languages & Runtimes
    "python","javascript","typescript","rust","go","java","kotlin","swift",
    "node.js","nodejs","deno","bun",
    # Tools & CLIs
    "npm","yarn","pnpm","pip","cargo","maven","gradle",
    "docker","kubernetes","k8s","helm","terraform","ansible","pulumi",
    "git","github","gitlab","claude","claude code","openai","anthropic",
    # Databases & Services
    "postgresql","postgres","mysql","mongodb","redis","neo4j","falkordb","graphiti",
    "aws","azure","gcp","vercel","netlify","cloudflare",
    # APIs & Protocols
    "rest","graphql","grpc","websocket","oauth","jwt",
]

# Citation check: Keywords → display_name
CITATION_TYPES = {
    "book":    (["buch","book","isbn"],                  "Book"),
    "article": (["artikel","article","journal","paper"], "Article"),
    "web":     (["http://","https://","url:"], "Website"),  # "website" removed - too many false positives
    "spec":    (["rfc ","specification"],                "Spec"),
    "song":    (["song ","track ","lied ","musikstück"], "Song"),
    "album":   (["album "],                              "Album"),
    "film":    (["film ","movie "],                      "Film"),
    "novel":   (["roman ","novel "],                     "Novel"),
    "painting": (["gemälde","painting ","bild "],        "Painting"),
    "podcast": (["podcast ","episode "],                 "Podcast"),
}
# Pattern detection for required fields
def has_title(t): return bool(re.search(r"['\"][\w\s\-:]+['\"]|titel[:\s]+\w|title[:\s]+\w", t, re.I))
def has_author(t): return bool(re.search(r"\bvon\s+[A-Z]|\bby\s+[A-Z]|\bautor[:\s]+|\bauthor[:\s]+", t, re.I))
def has_year(t): return bool(re.search(r"\b(19|20)\d{2}\b|\bjahr[:\s]+|\byear[:\s]+", t))
def has_artist(t): return bool(re.search(r"\bvon\s+[A-Z]|\bby\s+[A-Z]|\bartist[:\s]+|\bkünstler[:\s]+", t, re.I))
def has_director(t): return bool(re.search(r"\bregisseur[:\s]+|\bdirector[:\s]+|\bvon\s+[A-Z]|\bby\s+[A-Z]", t, re.I))
def has_host(t): return bool(re.search(r"\bhost[:\s]+[A-Z]|\bvon\s+[A-Z]|\bby\s+[A-Z]|\bmit\s+[A-Z]", t, re.I))
def has_url(t): return bool(re.search(r"https?://|url[:\s]+", t, re.I))
def has_accessed(t): return bool(re.search(r"\bzugriff|\baccessed|\b\d{4}-\d{2}-\d{2}|\b\d{2}\.\d{2}\.\d{4}", t, re.I))  # ISO + DE format
def has_source(t): return bool(re.search(r"\bquelle[:\s]+|\bsource[:\s]+|\barxiv|\bjournal|\bin\s+[A-Z]", t, re.I))
def has_number(t): return bool(re.search(r"rfc\s*\d+|\bnummer[:\s]+|\bnumber[:\s]+|\biso\s*\d+", t, re.I))
# Required fields per type: (check_func, display_name)
REQUIRED = {
    "book":    [(has_author,"author"),(has_title,"title"),(has_year,"year")],
    "article": [(has_author,"author"),(has_title,"title"),(has_source,"source"),(has_year,"year")],
    "web":     [(has_url,"url"),(has_accessed,"accessed")],
    "spec":    [(has_number,"number"),(has_year,"year")],
    "song":    [(has_title,"title"),(has_artist,"artist")],
    "album":   [(has_title,"title"),(has_artist,"artist"),(has_year,"year")],
    "film":    [(has_title,"title"),(has_director,"director"),(has_year,"year")],
    "novel":   [(has_title,"title"),(has_author,"author"),(has_year,"year")],
    "painting": [(has_title,"title"),(has_artist,"artist")],
    "podcast": [(has_title,"title"),(has_host,"host")],
}

def has_creds(text):
    """Format-based secret detection (instead of keyword-based).

    Detects ACTUAL secret values like:
    - AKIAIOSFODNN7EXAMPLE (AWS Key)
    - ghp_xxxx (GitHub Token)
    - sk_live_xxxx (Stripe Key)
    - -----BEGIN PRIVATE KEY-----

    Allows documentation like:
    - "1Password is a good tool"
    - "TokenService class"
    - "credentials for login"
    """
    # Check for actual secret formats first
    found, secret_type, _ = detect_secret(text)
    if found:
        return True, secret_type

    # Also check for keyword + value patterns (e.g., "password: abc123")
    has_kw, keyword = has_keyword_with_value(text)
    if has_kw:
        return True, f"Keyword '{keyword}' with value"

    return False, None
def chash(text): return hashlib.md5(text.encode()).hexdigest()[:8]
def allow(): return {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}
def deny(msg): return {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":msg}}
def allow_with_msg(msg): return {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","permissionDecisionReason":msg}}

# Version check for technical learnings
def is_technical(text):
    """Check if text contains technical content (Library, Framework, Tool)."""
    tl = text.lower()
    for kw in TECH_KEYWORDS:
        # Word boundaries to avoid false positives
        if re.search(rf'\b{re.escape(kw)}\b', tl):
            return True, kw
    return False, ""

def has_version(text):
    """Check if text contains a version indicator."""
    # v1.2.3, 1.2.3, v2, 2.0
    if re.search(r'\bv?\d+\.\d+(\.\d+)?', text, re.I): return True
    # >=2.0, ^3.0, ~1.2
    if re.search(r'[>=<^~]\d+\.\d+', text): return True
    # "version 2", "Version: 3"
    if re.search(r'\bversion[:\s]+\d+', text, re.I): return True
    # "ab v2", "seit v3", "from v2"
    if re.search(r'\b(ab|seit|from|since)\s+v?\d+', text, re.I): return True
    # Tool name followed by number: "React 18", "Python 3", "ES6"
    if re.search(r'\b[A-Za-z]+\s+\d+[:\s]', text): return True
    # Year in parentheses: "(2024)", "(2026)"
    if re.search(r'\(20\d{2}\)', text): return True
    return False

def check_citation(body, source_desc=""):
    """Check if body contains citable content and if required fields are present.
    Checks both body AND source_description for required fields (URLs often in source_desc)."""
    bl = body.lower()
    combined = body + " " + source_desc  # Combine both for required field checks
    # Bible verse pattern (e.g., "John 3:16")
    if re.search(r'\b[A-Za-zäöüÄÖÜ]+\s+\d+:\d+', body):
        return True, "Bible verse", []
    for typ, (keywords, display) in CITATION_TYPES.items():
        if any(kw in bl for kw in keywords):
            missing = [name for check, name in REQUIRED.get(typ, []) if not check(combined)]
            return True, display, missing
    return False, "", []

# Title searchability check
REDUNDANT_PREFIXES = ["procedure:", "learning:", "concept:", "decision:", "requirement:"]
FILLER_WORDS = ["comprehensive", "guide", "understanding", "advanced", "properly", "best practices",
                "fantastisch", "wundervoll", "absolut", "eigentlich", "basically"]

def check_title_searchability(name):
    """Check if title is search-friendly. Returns list of warnings."""
    warnings = []
    nl = name.lower()

    # Too long (> 60 chars)
    if len(name) > 60:
        warnings.append(f"Title too long ({len(name)} chars). Recommended: <60")

    # Redundant prefixes (Entity-Type is auto-detected)
    for prefix in REDUNDANT_PREFIXES:
        if nl.startswith(prefix):
            warnings.append(f"Prefix '{prefix.upper()}' unnecessary - Entity-Type is auto-detected")
            break

    # Filler words
    for filler in FILLER_WORDS:
        if filler in nl:
            warnings.append(f"Filler word '{filler}' makes title longer without value")
            break

    return warnings

def main():
    try: hook_input = json.load(sys.stdin)
    except: print(json.dumps(allow())); return
    register_hook("graphiti")
    tool_name = hook_input.get("tool_name","")
    tool_input = hook_input.get("tool_input",{})
    if tool_name != "mcp__mcp-funnel__bridge_tool_request":
        print(json.dumps(allow())); return
    bridge_tool = tool_input.get("tool","")
    if "graphiti" not in bridge_tool.lower():
        print(json.dumps(allow())); return
    args = tool_input.get("arguments",{})

    if "add_memory" in bridge_tool.lower():
        src = args.get("source_description","")
        if not src or not src.strip():
            print(json.dumps(deny("💡 source_description missing. Where does this come from?\n→User statement|Research[URL]|Own experience")))
            return
        body = args.get("episode_body","")
        creds_found, creds_type = has_creds(body)
        if creds_found:
            print(json.dumps(deny(f"⚠️ Secret detected: {creds_type}\n→Secrets belong in 1Password|Secrets Manager|Env Vars")))
            return
        # Citation check (body + source_description for required fields)
        is_citable, ctype, missing = check_citation(body, src)
        if is_citable and missing:
            print(json.dumps(deny(f"💡 {ctype} detected. For citation, missing: {', '.join(missing)}\n→Research|Ask user")))
            return

        # Title searchability check (Soft Warning)
        name = args.get("name","")
        title_warnings = check_title_searchability(name)
        if title_warnings:
            state = read_state()
            title_hash = hashlib.md5(name.encode()).hexdigest()[:8]
            title_warning_state = state.get("title_warning_shown", {})
            if title_warning_state.get("hash") != title_hash:
                write_state("title_warning_shown", {"hash": title_hash})
                warn_text = "\n".join(f"• {w}" for w in title_warnings)
                print(json.dumps(deny(f"💡 Title could be more searchable:\n{warn_text}\n→Shorten title|Repeat to skip")))
                return

        # group_id selection (before other checks)
        gid = args.get("group_id","")
        eff_gid = gid.strip() if gid else "main"
        curr_hash = chash(body)
        state = read_state()
        active_gids = state.get("active_group_ids", [])
        proj_gid = state.get("project_group_id", "")

        # If agent explicitly set a project-specific group_id (not main) → allow without asking
        # Only ask when: no group_id set OR group_id is "main" (needs confirmation)
        explicit_project_gid = gid and gid.strip() and gid.strip() != "main"

        if not explicit_project_gid:
            # No explicit project group_id → need to confirm where to save
            # Check if group_id decision was already made
            gid_decision = state.get("group_id_decision", {})
            gid_decision_made = (gid_decision.get("name") == name and
                                gid_decision.get("content_hash") == curr_hash and
                                gid_decision.get("group_id") == eff_gid)

            if not gid_decision_made:
                # Build options list
                options = list(set(active_gids))  # Unique
                if "main" not in options:
                    options.append("main")

                # Format question based on number of options
                if len(options) == 1 and options[0] == "main":
                    msg = f"💡 No project context. Save to 'main' (permanent)?\n→yes: Repeat with group_id='main'"
                elif len(options) == 2 and "main" in options:
                    proj = [o for o in options if o != "main"][0]
                    msg = f"💡 Where to save?\n• {proj} (project-specific)\n• main (permanent)\n→Set group_id, repeat"
                else:
                    opts_str = "|".join(options)
                    msg = f"💡 Multiple contexts active: {opts_str}\n→Set group_id, repeat"

                # Store decision for repeat
                write_state("group_id_decision", {"name": name, "content_hash": curr_hash, "group_id": eff_gid})
                print(json.dumps(deny(msg)))
                return

        # Explicit project group_id set OR decision was made (repeat) - continue with other checks

        tech_found, tech_kw = is_technical(body)
        version_confirmed = False
        if tech_found and not has_version(body):
            version_pending = state.get("version_pending",{})
            if not (version_pending.get("name") == name and version_pending.get("content_hash") == curr_hash):
                write_state("version_pending",{"name":name,"content_hash":curr_hash})
                print(json.dumps(deny(f"❤️ '{tech_kw}' without version. Recommended: '{tech_kw} v1.2.3: ...'\n→Add version|Repeat to skip")))
                return
            version_confirmed = True  # Cleared at the end

        if eff_gid == "main":
            pending = state.get("main_pending",{})
            if pending.get("name") == name:
                write_state("main_pending",{})
                write_state("group_id_decision",{})  # Clear decision
                if version_confirmed: write_state("version_pending",{})
                write_state("memory_saved",True)
                msg = "Content unchanged - abstraction recommended!" if pending.get("content_hash") == curr_hash else ""
                print(json.dumps(allow_with_msg(msg) if msg else allow()))
                return
            write_state("main_pending",{"name":name,"content_hash":curr_hash})
            print(json.dumps(deny(f"💡 'main' = permanent. Is this correct?\n1. Transferable? 2. Abstracted? 3. Relevant in 5 years?\n→NO=project-specific|YES=repeat with name='{name}'")))
            return
        # Non-main save: clear all pending states
        write_state("group_id_decision",{})  # Clear decision
        if version_confirmed: write_state("version_pending",{})
        write_state("memory_saved",True)
        print(json.dumps(allow())); return

    if "clear_graph" in bridge_tool.lower():
        if not read_state().get("graphiti_review_done",False):
            print(json.dumps(deny("💡 Before clear_graph: Promote valuable content?\n→search_nodes(entity_types=['Learning','Decision','Concept'])\n→Promote to 'main'→THEN delete")))
            return
        print(json.dumps(allow())); return

    if "search_nodes" in bridge_tool.lower():
        et = str(args.get("entity_types",[])).lower()
        if "learning" in et or "decision" in et or "concept" in et:
            write_state("graphiti_review_done",True)
        write_state("graphiti_searched",True)
        gids = args.get("group_ids", [])
        state = read_state()

        # All active_group_ids MUST be searched
        active_gids = state.get("active_group_ids", [])
        required_gids = set(active_gids + ["main"])  # main is always included

        if gids:
            provided_gids = set(gids)
            missing = required_gids - provided_gids
            if missing:
                all_required = '", "'.join(sorted(required_gids))
                missing_str = ", ".join(sorted(missing))
                print(json.dumps(deny(f"💡 Not all contexts searched. Missing: {missing_str}\n→group_ids=[\"{all_required}\"]")))
                return
        else:
            # No group_ids provided - all required
            all_required = '", "'.join(sorted(required_gids))
            print(json.dumps(deny(f"💡 group_ids missing.\n→group_ids=[\"{all_required}\"]")))
            return
        print(json.dumps(allow())); return

    print(json.dumps(allow()))

if __name__ == "__main__": main()
