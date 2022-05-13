import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

from src import model
from tests import PROJECT, TESTS


class TestModel(unittest.TestCase):
    files = [
        Path("5300221014-VWC-MS-DWG-00200-01-R0.dwg"),
        Path("5300221014-VWC-MS-DWG-00200-02-R0.dwg"),
        Path("5300221014-VWC-MS-DWG-00200-03-R0.dwg"),
    ]

    @patch.object(shutil, "copy")
    def test_create_temp_files(self, mock_copy: Mock) -> None:
        model.create_temp_files(self.files, PROJECT, TESTS)
        self.assertEqual(mock_copy.call_count, 3)

    def test_remove_temp(self) -> None:
        temp: list[Path] = []
        for file in self.files:
            (PROJECT / file).write_bytes(b"")
            temp.append(PROJECT / file)
            (PROJECT / f"{file.stem}-Model.pdf").write_bytes(b"")
            temp.append(PROJECT / f"{file.stem}-Model.pdf")
        model.remove_temp(self.files, PROJECT, True)
        for file in temp:
            self.assertFalse(file.exists())

    @patch("builtins.print")
    def test_bad_temp(self, mock_print: Mock) -> None:
        files = (PROJECT / f"{file.stem}-Model.pdf" for file in self.files)
        call_args = [call(f"Could not find {pdf} to delete.") for pdf in files]
        model.remove_temp(self.files, PROJECT, False)
        self.assertEqual(mock_print.call_count, 3)
        self.assertListEqual(call_args, mock_print.call_args_list)

    @patch("src.tools.make_pdf")
    def test_process_sheets(self, mock_make_pdf: Mock) -> None:
        model.process_sheets(self.files, TESTS)
        self.assertEqual(3, mock_make_pdf.call_count)

    @patch.object(model, "remove_temp")
    @patch.object(model, "merge_pdf")
    @patch.object(model, "process_sheets")
    @patch.object(model, "create_temp_files")
    def test_main_with_dest_and_output(
        self,
        mock_create_temp_files: Mock,
        mock_process_sheets: Mock,
        mock_merge_pdf: Mock,
        mock_remove_temp: Mock,
    ) -> None:
        output = TESTS / "Combined.pdf"
        result = model.main(
            drawings=self.files,
            source=PROJECT,
            sht_count=3,
            dest=TESTS,
            output=output,
            view=False,
            remove_dwg=False,
        )
        mock_create_temp_files.assert_called_once_with(self.files, PROJECT, TESTS)
        mock_process_sheets.assert_called_once_with(self.files, TESTS)
        mock_merge_pdf.assert_called_once_with(self.files, TESTS, output)
        mock_remove_temp.assert_called_once_with(self.files, TESTS, True)
        self.assertEqual(result, output)

    @patch.object(os, "startfile")
    @patch.object(model, "remove_temp")
    @patch.object(model, "merge_pdf")
    @patch.object(model, "process_sheets")
    def test_main_no_dest_or_output(
        self,
        mock_process_sheets: Mock,
        mock_merge_pdf: Mock,
        mock_remove_temp: Mock,
        mock_view: Mock,
    ) -> None:
        output = PROJECT / "5300221014-VWC-MS-DWG-00200-01_03-R0.pdf"
        result = model.main(
            drawings=self.files,
            source=PROJECT,
            sht_count=3,
            dest=None,
            output=None,
            view=True,
            remove_dwg=False,
        )
        mock_process_sheets.assert_called_once_with(self.files, PROJECT)
        mock_merge_pdf.assert_called_once_with(self.files, PROJECT, output)
        mock_remove_temp.assert_called_once_with(self.files, PROJECT, False)
        mock_view.assert_called_once_with(output)
        self.assertEqual(result, output)
