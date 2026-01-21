#!/usr/bin/env python3
"""Tests für Titel-Guideline Prüfung (Auffindbarkeit)"""
import sys, os, importlib.util

# Load module with hyphen in name
hook_path = os.path.join(os.path.dirname(__file__), '..', 'hooks', 'pre-tool-use', 'graphiti-guard.py')
spec = importlib.util.spec_from_file_location("graphiti_guard", hook_path)
graphiti_guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graphiti_guard)
check_title_searchability = graphiti_guard.check_title_searchability

# Format: (name, expected_warnings_count, reason)
TESTS = [
    # --- GUTE TITEL (keine Warnung) ---
    ("Wann welche Tests schreiben", 0, "Kurz, deutsch, fragend"),
    ("GraphQL vs REST Entscheidung", 0, "Kurz, klar"),
    ("Docker Port-Mapping nach Suspend", 0, "Spezifisch aber kurz"),
    ("1Password SSH Agent Setup", 0, "Tool + Kontext"),
    ("Secrets nie in Graphiti speichern", 0, "Klare Regel"),

    # --- PROBLEMATISCHE TITEL (Warnung) ---
    ("Software Testing Best Practices - Mandatory Test Requirements", 1, "Zu lang + zu technisch"),
    ("A Comprehensive Guide to Understanding Advanced React Patterns", 1, "Zu lang"),
    ("PROCEDURE: How to properly configure environment variables", 1, "PROCEDURE prefix unnötig"),
    ("Learning: I learned that tests are important for quality", 1, "Learning prefix redundant"),

    # --- GRENZFÄLLE ---
    ("React Hooks vs Class Components", 0, "OK - spezifisch genug"),
    ("Mein absolut fantastisches und wundervolles Learning über Testing", 1, "Zu lang + Füllwörter"),
]

def run_tests():
    passed = 0
    failed = 0

    print("=" * 60)
    print("Titel-Guideline Tests (Auffindbarkeit)")
    print("=" * 60)

    for name, exp_warnings, reason in TESTS:
        warnings = check_title_searchability(name)
        actual_warnings = len(warnings)

        # Test: Erwartete Anzahl Warnungen (0 = gut, >0 = problematisch)
        has_expected_warnings = (actual_warnings > 0) == (exp_warnings > 0)

        if has_expected_warnings:
            passed += 1
            status = "OK" if exp_warnings == 0 else "WARN"
            print(f"✓ [{status}] '{name[:40]}...' ({reason})")
        else:
            failed += 1
            print(f"✗ '{name[:40]}...'")
            print(f"  Erwartet: {'Warnung' if exp_warnings > 0 else 'OK'} ({reason})")
            print(f"  Ergebnis: {actual_warnings} Warnungen: {warnings}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{len(TESTS)} passed, {failed} failed")
    print("=" * 60)

    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
