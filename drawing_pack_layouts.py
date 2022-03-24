import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Optional, Sequence, Tuple

from PyPDF3.merger import PdfFileMerger
from PyPDF3.pdf import PdfFileReader

import drawing_pack_model

CWD = Path.cwd()


def main(
    source: Path,
    destination: Optional[Path],
    output: Optional[Path],
    view: bool = False,
) -> Path:
    """Convert the <source> file to pdfs."""
    print(source, destination, output, view)
    del_source = False
    if destination is None:
        destination = source.parent
    elif destination != source.parent:
        shutil.copyfile(source, destination / source.name)
        source = destination / source.name
        del_source = True
    if output is None:
        output = source.with_suffix(".pdf")
    else:
        output = destination / output.with_suffix(".pdf")
    sheets = get_layouts(source)

    with open("pdfgen11x17layout.scr") as file:
        base_scr = file.readlines()

    temp_files, scrs = process_sheets(sheets, source, destination, base_scr)

    merge(temp_files, output)

    if del_source:
        scrs.append(source)

    remove_temp(scrs)
    if view:
        os.startfile(output)
    return output


def get_base_name(source: Path, sheet_count: int) -> str:
    """Returns the name of the source file removing multi sheet reference as needed"""
    if sheet_count == 1:
        return source.name
    # Default format 5300XXXXXX-VWC-MS-DWG-YYYYY
    return source.name[:27]


def process_sheets(
    sheets: Sequence[str], source: Path, destination: Path, base_scr: list[str]
) -> Tuple[list[Path], list[Path]]:
    """Creates the PDFs for all sheets"""
    base_name = get_base_name(source, len(sheets))
    temp_files: list[Path] = []
    scrs: list[Path] = []
    threads: list[threading.Thread] = []
    for idx, sheet in enumerate(sheets):
        temp_files.append(
            destination / f"{base_name}{'-' if len(sheets) == 1 else ''}{sheet}.pdf"
        )
        scrs.append(destination / f"scr{idx}.scr")
        scr = base_scr[:]
        scr[2] = f'"{sheet}"\n'
        with open(destination / f"scr{idx}.scr", "w+") as file:
            file.writelines(scr)
        t = threading.Thread(target=make_pdf, args=(source, destination / f"scr{idx}"))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    if source.stem != base_name:
        for scr in scrs:
            rename_file(source, base_name, scr)

    return temp_files, scrs


def get_accore() -> str:
    base = Path("C:/Program Files/Autodesk")
    temp = ""
    for folder in base.iterdir():
        if "AutoCAD" in folder.name:
            temp = folder.name
    return str(base / temp / "accoreconsole.exe")


def make_pdf(source: Path, scr: Path) -> None:
    """Creates the layout pdf of based on the sheet listed in the SRC file."""
    exe = get_accore()
    source = source.with_suffix(".dwg")
    subprocess.run(f'"{exe}" /i "{source}" /s "{scr}" /l "en-US"')


def rename_file(source: Path, base_name: str, scr: Path) -> None:
    """Renames the PDF to remove extra sheet references"""
    parent = source.parent
    orig_name = source.stem
    with scr.open() as f:
        sheet = f.readlines()[2].strip().replace('"', "")
    pdf = source.with_name(f"{orig_name}-{sheet}.pdf")
    new_name = f"{pdf.stem[:27]}{sheet}.pdf"
    pdf.replace(parent / new_name)


def merge(files: list[Path], output: Path) -> None:
    """Merges the individual PDFs into one."""
    merged = PdfFileMerger(strict=False)
    for file in files:
        title = file.stem
        merged.append(PdfFileReader(str(file)), title)
    merged.write(str(output))


def remove_temp(files: list[Path]) -> None:
    """Deletes all temp files"""
    for file in files:
        try:
            file.unlink()
        except FileNotFoundError:
            continue
    plot = CWD / "plot.log"
    if plot.exists():
        plot.unlink()


def get_layouts(drawing: Path) -> list[str]:
    """Opens the drawing and returns a list of all sheet names"""
    # odafc.win_exec_path = "./ODA/ODAFileConverter.exe"
    # doc = odafc.readfile(str(drawing))
    # return doc.layout_names_in_taborder()[1:]
    base = Path(__file__).parent
    layouts = base / "layouts.txt"
    scr = base / "sheetlist.scr"
    with open(scr, "w+") as f:
        f.write(
            f"""
(if (setq des (open "{layouts.as_posix()}" "w"))
  (progn
    (setq items (dictsearch (namedobjdict) "ACAD_LAYOUT"))
    (foreach layout items (
        if (= (nth 0 layout) 3)
        (write-line (cdr layout) des)
        )
    )
    (close des)
  )
)
"""
        )
    subprocess.run(f'"{get_accore()}" /i "{str(drawing)}" /s "{scr}" /l "en-US"')
    with open(layouts) as f:
        sheets = [sheet.strip() for sheet in f.readlines() if sheet.strip() != "Model"]
    layouts.unlink()
    scr.unlink()
    return sheets
