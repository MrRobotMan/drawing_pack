import re
import subprocess
from pathlib import Path
from typing import Iterable

from src import CWD

# Grab the drawing "number" and revision
# 5300600002-VWC-MS-SPC-00001-00-R34
# base: 5300600002-VWC-MS-SPC-00001-00
# ?: = non-caputuring group, thrown away
# rev: 34
DWG = re.compile(r"(?P<base>\w{10}-\w{3}-\w{2}-\w{3}-\w{5}.*)(?:-R)(?P<rev>\w+)")


def process_match(match: str) -> str:
    """Return a cleaned version of the match string, removing duplicate *
    >>> process_match('*************')
    '*DWG*.dwg'
    >>> process_match('*****205*R0*******')
    '*DWG*205*R0*.dwg'
    >>> process_match('*****205**R0******')
    '*DWG*205*R0*.dwg'
    >>> process_match('*PID-00205*')
    '*PID-00205*.dwg'
    """
    match = f"*{match}*.dwg"
    while "**" in match:
        match = match.replace("**", "*")
    if match[1].isdigit() or match == "*.dwg":
        match = f"*DWG{match}"
    return match


def get_files(match: str, source: Path) -> Iterable[Path]:
    """
    Returns a list of matching files if any.
    >>> list(get_files('*00205*R0*.dwg', Path('Q:/cad_drawings/contract/5300221014 SPP3 Caustic Ph 2')))
    [WindowsPath('5300221014-VWC-MS-DWG-00205-01-R0.dwg'), WindowsPath('5300221014-VWC-MS-DWG-00205-02-R0.dwg'), \
WindowsPath('5300221014-VWC-MS-DWG-00205-03-R0.dwg'), WindowsPath('5300221014-VWC-MS-DWG-00205-04-R0.dwg'), \
WindowsPath('5300221014-VWC-MS-DWG-00205-05-R0.dwg'), WindowsPath('5300221014-VWC-MS-DWG-00205-06-R0.dwg')]
    >>> list(get_files('*245*R0*.dwg', Path('Q:/cad_drawings/contract/5300221014 SPP3 Caustic Ph 2')))
    []
    """
    for file in source.glob(match):
        yield Path(file.name)


def get_file_count(match: str, source: Path) -> int:
    """How many files match the search string
    >>> get_file_count('*00205*R0*.dwg', Path('Q:/cad_drawings/contract/5300221014 SPP3 Caustic Ph 2'))
    6
    >>> get_file_count('*245*R0*.dwg', Path('Q:/cad_drawings/contract/5300221014 SPP3 Caustic Ph 2'))
    0
    """
    return sum(1 for _ in source.glob(match))


def get_latest(files: Iterable[Path]) -> Iterable[Path]:
    """Gets the latest drawing of each sheet"""
    str_files = iter((file.stem, file.suffix) for file in files)
    found: dict[str, list[str]] = {}
    for file, suffix in str_files:
        match = DWG.search(file)
        if not match:
            continue
        base, rev = match.groups()
        if base in found:
            cur = found[base][0]
            if rev.isdigit() and cur.isdigit():
                found[base][0] = str(max((int(rev), int(cur))))
            elif not rev.isdigit() and cur.isdigit():
                """Digit always bigger than letter"""
                found[base][0] = cur
            elif rev.isdigit() and not cur.isdigit():
                """Digit always bigger than letter"""
                found[base][0] = rev
            else:
                found[base][0] = max((rev, cur))
        else:
            found[base] = [rev, suffix]
    for k, v in found.items():
        yield Path(f"{k}-R{v[0]}").with_suffix(v[1])


def make_pdf(source: Path, scr: Path) -> None:
    """Creates the layout pdf of based on the sheet listed in the SRC file."""
    exe = get_accore()
    source = source.with_suffix(".dwg")
    subprocess.run(f'"{exe}" /i "{source}" /s "{scr}" /l "en-US"')


def get_accore() -> str:
    base = Path("C:/Program Files/Autodesk")
    temp = ""
    for folder in base.iterdir():
        if "AutoCAD" in folder.name:
            temp = folder.name
    return str(base / temp / "accoreconsole.exe")


def remove_plot_logs() -> None:
    for plot in (CWD / "plot.log", CWD / "hardcopy.log"):
        if plot.exists():
            plot.unlink()
