#!/usr/bin/env python3
"""Automatisierte Tests für Zitierfähigkeits-Prüfung (Phase 19)"""
import sys, os, importlib.util

# Load module with hyphen in name
hook_path = os.path.join(os.path.dirname(__file__), '..', 'hooks', 'pre-tool-use', 'graphiti-guard.py')
spec = importlib.util.spec_from_file_location("graphiti_guard", hook_path)
graphiti_guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graphiti_guard)
check_citation = graphiti_guard.check_citation
CITATION_TYPES = graphiti_guard.CITATION_TYPES

TESTS = [
    # (body, expected_citable, expected_type, should_have_missing)
    # --- BÜCHER ---
    ("Buch 'Atomic Habits' ist super", True, "Buch", True),
    ("Buch 'Atomic Habits' von James Clear", True, "Buch", True),  # Jahr fehlt
    ("Buch 'Atomic Habits' von James Clear (2018)", True, "Buch", False),
    ("Book 'Clean Code' by Robert Martin (2008)", True, "Buch", False),
    ("ISBN 978-3-12345-678-9 'Atomic Habits' von James Clear 2018", True, "Buch", False),

    # --- ARTIKEL ---
    ("Artikel 'XYZ' ist interessant", True, "Artikel", True),
    ("Paper 'Attention Is All You Need' by Vaswani 2017 arxiv", True, "Artikel", False),

    # --- WEB ---
    ("https://example.com ist eine gute Quelle", True, "Webseite", True),  # accessed fehlt
    ("https://example.com accessed 2026-01-18", True, "Webseite", False),
    ("URL: example.com Zugriff 2026-01", True, "Webseite", False),

    # --- SPEC ---
    ("RFC 2616 ist HTTP Spec", True, "Spec", True),  # Jahr fehlt
    ("RFC 2616 (1999) HTTP Specification", True, "Spec", False),

    # --- MUSIK ---
    ("Song 'Bohemian Rhapsody'", True, "Musikstück", True),  # Artist fehlt
    ("Song 'Bohemian Rhapsody' von Queen", True, "Musikstück", False),
    ("Track 'Stairway to Heaven' Artist Led Zeppelin", True, "Musikstück", False),

    # --- ALBUM ---
    ("Album 'Abbey Road'", True, "Album", True),  # Artist + Jahr fehlt
    ("Album 'Abbey Road' Beatles", True, "Album", True),  # Jahr fehlt
    ("Album 'Abbey Road' von Beatles (1969)", True, "Album", False),

    # --- FILM ---
    ("Film 'Inception' ist genial", True, "Film", True),
    ("Film 'Inception' von Christopher Nolan", True, "Film", True),  # Jahr fehlt
    ("Film 'Inception' Regisseur Christopher Nolan 2010", True, "Film", False),
    ("Movie 'Matrix' Director Wachowski 1999", True, "Film", False),

    # --- ROMAN ---
    ("Roman '1984' ist düster", True, "Roman", True),
    ("Roman '1984' von George Orwell (1949)", True, "Roman", False),
    ("Novel 'Dune' by Frank Herbert 1965", True, "Roman", False),

    # --- GEMÄLDE ---
    ("Gemälde 'Mona Lisa' ist bekannt", True, "Gemälde", True),
    ("Gemälde 'Mona Lisa' von Leonardo da Vinci", True, "Gemälde", False),
    ("Painting 'Starry Night' Artist Van Gogh", True, "Gemälde", False),

    # --- PODCAST ---
    ("Podcast 'Lex Fridman' ist gut", True, "Podcast", True),  # Host fehlt
    ("Podcast 'Lex Fridman Podcast' Host Lex Fridman", True, "Podcast", False),

    # --- BIBELVERSE ---
    ("Johannes 3:16 sagt...", True, "Bibelvers", False),
    ("Psalm 23:1 ist bekannt", True, "Bibelvers", False),
    ("Matthäus 5:3 Seligpreisung", True, "Bibelvers", False),

    # --- KEIN ZITAT ---
    ("Ich habe heute viel gelernt", False, "", False),
    ("Die API funktioniert gut", False, "", False),
    ("GraphQL ist für kleine Teams overkill", False, "", False),
    # "Websites" im Text sollte NICHT web-citation triggern (war ein Bug)
    ("58K Websites geleakt wegen schlechter Secrets", False, "", False),
    ("Viele Websites nutzen .env Dateien", False, "", False),
]

# Neue Tests für source_description Integration
SOURCE_DESC_TESTS = [
    # (body, source_desc, expected_citable, expected_type, should_have_missing)
    # URL in body + Datum in source_desc - sollte trotzdem zählen
    ("https://example.com gute Doku", "Recherche 20.01.2026", True, "Webseite", False),  # DE-Datum
    ("https://docs.example.com/api", "Zugriff 2026-01-20", True, "Webseite", False),  # ISO-Datum
    ("https://blog.example.com/post", "", True, "Webseite", True),  # Kein Datum = missing
    # Procedure mit URLs in source_desc (der ursprüngliche Bug-Case)
    ("PROCEDURE: Secrets Management...", "Recherche 20.01.2026: https://gitguardian.com", False, "", False),
]

def run_tests():
    passed = 0
    failed = 0
    total = len(TESTS) + len(SOURCE_DESC_TESTS)

    print("=" * 60)
    print("Zitierfähigkeits-Prüfung Tests")
    print("=" * 60)

    # Standard Tests (body only)
    print("\n--- Body-Only Tests ---")
    for i, (body, exp_citable, exp_type, exp_has_missing) in enumerate(TESTS):
        is_citable, ctype, missing = check_citation(body)
        has_missing = len(missing) > 0

        ok_citable = is_citable == exp_citable
        ok_type = (not exp_citable) or (ctype == exp_type)
        ok_missing = has_missing == exp_has_missing

        if ok_citable and ok_type and ok_missing:
            passed += 1
            print(f"✓ Test {i+1}: {body[:40]}...")
        else:
            failed += 1
            print(f"✗ Test {i+1}: {body[:40]}...")
            print(f"  Expected: citable={exp_citable}, type='{exp_type}', has_missing={exp_has_missing}")
            print(f"  Got:      citable={is_citable}, type='{ctype}', has_missing={has_missing}")
            if missing:
                print(f"  Missing fields: {missing}")

    # Source Description Tests (body + source_desc)
    print("\n--- Body + Source_Desc Tests ---")
    for i, (body, src, exp_citable, exp_type, exp_has_missing) in enumerate(SOURCE_DESC_TESTS):
        is_citable, ctype, missing = check_citation(body, src)
        has_missing = len(missing) > 0

        ok_citable = is_citable == exp_citable
        ok_type = (not exp_citable) or (ctype == exp_type)
        ok_missing = has_missing == exp_has_missing

        if ok_citable and ok_type and ok_missing:
            passed += 1
            print(f"✓ SrcTest {i+1}: body='{body[:25]}...' src='{src[:20]}...'")
        else:
            failed += 1
            print(f"✗ SrcTest {i+1}: body='{body[:25]}...' src='{src[:20]}...'")
            print(f"  Expected: citable={exp_citable}, type='{exp_type}', has_missing={exp_has_missing}")
            print(f"  Got:      citable={is_citable}, type='{ctype}', has_missing={has_missing}")
            if missing:
                print(f"  Missing fields: {missing}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print("=" * 60)

    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
