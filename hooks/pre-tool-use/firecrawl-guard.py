#!/usr/bin/env python3
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from session_state import register_hook, is_hook_active, read_state, write_state

# Libraries/frameworks that Context7 likely has docs for
LIBS = [
    # Frontend frameworks
    "react","vue","angular","svelte","next","nuxt","remix","astro","solid","qwik","htmx",
    # Backend frameworks
    "express","fastapi","django","flask","rails","hono","elysia","fastify","nestjs","spring","laravel",
    # Runtimes
    "typescript","node","deno","bun","python","go","rust",
    # AI/ML
    "langchain","llamaindex","openai","anthropic","huggingface","cohere","replicate","groq","mistral","gemini","claude",
    # Databases & ORMs
    "prisma","drizzle","sequelize","mongoose","supabase","firebase","redis","postgres","mysql","sqlite","mongodb",
    # CSS/UI
    "tailwind","bootstrap","material-ui","chakra","shadcn","radix",
    # Testing
    "pytest","jest","vitest","playwright","cypress","mocha",
    # DevOps
    "docker","kubernetes","terraform","ansible","github","gitlab","vercel","netlify","cloudflare","aws","azure","gcp",
    # Build tools
    "vite","webpack","rollup","esbuild","turbo","npm","yarn","pnpm",
    # Auth
    "auth0","clerk","lucia","better-auth",
    # State management
    "zustand","jotai","redux","mobx","pinia",
    # Mobile/Desktop
    "react-native","expo","flutter","tauri","electron",
    # CMS
    "strapi","payload","sanity","contentful",
    # API
    "graphql","trpc","rest","grpc","swagger","openapi"
]
DOC_TERMS = ["docs","documentation","api","guide","tutorial","how to","example"]

def allow(): return {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}
def deny(msg): return {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":msg}}

def graphiti_check_required():
    """Check if Graphiti search is required before external research."""
    state = read_state()
    # Only enforce if Graphiti is installed (graphiti_available=True)
    if not state.get("graphiti_available"): return False
    # Block if not searched yet
    return not state.get("graphiti_searched", False)

def is_lib_search(q):
    ql = q.lower()
    for lib in LIBS:
        if lib in ql and any(t in ql for t in DOC_TERMS): return True, lib
    return False, ""

def main():
    try: hi = json.load(sys.stdin)
    except: print(json.dumps(allow())); return
    register_hook("firecrawl")
    tn, ti = hi.get("tool_name",""), hi.get("tool_input",{})

    # WebSearch/WebFetch: Check Graphiti first, then Firecrawl
    if tn in ["WebSearch","WebFetch"]:
        if graphiti_check_required():
            print(json.dumps(deny("💡 Was weißt du schon dank Graphiti?\n→search_nodes(query)")))
            return
        if not read_state().get("firecrawl_attempted",False):
            print(json.dumps(deny("💡 Firecrawl > WebSearch (strukturierte Daten)\n→discover_tools_by_words('firecrawl',enable=true)")))
            return
        print(json.dumps(allow())); return

    # Firecrawl via bridge: Check Graphiti first, then Context7
    if tn == "mcp__mcp-funnel__bridge_tool_request":
        bt = ti.get("tool","")
        if "firecrawl" in bt.lower():
            if graphiti_check_required():
                print(json.dumps(deny("💡 Was weißt du schon dank Graphiti?\n→search_nodes(query)")))
                return
            write_state("firecrawl_attempted",True)
            if is_hook_active("context7"):
                args = ti.get("arguments",{})
                q = args.get("query","") or args.get("url","")
                is_lib, lib = is_lib_search(q)
                if is_lib and lib not in read_state().get("context7_attempted_for",[]):
                    print(json.dumps(deny(f"💡 Context7 hat Docs für '{lib}'\n→context7__resolve_library_id(libraryName='{lib}')")))
                    return
            print(json.dumps(allow())); return
    print(json.dumps(allow()))

if __name__ == "__main__": main()
