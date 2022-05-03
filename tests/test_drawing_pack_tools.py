import unittest
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, patch

from src import drawing_pack_tools as tools

from tests import PROJECT


class TestProcessMatch(unittest.TestCase):
    def test_process_match_blank(self) -> None:
        input_string = ""
        result = tools.process_match(input_string)
        self.assertEqual(result, "*DWG*.dwg")

    def test_process_match_stars(self) -> None:
        input_string = "*****"
        result = tools.process_match(input_string)
        self.assertEqual(result, "*DWG*.dwg")

    def test_process_match_valid_drawing(self) -> None:
        input_string = "00200"
        result = tools.process_match(input_string)
        self.assertEqual(result, "*DWG*00200*.dwg")

    def test_process_match_valid_drawing_extras(self) -> None:
        input_string = "00200**R0"
        result = tools.process_match(input_string)
        self.assertEqual(result, "*DWG*00200*R0*.dwg")

    def test_process_match_PID(self) -> None:
        input_string = "PID-00200**R0"
        result = tools.process_match(input_string)
        self.assertEqual(result, "*PID-00200*R0*.dwg")


class TestGetFiles(unittest.TestCase):
    match = "*00200*.dwg"
    source = Path()

    def empty_generator(self) -> Generator[Path, None, None]:
        yield from ()

    def full_generator(self) -> Generator[Path, None, None]:
        files = [
            Path("5300221014-VWC-MS-DWG-00205-01-R0.dwg"),
            Path("5300221014-VWC-MS-DWG-00205-01-RA.dwg"),
            Path("5300221014-VWC-MS-DWG-00205-02-RA.dwg"),
            Path("5300221014-VWC-MS-DWG-00205-02-RB.dwg"),
            Path("5300221014-VWC-MS-DWG-00205-02-R0.dwg"),
            Path("5300221014-VWC-MS-DWG-00205-03-R0.dwg"),
            Path("5300221014-VWC-MS-DWG-00205-03-R1.dwg"),
            Path("00205-03-R1.dwg"),
        ]
        for file in files:
            yield file

    def test_files_not_found(self) -> None:
        with patch.object(Path, "glob", return_value=self.empty_generator()):
            self.assertEqual(tools.get_files(self.match, self.source), None)
        with patch.object(Path, "glob", return_value=self.empty_generator()):
            self.assertEqual(tools.get_file_count(self.match, self.source), 0)

    def test_found_files(self) -> None:
        with patch.object(Path, "glob", return_value=self.full_generator()):
            self.assertListEqual(
                list(tools.get_files(self.match, self.source)),  # type: ignore
                list(self.full_generator()),
            )
        with patch.object(Path, "glob", return_value=self.full_generator()):
            self.assertEqual(tools.get_file_count(self.match, self.source), 8)

    def test_get_latest(self) -> None:
        files = self.full_generator()
        expected = [
            Path("5300221014-VWC-MS-DWG-00205-01-R0.dwg"),
            Path("5300221014-VWC-MS-DWG-00205-02-R0.dwg"),
            Path("5300221014-VWC-MS-DWG-00205-03-R1.dwg"),
        ]
        actual = tools.get_latest(files)
        self.assertListEqual(expected, list(actual))


class TestAutoCad(unittest.TestCase):
    @patch.object(
        tools,
        "get_accore",
        return_value="C:/Program Files/Autodesk/AutoCAD 2019/accoreconsole.exe",
    )
    @patch("subprocess.run")
    def test_make_pdf(self, mock_run: Mock, mock_accore: Mock) -> None:
        source = Path("test_drawing.dwg")
        src = Path("test_scr.scr")
        tools.make_pdf(source, src)
        mock_accore.assert_called_once()
        mock_run.assert_called_once_with(
            '"C:/Program Files/Autodesk/AutoCAD 2019/accoreconsole.exe" /i "test_drawing.dwg" /s "test_scr.scr" /l "en-US"'
        )

    def test_get_accore(self) -> None:
        expected = "C:/Program Files/Autodesk/AutoCAD 2019/accoreconsole.exe"
        actual = tools.get_accore()
        self.assertEqual(Path(actual), Path(expected))

    def test_remove_plot_logs(self) -> None:
        plot = Path(PROJECT) / "plot.log"
        hardcopy = Path(PROJECT) / "hardcopy.log"
        plot.write_text("")
        hardcopy.write_text("")
        self.assertTrue(plot.exists())
        tools.remove_plot_logs()
        self.assertFalse(plot.exists())
        self.assertFalse(hardcopy.exists())
