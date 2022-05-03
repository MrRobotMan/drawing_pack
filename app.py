import sys

from src import drawing_pack
from src.drawing_pack_gui import MainApplication


def main() -> None:
    if len(sys.argv) == 1:
        app = MainApplication()
        sys.exit(app.exec())
    else:
        drawing_pack.app()


if __name__ == "__main__":
    main()
