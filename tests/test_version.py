#!/usr/bin/env python3
"""Automatisierte Tests für Versions-Prüfung bei technischen Learnings (Phase 23)"""
import sys, os, importlib.util

# Load module with hyphen in name
hook_path = os.path.join(os.path.dirname(__file__), '..', 'hooks', 'pre-tool-use', 'graphiti-guard.py')
spec = importlib.util.spec_from_file_location("graphiti_guard", hook_path)
graphiti_guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graphiti_guard)
is_technical = graphiti_guard.is_technical
has_version = graphiti_guard.has_version
TECH_KEYWORDS = graphiti_guard.TECH_KEYWORDS

# Tests für is_technical()
TECH_TESTS = [
    # (text, expected_is_technical, expected_keyword_contains)
    ("React Hooks sind besser als Class Components", True, "react"),
    ("Claude Code v2.1.12: hookEventName ist Pflicht", True, "claude"),
    ("Python 3.11 hat match/case", True, "python"),
    ("Docker Compose funktioniert gut", True, "docker"),
    ("npm install ist schnell", True, "npm"),
    ("GraphQL ist für kleine Teams overkill", True, "graphql"),
    ("Kubernetes Pods neu starten", True, "kubernetes"),
    ("REST API Design Patterns", True, "rest"),
    ("Ich mag Kaffee", False, ""),
    ("Das Meeting war produktiv", False, ""),
    ("Mein Hund heißt Max", False, ""),
    ("Die Sonne scheint heute", False, ""),
]

# Tests für has_version()
VERSION_TESTS = [
    # (text, expected_has_version)
    # Semantic versions
    ("v1.2.3 ist stabil", True),
    ("Version 2.0 hat Breaking Changes", True),
    ("ab v3.0 funktioniert es", True),
    ("seit v2.1 deprecated", True),
    ("from v4 onwards", True),
    ("React 18 ist stabil", True),
    ("Python 3.11+ hat match/case", True),
    (">=2.0 required", True),
    ("^3.0.0 kompatibel", True),
    ("~1.2 minor updates", True),
    # Jahre als Version
    ("(2026) Format", True),
    ("seit 2024", True),
    # Keine Version
    ("Das funktioniert gut", False),
    ("Hooks sind besser", False),
    ("API Design", False),
]

# Kombinierte Tests (is_technical + has_version → sollte warnen oder nicht)
COMBINED_TESTS = [
    # (text, should_warn) - warn = technisch ABER keine Version
    ("React Hooks sind besser als Class Components", True),  # tech, no version → WARN
    ("React 18: Hooks sind besser als Class Components", False),  # tech, has version → OK
    ("Claude Code v2.1.12: hookEventName ist Pflicht", False),  # tech, has version → OK
    ("hookEventName ist Pflicht", False),  # no tech → OK (no warning)
    ("Ich mag Kaffee", False),  # no tech → OK
    ("Docker Compose funktioniert gut", True),  # tech, no version → WARN
    ("Docker Compose v2.20: funktioniert gut", False),  # tech, has version → OK
    ("Python match/case ist performant", True),  # tech, no version → WARN
    ("Python 3.11: match/case ist performant", False),  # tech, has version → OK
]

def run_tests():
    passed = 0
    failed = 0

    print("=" * 60)
    print("Versions-Prüfung Tests (Phase 23)")
    print("=" * 60)

    # Test is_technical()
    print("\n--- is_technical() Tests ---")
    for text, exp_tech, exp_kw in TECH_TESTS:
        is_tech, found_kw = is_technical(text)
        ok = (is_tech == exp_tech) and (not exp_tech or exp_kw in found_kw.lower())
        if ok:
            passed += 1
            print(f"✓ '{text[:35]}...' → tech={is_tech}")
        else:
            failed += 1
            print(f"✗ '{text[:35]}...'")
            print(f"  Expected: tech={exp_tech}, kw contains '{exp_kw}'")
            print(f"  Got:      tech={is_tech}, kw='{found_kw}'")

    # Test has_version()
    print("\n--- has_version() Tests ---")
    for text, exp_has in VERSION_TESTS:
        has_ver = has_version(text)
        if has_ver == exp_has:
            passed += 1
            print(f"✓ '{text[:35]}...' → version={has_ver}")
        else:
            failed += 1
            print(f"✗ '{text[:35]}...'")
            print(f"  Expected: version={exp_has}")
            print(f"  Got:      version={has_ver}")

    # Test combined logic
    print("\n--- Kombinierte Tests (sollte warnen?) ---")
    for text, exp_warn in COMBINED_TESTS:
        is_tech, _ = is_technical(text)
        has_ver = has_version(text)
        should_warn = is_tech and not has_ver
        if should_warn == exp_warn:
            passed += 1
            print(f"✓ '{text[:35]}...' → warn={should_warn}")
        else:
            failed += 1
            print(f"✗ '{text[:35]}...'")
            print(f"  Expected: warn={exp_warn}")
            print(f"  Got:      warn={should_warn} (tech={is_tech}, ver={has_ver})")

    print("\n" + "=" * 60)
    total = len(TECH_TESTS) + len(VERSION_TESTS) + len(COMBINED_TESTS)
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print("=" * 60)

    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
