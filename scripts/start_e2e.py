"""Same launcher/production code, with a guarded test-only provider injection."""

from start import main

if __name__ == "__main__":
    raise SystemExit(main(app_import="test_support.e2e_app:app"))
