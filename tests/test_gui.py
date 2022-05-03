# pyright: reportUnknownMemberType=false, reportGeneralTypeIssues=false

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PySide6.QtTest import QTest
from src import app, gui

from tests import PROJECT


class TestGUI(unittest.TestCase):
    source = R".\Testing"
    dest = R".\Testing"

    def setUp(self) -> None:
        self.app = gui.MainApplication()

    def tearDown(self) -> None:
        self.app.shutdown()

    def test_path_change(self) -> None:
        QTest.keyClicks(self.app.source, self.source)
        self.app.source.editingFinished.emit()
        text = self.app.status.toPlainText()
        last_line = text.split("\n")[-1]
        self.assertEqual(last_line, R"Source Folder: .\Testing")

    def test_sheets_toggle(self) -> None:
        self.app.layouts.setChecked(True)
        self.app.sheets()
        self.assertTrue(self.app.keep_sheets.isChecked())
        self.app.layouts.setChecked(False)
        self.app.sheets()
        self.assertFalse(self.app.keep_sheets.isVisible())

    def test_console(self) -> None:
        self.app.console("Test Text")
        self.assertEqual("Test Text", self.app.status.toPlainText().split("\n")[-1])
        sys.stderr.write("Test Error")
        self.assertEqual("Test Error", self.app.status.toPlainText().split("\n")[-1])

    def test_restore_stderr(self) -> None:
        self.app.__del__()
        self.assertEqual(sys.stderr, sys.__stderr__)

    def test_open_file(self) -> None:
        self.app.latest_file = Path("Test File.pdf")
        with patch.object(os, "startfile") as mock_startfile:
            self.app.open_file()
            mock_startfile.assert_called_once_with(Path("Test File.pdf"))
            self.assertFalse(self.app.open.isVisible())

    def test_set_latest(self) -> None:
        files = "file1.pdf\nfile2.pdf"
        self.app.set_latest(files)
        self.assertEqual(self.app.latest_file, Path("file1.pdf"))

    @patch.object(app, "main", return_value="Test File.pdf")
    def test_paperspace(self, mock_main: Mock) -> None:
        self.app.source.setText(self.source)
        self.app.dest.setText(self.dest)
        self.app.layouts.setChecked(True)
        self.app.layouts.clicked.emit()
        self.app.process()
        mock_main.assert_called_once_with(
            match="",
            source=Path(self.source),
            dest=Path(self.dest),
            output=None,
            paper=True,
            latest=True,
            keep=True,
            del_source=False,
            view=False,
        )

    def test_modelspace(self) -> None:
        self.app.match.setText("00200")
        self.app.rev.setText("R0")
        self.app.source.setText(str(PROJECT))
        self.app.process()
        self.assertEqual(
            f"Error: No matching files for '00200*R0' in '{PROJECT}'",
            self.app.status.toPlainText().split("\n")[-1],
        )
