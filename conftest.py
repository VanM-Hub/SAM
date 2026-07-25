import sys
from pathlib import Path

# Add the src directory to sys.path so that "src.sam.*" imports work
# and also so that "sam" can be resolved as src/sam
_src = str(Path(__file__).parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)
