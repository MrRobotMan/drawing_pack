import unittest
from unittest.mock import Mock, patch

from click.testing import CliRunner
from src import app, cli


class TestCLI(unittest.TestCase):
    @patch.object(app, "main", return_value="5300000000-VWC-MS-DWG-00200-01_10-R0.dwg")
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
        result = runner.invoke(cli.main, args=args)
        mock_main.assert_called_once()
        assert result.output == "5300000000-VWC-MS-DWG-00200-01_10-R0.dwg\n"
