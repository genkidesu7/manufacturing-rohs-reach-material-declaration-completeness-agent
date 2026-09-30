"""AgentCore Platform v1.0"""

# Shared mock-mode resolution helper.
#
# .claude/rules/implementation_rule.md Rule 1: the scaffold `deploy-stg` CI job sets
# STG_MOCK_MODE=true (CI-script-only variable) but never USE_MOCK — the canonical flag
# every service/test expects. Every mock-mode gate in this project must resolve through
# this single helper so a future rename only needs one edit, and so deploy-stg's env
# actually activates mock mode instead of silently falling through to the real path.

import os
from pathlib import Path

from dotenv import dotenv_values

_env: dict[str, str | None] = dotenv_values(Path(__file__).parent.parent.parent / ".env")


def _get_flag(key: str) -> str:
    """OS env takes precedence over .env file."""
    return os.environ.get(key) or _env.get(key) or ""


def mock_mode_enabled() -> bool:
    """True if mock mode is on via either USE_MOCK (canonical) or STG_MOCK_MODE (deploy-stg)."""
    return _get_flag("USE_MOCK").lower() in ("1", "true", "yes") or _get_flag("STG_MOCK_MODE").lower() in (
        "1",
        "true",
        "yes",
    )
