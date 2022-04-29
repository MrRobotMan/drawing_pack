import ctypes
import os
import sys
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QToolButton,
    QWidget,
)

from src import drawing_pack


class emitter(QObject):
    textWritten = Signal(str)

    def write(self, text: Any):
        self.textWritten.emit(str(text))


class MainApplication(QApplication):
    def __init__(self) -> None:
        super().__init__(sys.argv)
        # Set the process ID so the taskbar icon in windows shows correctly.
        if os.name == "nt":
            app_id = "DrawingPack"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        self.latest_file = Path()
        self.window = QMainWindow()
        self.window.setWindowTitle("Drawing Pack Tool")
        self.window.setWindowIcon(
            QIcon(str(Path(__file__).with_name("veolia_logo_sm.png")))
        )
        self.grid = QGridLayout()

        self.match_label = QLabel("Enter Drawing Number\n[e.g. 205, blank for all]")
        self.match = QLineEdit()
        self.match.setFixedWidth(133)

        self.rev_label = QLabel("Rev")
        self.rev = QLineEdit()
        self.rev.setFixedWidth(25)

        self.source_label = QLabel("Enter Source Path")
        self.source = QLineEdit()
        self.source.setFixedWidth(158)
        self.source_picker = QToolButton()
        self.source_picker.setArrowType(Qt.RightArrow)
        self.source_picker.clicked.connect(
            lambda: self.get_directory(self.source, "Q:/CAD_Drawings/Contract")
        )
        self.source.editingFinished.connect(
            lambda: self.path_change(self.source, "Source")
        )

        self.dest_label = QLabel("Enter Destination Path\n[if not source]")
        self.dest = QLineEdit()
        self.dest.setFixedWidth(158)
        self.dest_picker = QToolButton()
        self.dest_picker.setArrowType(Qt.RightArrow)
        self.dest_picker.clicked.connect(
            lambda: self.get_directory(self.dest, str(Path.home()))
        )
        self.dest.editingFinished.connect(
            lambda: self.path_change(self.dest, "Destination")
        )

        self.output_label = QLabel("Enter Output File Name\n[optional]")
        self.output = QLineEdit()
        self.output.setFixedWidth(189)

        self.layouts_label = QLabel("Get paperspace instead of modelspace")
        self.layouts = QCheckBox()
        self.layouts.clicked.connect(self.sheets)

        self.keep_sheets_label = QLabel("Keep individual sheets also")
        self.keep_sheets = QCheckBox()

        self.status = QTextEdit("Ready")
        self.status.append("Leave Rev blank to get the latest revision of each file")
        self.status.append(
            "Leave output blank to get a file name of 5300XXXXXX-VWC-MS-DWG-XXXXX-01_ZZ-RX"
        )
        self.status.setReadOnly(True)
        self.status.setMinimumWidth(400)
        self.go = QPushButton("Go")
        self.open = QPushButton("Open File")
        self.match.returnPressed.connect(self.process)
        self.rev.returnPressed.connect(self.process)
        self.source.returnPressed.connect(self.process)
        self.dest.returnPressed.connect(self.process)
        self.output.returnPressed.connect(self.process)
        self.go.clicked.connect(self.process)
        self.open.clicked.connect(self.open_file)

        sys.stderr = emitter()
        sys.stderr.textWritten.connect(self.console)

        self.grid.setColumnStretch(4, 1)
        self.window.setFixedHeight(250)
        self.window.setMinimumWidth(830)

        self.initUI()
        self.window.show()

    def initUI(self):
        central_widget = QWidget()
        central_widget.setLayout(self.grid)
        self.grid.addWidget(self.match_label, 0, 0)
        self.grid.addWidget(self.match, 0, 1)

        self.grid.addWidget(self.rev_label, 0, 2)
        self.grid.addWidget(self.rev, 0, 3)

        self.grid.addWidget(self.source_label, 1, 0)
        self.grid.addWidget(self.source, 1, 1, 1, 2)
        self.grid.addWidget(self.source_picker, 1, 3)

        self.grid.addWidget(self.dest_label, 2, 0)
        self.grid.addWidget(self.dest, 2, 1, 1, 2)
        self.grid.addWidget(self.dest_picker, 2, 3)

        self.grid.addWidget(self.output_label, 3, 0)
        self.grid.addWidget(self.output, 3, 1, 1, 3)

        self.grid.addWidget(self.layouts_label, 4, 0, 1, 2)
        self.grid.addWidget(self.layouts, 4, 3, Qt.AlignRight)

        self.grid.addWidget(self.keep_sheets_label, 5, 0, 1, 2)
        self.keep_sheets_label.hide()
        self.grid.addWidget(self.keep_sheets, 5, 3, Qt.AlignRight)
        self.keep_sheets.hide()

        self.grid.addWidget(self.status, 0, 4, 6, 1)
        self.grid.addWidget(self.go, 6, 0)
        self.grid.addWidget(self.open, 6, 1)
        self.open.hide()

        self.window.setCentralWidget(central_widget)

    def get_directory(self, entry: QLineEdit, default: str) -> None:
        source_picker = QFileDialog.getExistingDirectory(dir=default)
        entry.setText(source_picker)
        entry.editingFinished.emit()

    def process(self) -> None:
        if self.match.text():
            match = self.match.text().zfill(5)
        else:
            match = ""
        if self.rev.text():
            match += f"*R{self.rev.text()}"
            latest = False
        else:
            latest = True
        match.replace("RR", "R")  # If rev was input as R0 instead of 0 only.
        dest = Path(self.dest.text()) if self.dest.text() else None
        output = self.output.text() if self.output.text() else None
        result = drawing_pack.main(
            match=match,
            source=Path(self.source.text()),
            dest=dest,
            output=output,
            paper=self.layouts.isChecked(),
            latest=latest,
            keep=self.keep_sheets.isChecked(),
            del_source=False,
            view=False,
        )
        if isinstance(result, str):
            self.status.append(result)
        else:
            self.latest_file = result
            self.open.show()
            self.match.setText("")
            self.rev.setText("")
            self.output.setText("")
            self.status.append(f"Success! {self.latest_file} created.")

    def __del__(self):
        """Restore stderr"""
        sys.stderr = sys.__stderr__

    def console(self, text: Any):
        """Append to status box"""
        self.status.append(text)

    def path_change(self, textbox: QLineEdit, loc: str):
        """Print new path to output"""
        self.status.append(f"{loc} Folder: {textbox.text()}")

    def open_file(self):
        """Opens the file and removes the button."""
        os.startfile(self.latest_file)
        self.open.hide()

    def sheets(self):
        """Checks the box to keep individual sheets when selecting layout only"""
        if self.layouts.isChecked():
            self.keep_sheets_label.show()
            self.keep_sheets.show()
            self.keep_sheets.setChecked(True)
        else:
            self.keep_sheets_label.hide()
            self.keep_sheets.hide()


if __name__ == "__main__":
    app = MainApplication()
    sys.exit(app.exec())
