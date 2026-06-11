"""
Python mirror of the Unified Playbook Schema (dataclasses + helpers).

Companion to:
  references/UnifiedPlaybookSchema.ts
  kickga/playbook_schema.py (the package version)

See kickga/playbook_schema.py for full implementation + factories.
This file exists for quick reference / import from anywhere in t450 experiments.
"""

# Re-export everything from the package version for convenience
from kickga.playbook_schema import *  # noqa: F401,F403
