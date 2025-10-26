from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv

"""
Enhanced Config Loader
----------------------
Priority:
  1. OS env vars
  2. .env.<EMO_ENV> (if exists)
  3. .env
Provides: get(), require(), as_bool()
"""

class Config:
    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root) if root else Path.cwd()
        self._load()

    def _load(self):
        # Load base .env
        base_env = self.root / ".env"
        if base_env.exists():
            load_dotenv(base_env)
        # Load per-env override
        emo_env = os.getenv("EMO_ENV", "dev").lower()
        env_specific = self.root / f".env.{emo_env}"
        if env_specific.exists():
            load_dotenv(env_specific, override=True)
        # In-memory snapshot
        self._env: Dict[str, str] = dict(os.environ)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self._env.get(key, default)

    def require(self, key: str) -> str:
        val = self.get(key)
        if not val:
            raise RuntimeError(f"Missing required config: {key}")
        return val

    def as_bool(self, key: str, default: bool = False) -> bool:
        val = self.get(key)
        if val is None:
            return default
        return str(val).strip().lower() in ("1", "true", "yes", "on")

if __name__ == "__main__":
    c = Config()
    print("EMO_ENV=", c.get("EMO_ENV", "dev"))
    print("DB URL sample via router: run `make db-url`")