from __future__ import annotations

import os
from logging import INFO, basicConfig
from pathlib import Path

import click

from .main import main


@click.command()
@click.argument("file_url", type=str, required=False, default=None)
@click.option("-f", "--folder-url", type=str, required=False, default=None)
@click.option("-o", "--out-path", type=click.Path(), required=False, default=None)
@click.option("-p", "--privacy-scopes", type=str, required=False, default=None)
@click.option("--pdf/--no-pdf", default=True)
def cli(
    file_url: str | None = None,
    out_path: str | Path | None = None,
    folder_url: str | None = None,
    privacy_scopes: str | None = None,
    pdf: bool = True,
) -> None:
    basicConfig(level=INFO)
    if file_url is None:
        file_url = os.environ["LAB_STUDENT_SURVEY_FILE_URL"]
    if folder_url is None:
        folder_url = os.environ.get("LAB_STUDENT_SURVEY_FOLDER_URL")
    if out_path is None:
        out_path = "output.html"
    if privacy_scopes is not None:
        out_path = f"output.{privacy_scopes.replace(',', '_')}.html"
    main(
        file_url,
        folder_url=folder_url,
        out_path=out_path,
        privacy_scopes=privacy_scopes.split(",")
        if privacy_scopes is not None
        else None,
        pdf=pdf,
    )
