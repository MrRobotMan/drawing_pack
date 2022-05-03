import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src import app, layouts, model


class TestMain(unittest.TestCase):
    files = (
        Path("5300221014-VWC-MS-DWG-00200-01-R0.dwg"),
        Path("5300221014-VWC-MS-DWG-00200-01-RA.dwg"),
        Path("5300221014-VWC-MS-DWG-00200-02-RA.dwg"),
        Path("5300221014-VWC-MS-DWG-00200-02-RB.dwg"),
        Path("5300221014-VWC-MS-DWG-00200-02-R0.dwg"),
        Path("5300221014-VWC-MS-DWG-00200-03-R0.dwg"),
        Path("5300221014-VWC-MS-DWG-00200-03-R1.dwg"),
    )

    @classmethod
    def setUpClass(cls) -> None:
        for file in cls.files:
            file.write_bytes(b"")

    @classmethod
    def tearDownClass(cls) -> None:
        for file in cls.files:
            try:
                file.unlink()
            except FileNotFoundError:
                continue

    def test_bad_paperspace(self) -> None:
        source = "FileDoesNotExist.txt"
        result = app.main("", Path(source))
        self.assertEqual(result, f"Error: Could not find '{source}'")

    def test_no_match(self) -> None:
        search = "*PID*00200*.dwg"
        source = Path()
        result = app.main(search, source)
        self.assertEqual(result, f"Error: No matching files for '*PID*00200*.dwg' in '.'")

    @patch.object(
        layouts, "main", return_value=Path("5300221014-VWC-MS-DWG-00200-01-R0.pdf")
    )
    def test_paperspace(self, mock_main: Mock) -> None:
        source = self.files[0]
        with source.open("w+"):
            pass
        result = app.main("", source, latest=False, paper=True)
        self.assertEqual(result, str(source.with_suffix(".pdf")))
        mock_main.assert_called_once()
        source.unlink()

    @patch.object(
        model, "main", return_value=Path("5300221014-VWC-MS-DWG-00200-01_03-R0.pdf")
    )
    def test_model(self, mock_main: Mock) -> None:
        match = "00200"
        source = Path()
        result = app.main(match, source)
        mock_main.assert_called_once()
        self.assertEqual(result, "5300221014-VWC-MS-DWG-00200-01_03-R0.pdf")

    def test_get_output_files_no_name(self) -> None:
        files = list(app.get_output_files(4, Path(), None))
        self.assertListEqual(files, [None] * 4)

    def test_get_output_files_named(self) -> None:
        files = [str(file) for file in app.get_output_files(4, Path(), "file")]
        self.assertListEqual(
            files, ["file.pdf", "file(1).pdf", "file(2).pdf", "file(3).pdf"]
        )

    def test_get_total(self) -> None:
        total, paths = app.get_total((Path() for _ in range(2)))
        self.assertEqual(total, 2)
        self.assertEqual([".", "."], [str(path) for path in paths])
