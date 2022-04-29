import sys

from src.drawing_pack import app
from src.drawing_pack_gui import MainApplication

if len(sys.argv) == 1:
    app = MainApplication()
    sys.exit(app.exec())
else:
    app()
