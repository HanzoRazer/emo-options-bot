#!/usr/bin/env python
"""
generate_local_env.py
Creates a `local.dev.env` capturing your machine's absolute paths and typical
environment variables used in EMO/Phase 3 development.

Run:
    python tools/generate_local_env.py
"""

import os
from pathlib import Path

ENV_PATH = Path("local.dev.env")

def main():
    root = Path(__file__).resolve().parents[1]
    phase3_dir = root / "src" / "phase3"
    alpaca_key = os.getenv("ALPACA_KEY_ID", "")

    lines = [
        f"# Auto-generated local environment — edit as needed",
        f"EMO_ENV=dev",
        f"PHASE3_MODULE_DIR={phase3_dir}",
        f"PROJECT_ROOT={root}",
        f"ALPACA_KEY_ID={alpaca_key}",
        f"PYTHONPATH={root / 'src'}",
    ]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Created {ENV_PATH.resolve()}")

if __name__ == "__main__":
    main()