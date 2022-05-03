from pathlib import Path
from typing import Optional

import click

from src import app


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument(
    "match",
)
@click.argument(
    "source",
    type=click.Path(exists=True, path_type=Path),
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
    help="Flag to keep the individual sheets created along with the combined PDF (layout option only).",
)
@click.option(
    "-x",
    "--del_source",
    is_flag=True,
    default=False,
    help="Flag to delete the source file when done.",
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
    dest: Optional[Path],
    output: Optional[str],
    paper: bool,
    latest: bool,
    keep: bool,
    del_source: bool,
    view: bool,
) -> None:
    """Creates PDF files of the specified drawings.

    Searches the <source> directory for any files matching the MATCH parameter.

    If a <dest> directory is specified that is where the created PDFs will be stored.
    Otherwise they will be placed in the same directory as the <source>.

    If <output> is specified this will be the name of the combined PDF otherwise the
    default naming will be used.
    """
    result = app.main(
        match=match,
        source=source,
        dest=dest,
        output=output,
        paper=paper,
        latest=latest,
        keep=keep,
        del_source=del_source,
        view=view,
    )
    print(result)


if __name__ == "__main__":
    main()
