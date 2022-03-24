from pathlib import Path

import click

import drawing_pack_layouts
import drawing_pack_model
import drawing_pack_tools


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument(
    "match",
)
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    metavar="<source>",
)
@click.option(
    "-d",
    "--dest",
    type=click.Path(file_okay=False, path_type=Path),
    metavar="<dest>",
    help="Path to destination folder. New folders will be created.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    metavar="<output>",
    help="Filename of combined PDF.",
)
@click.option(
    "-p",
    "--paper",
    is_flag=True,
    help="Flag to select paperspace sheets instead of modelspace.",
)
@click.option(
    "-l",
    "--latest",
    is_flag=True,
    help="Flag to get the latest revision of each drawing matched.",
)
@click.option(
    "-k",
    "--keep",
    is_flag=True,
    help="Flag to keep the individual sheets created along with the combined PDF.",
)
@click.option(
    "-v",
    "--view",
    is_flag=True,
    help="Flag to open the combined PDF when finished.",
)
def main(
    match: str,
    source: Path,
    dest: Path,
    output: Path,
    paper: bool,
    latest: bool,
    keep: bool,
    view: bool,
) -> Path | str:
    """Creates PDF files of the specified drawings.

    Searches the <source> directory for any files matching the MATCH parameter.

    If a <dest> directory is specified that is where the created PDFs will be stored.
    Otherwise they will be placed in the same directory as the <source>.

    If <output> is specified this will be the name of the combined PDF otherwise the
    default naming will be used.

    \b
    \t5300XXXXXX-VWC-MS-DWG-YYYYY-ALL.pdf for modelspace drawings
    \t5300XXXXXX-VWC-MS-DWG-YYYYY-01_ZZ-RX.pdf for paperspace drawings


    """
    clean_match = drawing_pack_tools.process_match(match)
    matched_drawings = drawing_pack_tools.get_files(clean_match, source)
    if not matched_drawings:
        return f"No matching files for {match} in {source}"
    if latest:
        matched_drawings = drawing_pack_tools.get_latest(matched_drawings)
        # Handle this for paperspace

    if paper:
        return drawing_pack_layouts.main(source, dest, output, view)
    return drawing_pack_model.main(match, source, dest, output, latest, view)


if __name__ == "__main__":
    main()
