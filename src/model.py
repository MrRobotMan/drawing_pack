import os
import shutil
from pathlib import Path
from threading import Thread
from typing import Iterable, List, Optional, Union

from PyPDF3 import PdfFileMerger, PdfFileReader

from src import ROOT
from src import tools as tools


def main(
    drawings: Iterable[Path],
    source: Path,
    sht_count: int,
    dest: Optional[Path] = None,
    output: Optional[Path] = None,
    view: bool = False,
    remove_dwg: bool = False,
) -> Union[Path, str]:
    drawings = list(drawings)
    if dest:
        create_temp_files(drawings, source, dest)
        remove_dwg = True
    else:
        dest = source
    if not output:
        basename = drawings[0].stem  # Name of the first drawing
        # 5300XXXXXX-VWC-MS-DWG-XXXXX-R?-ALL
        output = dest / f"{basename[:27]}-01_{sht_count:0>2}{basename[30:]}.pdf"
    else:
        output = dest / output.with_suffix(".pdf")
    process_sheets(drawings, dest)
    merge_pdf(drawings, dest, output)
    remove_temp(drawings, dest, remove_dwg)
    if view:
        os.startfile(output)
    tools.remove_plot_logs()
    return output


def process_sheets(drawings: Iterable[Path], dest: Path) -> None:
    threads: list[Thread] = []
    scr = str(ROOT / "pdfgen11x17model.scr")
    for drawing in drawings:
        t = Thread(target=tools.make_pdf, args=(dest / drawing, scr))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


def create_temp_files(files: List[Path], source: Path, dest: Path) -> None:
    for file in files:
        shutil.copy(source / file.with_suffix(".dwg").name, dest)


def merge_pdf(files: List[Path], source: Path, output: Path) -> None:
    merged = PdfFileMerger(strict=False)
    for pdf in files:
        title = str(pdf)
        pdf = pdf.with_name(pdf.stem + "-Model.pdf")
        try:
            merged.append(PdfFileReader(str(source / pdf)), title)
        except FileNotFoundError:
            print(f"Could not find {pdf}. File skipped")
    merged.write(str(output.with_suffix(".pdf")))


def remove_temp(files: List[Path], source: Path, remove_dwg: bool) -> None:
    for file in files:
        pdf = source / f"{file.stem}-Model.pdf"
        try:
            pdf.unlink()
        except FileNotFoundError:
            pass
        if remove_dwg:
            dwg = source / file.with_suffix(".dwg")
            dwg.unlink()
