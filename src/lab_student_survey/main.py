from logging import getLogger
from pathlib import Path

from .analyze import analyze
from .gdrive import get_drive

LOG = getLogger(__name__)


def main(file_url: str, *, out_path: Path | str = "output.html") -> None:
    file_id = file_url.split("/")[-1].split("?")[0]
    drive = get_drive()
    in_file = drive.CreateFile({"id": file_id})
    csv_content = in_file.GetContentString(mimetype="text/csv")
    analyze(csv_content, out_path=out_path)

    filelist = drive.ListFile(
        {"q": f"'{in_file['parents'][0]['id']}' in parents and trashed=false"}
    ).GetList()
    out_file_candidates = [
        file for file in filelist if file["title"] == Path(out_path).name
    ]
    if out_file_candidates:
        LOG.info("Updating existing file")
        out_file = out_file_candidates[0]
    else:
        LOG.info("Creating new file")
        out_file = drive.CreateFile(
            {
                "title": Path(out_path).name,
                "mime_type": "text/html",
                "parents": [{"id": in_file["parents"][0]["id"]}],
            }
        )
    out_file.SetContentFile(out_path)
    out_file.Upload()
    LOG.info(f"Output saved to {out_file['alternateLink']}")
