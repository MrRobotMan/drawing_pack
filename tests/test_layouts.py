import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

from src import layouts
from tests import PROJECT, SRC, TESTS

BASE = (SRC / "pdfgen11x17layout.scr").read_text().splitlines()
multi_file = TESTS / "5300221014-VWC-MS-DWG-00200-01_03-R0.dwg"
sheet_names = [
    TESTS / f"5300221014-VWC-MS-DWG-00200-01_03-R0-{i}-R0.pdf" for i in range(1, 4)
]
sheets = ["-01-R0", "-02-R0", "-03-R0"]
single_file = TESTS / "5300221014-VWC-MS-DWG-00200-01-R0.dwg"


class TestLayouts(unittest.TestCase):
    def test_get_base_name_single(self) -> None:
        self.assertEqual(
            layouts.get_base_name(multi_file, 3), "5300221014-VWC-MS-DWG-00200"
        )

    def test_get_base_name_multi(self) -> None:
        self.assertEqual(
            layouts.get_base_name(single_file, 1),
            "5300221014-VWC-MS-DWG-00200-01-R0",
        )

    @patch("src.tools.make_pdf")
    def test_process_sheets(self, mock_make_pdf: Mock) -> None:
        layouts.process_sheets(sheets, PROJECT, TESTS, BASE)
        self.assertEqual(3, mock_make_pdf.call_count)

        # Clean up files made by test
        for file in TESTS.iterdir():
            if "scr" in file.name:
                file.unlink()

    def test_bad_sheet_name(self) -> None:
        self.assertEqual(layouts.clean_sheet_name("A"), "")

    def test_rename_file(self) -> None:
        scr = BASE
        scr[2] = f'"1-R0"\n'
        test_scr = TESTS / "test.scr"
        test_scr.write_text("\n".join(scr))
        sheet_names[0].write_bytes(b"")
        result = layouts.rename_file(multi_file, test_scr, 2)
        self.assertTrue(result.exists())
        test_scr.unlink()
        result.unlink()

    @patch("subprocess.run")
    def test_get_layouts(self, mock_subprocess: Mock) -> None:
        layouts_file = SRC / "layouts.txt"
        layouts_file.write_text("Model\n-01-R0\n-02-R0\n-03-R0")
        _sheets, qty = layouts.get_layouts(multi_file)
        self.assertListEqual(list(_sheets), sheets)
        self.assertEqual(qty, 3)

    @patch.object(layouts, "remove_temp")
    @patch.object(layouts, "merge")
    @patch.object(layouts, "rename_file", side_effect=sheet_names)
    @patch.object(layouts, "process_sheets", return_value=[f"scr{i}" for i in range(3)])
    @patch.object(layouts, "get_layouts", return_value=(sheets, 3))
    @patch.object(shutil, "copyfile")
    def test_main_with_dest_and_output(
        self,
        mock_copy_file: Mock,
        mock_get_layouts: Mock,
        mock_process_sheets: Mock,
        mock_rename_file: Mock,
        mock_merge: Mock,
        mock_remove_temp: Mock,
    ) -> None:
        output = TESTS / "5300221014-VWC-MS-DWG-00200-01_03-R0.pdf"
        base_scr = (SRC / "pdfgen11x17layout.scr").read_text().splitlines()
        result = layouts.main(
            source=PROJECT / "5300221014-VWC-MS-DWG-00200-01_03-R0.dwg",
            destination=TESTS,
            output=Path(output.name),
            view=False,
            del_source=False,
            keep_individual=False,
        )
        mock_copy_file.assert_called_once()
        mock_get_layouts.assert_called_once_with(multi_file)
        mock_process_sheets.assert_called_once_with(sheets, multi_file, TESTS, base_scr)
        self.assertEqual(3, mock_rename_file.call_count)
        mock_merge.assert_called_once_with(sheet_names, output)
        remove_temp_call_args = [
            call((TESTS / "5300221014-VWC-MS-DWG-00200-01_03-R0.dwg",)),
            call(sheet_names),
            call([f"scr{i}" for i in range(3)]),
        ]
        self.assertListEqual(remove_temp_call_args, mock_remove_temp.call_args_list)
        self.assertEqual(output, result)

    @patch.object(os, "startfile")
    @patch.object(layouts, "remove_temp")
    @patch.object(layouts, "merge")
    @patch.object(layouts, "rename_file", side_effect=sheet_names)
    @patch.object(layouts, "process_sheets", return_value=[f"scr{i}" for i in range(3)])
    @patch.object(layouts, "get_layouts", return_value=(sheets, 3))
    def test_main_no_dest_or_output(
        self,
        mock_get_layouts: Mock,
        mock_process_sheets: Mock,
        mock_rename_file: Mock,
        mock_merge: Mock,
        mock_remove_temp: Mock,
        mock_startfile: Mock,
    ) -> None:
        output = multi_file.with_suffix(".pdf")
        base_scr = (SRC / "pdfgen11x17layout.scr").read_text().splitlines()
        result = layouts.main(
            source=multi_file,
            destination=None,
            output=None,
            view=True,
            del_source=False,
            keep_individual=True,
        )
        mock_get_layouts.assert_called_once_with(multi_file)
        mock_process_sheets.assert_called_once_with(sheets, multi_file, TESTS, base_scr)
        self.assertEqual(3, mock_rename_file.call_count)
        mock_merge.assert_called_once_with(sheet_names, output)
        mock_remove_temp.assert_called_once_with([f"scr{i}" for i in range(3)])
        mock_startfile.assert_called_once_with(output)
        self.assertEqual(output, result)
