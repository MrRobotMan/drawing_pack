import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner
from src import drawing_pack
from src import drawing_pack_layouts as layouts
from src import drawing_pack_model as model


class TestAppHelpers(unittest.TestCase):
    @patch.object(
        drawing_pack, "main", return_value="5300000000-VWC-MS-DWG-00200-01_10-R0.dwg"
    )
    def test_cli_args(self, mock_main: Mock) -> None:
        args = [
            "00200*R0",
            ".",
            "-d",
            ".",
            "-o",
            "5300000000-VWC-MS-DWG-00200-01_10-R0.dwg",
            "-p",
            "-l",
            "-k",
            "-x",
            "-v",
        ]
        runner = CliRunner()
        result = runner.invoke(drawing_pack.app, args=args)
        mock_main.assert_called_once()
        assert result.output == "5300000000-VWC-MS-DWG-00200-01_10-R0.dwg\n"

    def test_get_output_files_no_name(self) -> None:
        files = list(drawing_pack.get_output_files(4, Path(), None))
        self.assertListEqual(files, [None] * 4)

    def test_get_output_files_named(self) -> None:
        files = [str(file) for file in drawing_pack.get_output_files(4, Path(), "file")]
        self.assertListEqual(
            files, ["file.pdf", "file(1).pdf", "file(2).pdf", "file(3).pdf"]
        )

    def test_get_total(self) -> None:
        total, paths = drawing_pack.get_total((Path() for _ in range(2)))
        self.assertEqual(total, 2)
        self.assertEqual([".", "."], [str(path) for path in paths])


class FileHandler:
    def __init__(self) -> None:
        self.files = (
            Path("5300221014-VWC-MS-DWG-00200-01-R0.dwg"),
            Path("5300221014-VWC-MS-DWG-00200-01-RA.dwg"),
            Path("5300221014-VWC-MS-DWG-00200-02-RA.dwg"),
            Path("5300221014-VWC-MS-DWG-00200-02-RB.dwg"),
            Path("5300221014-VWC-MS-DWG-00200-02-R0.dwg"),
            Path("5300221014-VWC-MS-DWG-00200-03-R0.dwg"),
            Path("5300221014-VWC-MS-DWG-00200-03-R1.dwg"),
        )
        self.setup()

    def setup(self) -> None:
        for file in self.files:
            with file.open("w+"):
                pass

    def teardown(self) -> None:
        for file in self.files:
            file.unlink()


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
        result = drawing_pack.main("", Path(source))
        self.assertEqual(result, f"Could not find '{source}'")

    def test_no_match(self) -> None:
        search = "*PID*00200*.dwg"
        source = Path()
        result = drawing_pack.main(search, source)
        self.assertEqual(result, f"No matching files for '*PID*00200*.dwg' in '.'")

    @patch.object(
        layouts, "main", return_value=Path("5300221014-VWC-MS-DWG-00200-01-R0.pdf")
    )
    def test_paperspace(self, mock_main: Mock) -> None:
        source = self.files[0]
        with source.open("w+"):
            pass
        result = drawing_pack.main("", source, latest=False, paper=True)
        self.assertEqual(result, str(source.with_suffix(".pdf")))
        mock_main.assert_called_once()
        source.unlink()

    @patch.object(
        model, "main", return_value=Path("5300221014-VWC-MS-DWG-00200-01_03-R0.pdf")
    )
    def test_model(self, mock_main: Mock) -> None:
        match = "00200"
        source = Path()
        result = drawing_pack.main(match, source)
        mock_main.assert_called_once()
        self.assertEqual(result, "5300221014-VWC-MS-DWG-00200-01_03-R0.pdf")
