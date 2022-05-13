import os
import re
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Iterable, Optional

from PyPDF3 import PdfFileMerger, PdfFileReader

from src import ROOT
from src import tools as tools

# Matches sheets (See clean_sheet_name) to get the sheet and rev. 1-R0 -> (1)(-R0)
SHEET_NAME = re.compile(r"-?(\d+)(.*)")


def main(
    source: Path,
    destination: Optional[Path],
    output: Optional[Path] = None,
    view: bool = False,
    del_source: bool = False,
    keep_individual: bool = False,
) -> Path:
    """Convert the <source> file to pdfs."""
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
    sheets, qty = get_layouts(source)
    fill = max((2, len(str(qty))))

    base_scr = (ROOT / "pdfgen11x17layout.scr").read_text().splitlines()

    scrs = process_sheets(sheets, source, destination, base_scr)
    temp_files = [rename_file(source, scr, fill) for scr in scrs]
    merge(temp_files, output)

    if del_source:
        remove_temp((source,))
    if not keep_individual:
        remove_temp(temp_files)

    remove_temp(list(scrs))
    if view:
        os.startfile(output)
    tools.remove_plot_logs()
    return output


def get_base_name(source: Path, sheet_count: int) -> str:
    """Returns the name of the source file removing multi sheet reference as needed"""
    if sheet_count == 1:
        return source.stem
    # Default format 5300XXXXXX-VWC-MS-DWG-YYYYY
    return source.name[:27]


def process_sheets(
    sheets: Iterable[str], source: Path, dest: Path, base_scr: list[str]
) -> list[Path]:
    """Creates the PDFs for all sheets"""
    scrs: list[Path] = []
    threads: list[threading.Thread] = []
    for idx, sheet in enumerate(sheets):
        scrs.append(dest / f"scr{idx}.scr")
        scr = base_scr[:]
        scr[2] = f'"{sheet}"'
        (dest / f"scr{idx}.scr").write_text("\n".join(scr))
        t = threading.Thread(target=tools.make_pdf, args=(source, dest / f"scr{idx}"))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    return scrs


def rename_file(source: Path, scr: Path, fill: int = 2) -> Path:
    """Renames the PDF to remove extra sheet references"""
    parent = source.parent
    orig_name = source.stem
    with scr.open() as f:
        sheet = f.readlines()[2].strip().replace('"', "")
    pdf = source.with_name(f"{orig_name}-{sheet}.pdf")
    sheet = clean_sheet_name(sheet, fill)
    new_name = f"{pdf.stem[:27]}{sheet}.pdf"
    return pdf.replace(parent / new_name)


def merge(files: Iterable[Path], output: Path) -> None:  # pragma: no cover
    """Merges the individual PDFs into one."""
    merged = PdfFileMerger(strict=False)
    for file in sorted(files):
        title = file.stem
        merged.append(PdfFileReader(str(file)), title)
    merged.write(str(output))


def remove_temp(files: Iterable[Path]) -> None:  # pragma: no cover
    """Deletes all temp files"""
    for file in files:
        try:
            file.unlink()
        except FileNotFoundError:
            continue


def get_layouts(drawing: Path) -> tuple[Iterable[str], int]:
    """Opens the drawing and returns a list of all sheet names"""
    # odafc.win_exec_path = "./ODA/ODAFileConverter.exe"
    # doc = odafc.readfile(str(drawing))
    # return doc.layout_names_in_taborder()[1:]
    base = Path(__file__).parent
    layouts = base / "layouts.txt"
    scr = base / "sheetlist.scr"
    scr.write_text(
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
    subprocess.run(f'"{tools.get_accore()}" /i "{str(drawing)}" /s "{scr}" /l "en-US"')
    with open(layouts) as f:
        sheets = (line.strip() for line in f.readlines() if line.strip() != "Model")
        f.seek(0)
        qty = sum(1 for line in f if line.strip() != "Model")
    layouts.unlink()
    scr.unlink()
    return sheets, qty


def clean_sheet_name(sheet: str, fill: int = 2) -> str:
    """Cleans the sheet names so they are the same
    Examples:
        >>> clean_sheet_name("1-R0", 2)
        '-01-R0'
        >>> clean_sheet_name("-6-R0", 2)
        '-06-R0'
        >>> clean_sheet_name("-10-R0", 2)
        '-10-R0'
        >>> clean_sheet_name("10-R0", 2)
        '-10-R0'
    """
    sheet_data = SHEET_NAME.search(sheet)
    if sheet_data is None:
        return ""
    sheet_num = sheet_data.group(1)
    sheet_rev = sheet_data.group(2)
    return f"-{sheet_num:0>{fill}}{sheet_rev}"
