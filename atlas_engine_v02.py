from __future__ import annotations
from pathlib import Path
import sys

# Make sure local atlas-engine/src is importable
REPO_ROOT = Path(__file__).resolve().parent
ATLAS_ENGINE_SRC = REPO_ROOT / "services" / "atlas-engine" / "src"
sys.path.append(str(ATLAS_ENGINE_SRC))

from atlas_engine import ATLASEngine, ATLASBlockedException  # noqa: F401
