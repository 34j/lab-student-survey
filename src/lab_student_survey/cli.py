import os
from logging import INFO, basicConfig

import click

from .main import main


@click.command()
@click.argument("file_url", type=str, required=False, default=None)
def cli(file_url: str | None = None) -> None:
    basicConfig(level=INFO)
    if file_url is None:
        file_url = os.environ["LABO_STUDENT_SURVEY_FILE_URL"]
    main(file_url, folder_url=os.environ.get("LABO_STUDENT_SURVEY_FOLDER_URL"))
    click.echo("Output saved to output.html")
