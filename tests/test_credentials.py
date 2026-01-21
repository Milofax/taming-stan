#!/usr/bin/env python3
"""
Automatisierte Tests für Secret-Erkennung (Format-basiert).
Testet die neue format-basierte Erkennung statt keyword-basiert.
"""
import sys, os, importlib.util

# Load secret_patterns module
lib_path = os.path.join(os.path.dirname(__file__), '..', 'hooks', 'lib')
sys.path.insert(0, lib_path)
from secret_patterns import detect_secret, has_keyword_with_value, _compile_patterns

# Load graphiti-guard to test has_creds integration
hook_path = os.path.join(os.path.dirname(__file__), '..', 'hooks', 'pre-tool-use', 'graphiti-guard.py')
spec = importlib.util.spec_from_file_location("graphiti_guard", hook_path)
graphiti_guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graphiti_guard)
has_creds = graphiti_guard.has_creds

# =============================================================================
# TEST CASES
# =============================================================================

# Format: (text, should_block, reason)
TESTS = [
    # =========================================================================
    # SOLLTE BLOCKIEREN - Echte Secrets (Format erkannt)
    # =========================================================================

    # AWS
    ("AKIAIOSFODNN7EXAMPLE", True, "AWS Access Key ID"),
    ("My key is AKIA1234567890ABCDEF", True, "AWS Key in text"),

    # GitHub
    ("ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", True, "GitHub PAT"),
    ("Token: gho_1234567890abcdefghijklmnopqrstuvwxyz", True, "GitHub OAuth"),

    # API Keys (generic patterns, no Stripe to avoid GitHub push protection)
    ("AKIAIOSFODNN7TESTKEY1", True, "AWS Key variant"),
    ("xoxp-123456789012-123456789012-123456789012-abcdefghijklmnopqrstuvwxyz1234", True, "Slack User Token"),

    # Private Keys
    ("-----BEGIN RSA PRIVATE KEY-----", True, "RSA Private Key"),
    ("-----BEGIN PRIVATE KEY-----", True, "Generic Private Key"),
    ("-----BEGIN EC PRIVATE KEY-----", True, "EC Private Key"),
    ("-----BEGIN OPENSSH PRIVATE KEY-----", True, "OpenSSH Private Key"),

    # Slack
    ("xoxb-123456789012-123456789012-xxxxxxxxxxxx", True, "Slack Bot Token"),

    # Discord (Pattern erwartet discordapp.com oder längeren Token)
    ("https://discordapp.com/api/webhooks/123456789012345678/abcdefghijklmnop", True, "Discord Webhook"),

    # Credit Cards (Visa: 16 digits starting with 4, Amex: 15 digits starting with 34/37)
    ("4111111111111111", True, "Visa Card"),
    ("4532015112830366", True, "Visa Card 2"),
    ("AMEX: 378282246310005", True, "Amex Card"),

    # Keyword + Value (e.g., "password: xyz123")
    ("password: mysecret123", True, "Password with value"),
    ("api_key = abc123xyz789", True, "API key with value"),
    ("secret: hunter2", True, "Secret with value"),
    ("token = eyJhbGciOiJIUzI1NiJ9", True, "Token with value"),

    # =========================================================================
    # SOLLTE ERLAUBEN - Keine echten Secrets
    # =========================================================================

    # Keywords ohne Werte (Dokumentation erlaubt)
    ("1Password is a great tool", False, "1Password app name"),
    ("1Password: Persoenlich + Teams, SSH Agent Integration", False, "1Password with colon (product description)"),
    ("TokenService handles auth", False, "Class name with token"),
    ("credentials for login", False, "Keyword ohne Wert"),
    ("password manager", False, "Password Manager reference"),
    ("The token endpoint is /api/auth", False, "Token as API term"),
    ("secret santa event", False, "Secret as normal word"),
    ("my PIN code system", False, "PIN as concept"),

    # Namen und Kontakte (erlaubt)
    ("Mathias arbeitet bei Firma XYZ", False, "Name"),
    ("Contact: Max Mustermann", False, "Contact name"),
    ("Author: John Doe", False, "Author name"),

    # Adressen und Orte (erlaubt)
    ("Büro in Berlin, Hauptstr. 5", False, "Address"),
    ("Location: Munich, Germany", False, "Location"),
    ("Office at 123 Main Street", False, "Street address"),

    # E-Mail und Telefon (erlaubt - Kontakte!)
    ("E-Mail: test@example.com", False, "Email address"),
    ("Contact: user@company.org", False, "Email in text"),
    ("Tel: +49 171 1234567", False, "Phone number"),
    ("Call: (555) 123-4567", False, "US phone"),

    # Normale Zahlen und Beträge (erlaubt)
    ("Projekt kostet 5000 Euro", False, "Money amount"),
    ("Budget: $10,000", False, "Dollar amount"),
    ("ID: 123456", False, "Normal ID number"),
    ("Version 2.0.0", False, "Version number"),

    # Zeit (erlaubt)
    ("Meeting um 14:30 Uhr", False, "Time"),
    ("Deadline: 2024-12-31", False, "Date"),

    # Technische Begriffe ohne Secrets
    ("API documentation", False, "API as term"),
    ("OAuth flow explained", False, "OAuth as concept"),
    ("JWT token format", False, "JWT as concept"),
    ("encryption key management", False, "Key as concept"),
]


def run_tests():
    """Führt alle Tests aus."""
    patterns = _compile_patterns()

    print("=" * 70)
    print("Secret-Erkennung Tests (Format-basiert)")
    print("=" * 70)
    print(f"Geladene Patterns: {len(patterns)}")
    print("=" * 70)

    passed = 0
    failed = 0

    for text, should_block, reason in TESTS:
        # Test via graphiti-guard's has_creds (which uses detect_secret + has_keyword_with_value)
        found, secret_type = has_creds(text)

        if found == should_block:
            passed += 1
            action = "BLOCK" if found else "ALLOW"
            print(f"✓ [{action}] '{text[:45]}...' ({reason})")
        else:
            failed += 1
            print(f"✗ '{text[:45]}...'")
            print(f"  Erwartet: {'BLOCK' if should_block else 'ALLOW'} ({reason})")
            print(f"  Ergebnis: {'BLOCK' if found else 'ALLOW'}" + (f" - {secret_type}" if found else ""))

    print("\n" + "=" * 70)
    print(f"Ergebnis: {passed}/{len(TESTS)} bestanden, {failed} fehlgeschlagen")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
