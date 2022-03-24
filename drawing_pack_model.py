import glob
import os
import shutil
import subprocess
from pathlib import Path
from textwrap import dedent
from threading import Thread
from typing import List, Optional, Union

from PyPDF3 import PdfFileMerger, PdfFileReader

ROOT = Path(__file__).parent.absolute()
CWD = Path.cwd()


def parse_path(path: str, make_dir: bool = False) -> Path:
    """Returns an absolute path object.
    >>> parse_path('~/desktop')
    WindowsPath('C:/Users/david.weiss/desktop')
    >>> parse_path('Q:/cad_drawings/contract/*221014*')
    WindowsPath('Q:/cad_drawings/contract/5300221014 SPP3 Caustic Ph 2')
    """
    if path.startswith("~"):
        path = str(Path().home()) + path[1:]
    _path = Path(path)
    try:
        if make_dir:
            _path.mkdir(exist_ok=True, parents=True)
        elif not _path.exists():
            raise FileNotFoundError
    except OSError:
        _path = Path(glob.glob(path)[0])
    except FileNotFoundError:
        print(f"{path} does not exist")
        exit(1)
    return _path


def get_files(match: str, source: Path) -> List[Path]:
    """
    Returns a list of matching files if any.
    >>> get_files('*00205*R0*.dwg', Path('Q:/cad_drawings/contract/5300221014 SPP3 Caustic Ph 2'))
    [WindowsPath('5300221014-VWC-MS-DWG-00205-01-R0'), WindowsPath('5300221014-VWC-MS-DWG-00205-02-R0'), WindowsPath('5300221014-VWC-MS-DWG-00205-03-R0'), WindowsPath('5300221014-VWC-MS-DWG-00205-04-R0'), WindowsPath('5300221014-VWC-MS-DWG-00205-05-R0'), WindowsPath('5300221014-VWC-MS-DWG-00205-06-R0')]
    >>> get_files('*245*R0*.dwg', Path('Q:/cad_drawings/contract/5300221014 SPP3 Caustic Ph 2'))
    []
    """
    files = source.glob(match)
    files = [Path(file.stem) for file in files]
    if not files:
        return []
    return files


def get_latest(files: list[Path]) -> list[Path]:
    """Gets the latest drawing of each sheet

    Each drawing is 33 character.
    The first 30 are the drawing number, the last 3 are the revision.
    """
    str_files = [file.name for file in files]
    found: dict[str, str] = {}
    for file in str_files:
        base, rev = file[:30], file[32:]
        if base in found:
            cur = found[base]
            if rev.isdigit() and cur.isdigit():
                found[base] = str(max((int(rev), int(cur))))
            elif not rev.isdigit() and cur.isdigit():
                """Digit always bigger than letter"""
                found[base] = cur
            elif rev.isdigit() and not cur.isdigit():
                """Digit always bigger than letter"""
                found[base] = rev
            else:
                found[base] = max((rev, cur))
        else:
            found[base] = rev
    return [Path(f"{k}-R{v}") for k, v in found.items()]


def create_temp_files(files: List[Path], source: Path, dest: Path) -> None:
    for file in files:
        shutil.copy(source / file.with_suffix(".dwg"), dest)


def make_pdf(drawing: Path) -> None:
    base = Path("C:/Program Files/Autodesk")
    temp = ""
    for folder in base.iterdir():
        if "AutoCAD" in folder.name:
            temp = folder.name
    exe = str(base / temp / "accoreconsole.exe")
    scr = str(ROOT / "pdfgen11x17model.scr")
    drawing = drawing.with_suffix(".dwg")
    subprocess.run(f'"{exe}" /i "{drawing}" /s "{scr}" /l "en-US"')


def merge_pdf(files: List[Path], source: Path, output: Path) -> None:
    merged = PdfFileMerger(strict=False)
    for pdf in files:
        title = str(pdf)
        pdf = pdf.with_name(pdf.name + "-Model.pdf")
        try:
            merged.append(PdfFileReader(str(source / pdf)), title)
        except FileNotFoundError:
            print(f"Could not find {pdf}. File skipped")
    merged.write(str(source / output.with_suffix(".pdf")))


def remove_temp(files: List[Path], source: Path, remove_dwg: bool) -> None:
    for file in files:
        pdf = source / file.with_name(file.name + "-Model.pdf")
        try:
            pdf.unlink()
        except FileNotFoundError:
            pass
        if remove_dwg:
            dwg = source / file.with_suffix(".dwg")
            dwg.unlink()
    try:
        plot = CWD / "plot.log"
        plot.unlink()
    except (FileNotFoundError, PermissionError):
        pass


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


def main(
    match: str,
    source: Path,
    dest: Optional[Path] = None,
    output: Optional[Path] = None,
    latest: bool = False,
    view: bool = False,
) -> Union[Path, str]:
    match = process_match(match)
    remove_dwg = False
    drawings = get_files(match, source)
    if not drawings:
        return f"No matching files for {match} in {source}"
    if latest:
        drawings = get_latest(drawings)
    if not output:
        basename = drawings[0].name  # Name of the first drawing
        # 5300XXXXXX-VWC-MS-DWG-XXXXX-R?-ALL
        output = Path(basename[:27] + basename[30:] + "-ALL")
    if dest:
        create_temp_files(drawings, source, dest)
        remove_dwg = True
    else:
        dest = source
    threads: list[Thread] = []
    for drawing in drawings:
        t = Thread(target=make_pdf, args=(dest / drawing,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    merge_pdf(drawings, dest, output)
    remove_temp(drawings, dest, remove_dwg)
    if view:
        os.startfile(output)
    return dest / output.with_suffix(".pdf")
