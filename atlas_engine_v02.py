# DEPRECIADO — mantido apenas para retrocompatibilidade de scripts externos.
# Use diretamente: from atlas_engine.atlas_engine import ATLASEngine, ATLASBlockedException
# (requer pip install -e services/atlas-engine)
import warnings
warnings.warn(
    "atlas_engine_v02.py na raiz está depreciado. "
    "Importe de atlas_engine.atlas_engine diretamente.",
    DeprecationWarning,
    stacklevel=2,
)
from atlas_engine.atlas_engine import ATLASEngine, ATLASBlockedException  # noqa: F401
