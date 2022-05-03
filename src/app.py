from pathlib import Path
from typing import Iterable, Optional

from src import layouts, model, tools


def main(
    match: str,
    source: Path,
    dest: Optional[Path] = None,
    output: Optional[str] = None,
    paper: bool = False,
    latest: bool = True,
    keep: bool = False,
    del_source: bool = False,
    view: bool = False,
) -> str:
    """Creates PDF files of the specified drawings.

    Searches the <source> directory for any files matching the MATCH parameter.

    If a <dest> directory is specified that is where the created PDFs will be stored.
    Otherwise they will be placed in the same directory as the <source>.

    If <output> is specified this will be the name of the combined PDF otherwise the
    default naming will be used.
    """
    if source.is_dir():
        clean_match = tools.process_match(match)
        matched_drawings = tools.get_files(clean_match, source)
        if matched_drawings is None:
            return f"No matching files for '{match}' in '{source}'"
        source_dir = source
    else:
        if not source.exists():
            return f"Could not find '{source}'"
        matched_drawings = (source,)  # For the rest to work, this needs to be iterable.
        source_dir = source.parent
    if not dest:
        dest = source_dir
    if latest:
        matched_drawings = tools.get_latest(matched_drawings)
    total_files, matched_drawings = get_total(matched_drawings)
    if paper:
        out_files = get_output_files(total_files, dest, output)
        return "\n".join(
            str(
                layouts.main(
                    source=source / matched,
                    destination=dest,
                    output=out,
                    view=view,
                    del_source=del_source,
                    keep_individual=keep,
                )
            )
            for matched, out in zip(matched_drawings, out_files)
        )
    else:
        out = Path(output) if output else None
        return str(
            model.main(
                drawings=matched_drawings,
                source=source,
                sht_count=total_files,
                dest=dest,
                output=out,
                view=view,
                remove_dwg=del_source,
            )
        )


def get_total(drawings: Iterable[Path]) -> tuple[int, Iterable[Path]]:
    """Finds then length of the iterable and returns that and the iterable.
    Example:
        >>> a = get_total((Path() for _ in range(2)))
        >>> a[0]
        2
        >>> [str(item) for item in a[1]]
        ['.', '.']
    """
    drawings = list(drawings)
    return len(drawings), iter(drawings)


def get_output_files(
    total: int, destination: Path, name: Optional[str]
) -> Iterable[Optional[Path]]:
    """Generate an output file name for each match.
    Examples:
        >>> list(get_output_files(3, Path(), None))
        [None, None, None]
        >>> [str(file) for file in get_output_files(3, Path(), "file")]
        ['file.pdf', 'file(1).pdf', 'file(2).pdf']
    """
    if name is None:
        for _ in range(total):
            yield None
    else:
        for idx in range(total):
            if idx == 0:
                yield (destination / name).with_suffix(".pdf")
            else:
                yield (destination / f"{name}({idx})").with_suffix(".pdf")
