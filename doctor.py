#!/usr/bin/env python3
"""Sanity-check the environment before a timed practice run.

    python doctor.py
"""
import importlib
import sys

REQUIRED = ["fastapi", "uvicorn", "httpx", "pydantic", "pytest"]


def main() -> int:
    ok = True

    if sys.version_info < (3, 10):
        print(f"✗ Python 3.10+ required, found {sys.version.split()[0]}")
        ok = False
    else:
        print(f"✓ Python {sys.version.split()[0]}")

    for mod in REQUIRED:
        try:
            importlib.import_module(mod)
            print(f"✓ {mod} importable")
        except ImportError:
            print(f"✗ {mod} not installed — run: pip install -r requirements.txt")
            ok = False

    try:
        import mock_crm.main  # noqa: F401
        print("✓ mock_crm.main imports cleanly")
    except Exception as e:
        print(f"✗ mock_crm.main failed to import: {e}")
        ok = False

    try:
        import platform_service.main  # noqa: F401
        print("✓ platform_service.main imports cleanly")
    except Exception as e:
        print(f"✗ platform_service.main failed to import: {e}")
        ok = False

    if ok:
        print("\nAll good. Start the timer and go.")
    else:
        print("\nFix the above before starting your timed run.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
