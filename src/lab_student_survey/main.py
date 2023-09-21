from logging import getLogger
from pathlib import Path

from pydrive2.drive import GoogleDrive
from pydrive2.files import GoogleDriveFile

from .analyze import analyze
from .gdrive import get_drive

LOG = getLogger(__name__)


def create_or_get_file(
    drive: GoogleDrive, name: str, folder_id: str, mimetype: str
) -> GoogleDriveFile:
    filelist = drive.ListFile(
        {"q": f"'{folder_id}' in parents and trashed=false"}
    ).GetList()
    file_candidates = [file for file in filelist if file["title"] == name]
    if file_candidates:
        return file_candidates[0]
    return drive.CreateFile(
        {
            "title": name,
            "mime_type": "text/html",
            "parents": [{"id": folder_id}],
        }
    )


def main(
    file_url: str,
    *,
    out_path: Path | str = "output.html",
    folder_url: str | None = None,
    pdf: bool = True,
) -> None:
    file_id = file_url.split("/")[-1].split("?")[0]
    drive = get_drive()
    in_file = drive.CreateFile({"id": file_id})
    csv_content = in_file.GetContentString(mimetype="text/csv")
    analyze(csv_content, out_path=out_path, pdf=pdf)

    folder_id = (
        in_file["parents"][0]["id"] if folder_url is None else folder_url.split("/")[-1]
    )
    out_file = create_or_get_file(drive, Path(out_path).name, folder_id, "text/html")
    out_file.SetContentFile(out_path)
    out_file.Upload()
    LOG.info(f"HTML saved to {out_file['alternateLink']}")

    if pdf:
        pdf_path = Path(out_path).with_suffix(".pdf")
        out_file = create_or_get_file(
            drive, pdf_path.name, folder_id, "application/pdf"
        )
        out_file.SetContentFile(pdf_path)
        out_file.Upload()
        LOG.info(f"PDF saved to {out_file['alternateLink']}")
