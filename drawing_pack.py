import sys

from src import cli
from src.gui import MainApplication


def main() -> None:
    if len(sys.argv) == 1:
        app = MainApplication()
        sys.exit(app.exec())
    else:
        cli.main()


if __name__ == "__main__":
    main()
