import sys
from pathlib import Path

TESTS = Path(__file__).parent
PROJECT = TESTS.parent
SRC = PROJECT / "src"

sys.path.append(str(SRC.absolute()))
