from __future__ import annotations

import os
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydrive2.drive import GoogleDrive
    from pydrive2.files import GoogleDriveFile

from .analyze import analyze
from .gdrive import get_drive

IS_CI = os.environ.get("GITHUB_ACTIONS") == "true"

LOG = getLogger(__name__)


def get_file(drive: GoogleDrive, name: str, folder_id: str) -> GoogleDriveFile | None:
    """Find a file by name in a Google Drive folder.

    Returns:
        The matching file, or None when no file matches.

    """
    filelist = drive.ListFile({"q": f"'{folder_id}' in parents and trashed=false"}).GetList()
    file_candidates = [file for file in filelist if file["title"] == name]
    if file_candidates:
        return file_candidates[0]
    return None


def create_or_get_file(
    drive: GoogleDrive, name: str, folder_id: str, mimetype: str
) -> GoogleDriveFile:
    """Find a file by name or create it in a Google Drive folder.

    Returns:
        The existing or newly created file.

    """
    file = get_file(drive, name, folder_id)
    if file is not None:
        return file
    return drive.CreateFile({
        "title": name,
        "mime_type": mimetype,
        "parents": [{"id": folder_id}],
    })


def main(
    file_url: str,
    *,
    out_path: Path | str = "output.html",
    folder_url: str | None = None,
    pdf: bool = True,
    privacy_scopes: list[str] | None = None,
) -> None:
    """Download, analyze, and publish a survey spreadsheet."""
    file_id = file_url.rsplit("/", maxsplit=1)[-1].split("?", maxsplit=1)[0]
    drive = get_drive()
    in_file = drive.CreateFile({"id": file_id})
    csv_content = in_file.GetContentString(mimetype="text/csv")

    for n in ["metadata.csv", "metadata_group_name.csv"]:
        metadata_file = get_file(drive, n, in_file["parents"][0]["id"])
        if metadata_file is not None:
            LOG.info("Downloading %s...", n)
            metadata_file.GetContentFile(n)

    analyze(csv_content, out_path=out_path, pdf=pdf, privacy_scopes=privacy_scopes)

    folder_id = in_file["parents"][0]["id"] if folder_url is None else folder_url.split("/")[-1]
    out_file = create_or_get_file(drive, Path(out_path).name, folder_id, "text/html")
    out_file.SetContentFile(out_path)
    out_file.Upload()
    if not IS_CI:
        LOG.info("✔✨HTML saved to %s and %s", out_file["alternateLink"], out_path)
    else:
        LOG.info("✔✨HTML saved")

    if pdf:
        pdf_path = Path(out_path).with_suffix(".pdf")
        out_file = create_or_get_file(drive, pdf_path.name, folder_id, "application/pdf")
        out_file.SetContentFile(pdf_path)
        out_file.Upload()
        if not IS_CI:
            LOG.info("✔✨PDF saved to %s and %s", out_file["alternateLink"], pdf_path)
        else:
            LOG.info("✔✨PDF saved")
