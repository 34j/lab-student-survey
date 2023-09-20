from pathlib import Path

from .analyze import analyze
from .gdrive import get_drive


def main(file_url: str, *, out_path: Path | str = "output.html") -> None:
    file_id = file_url.split("/")[-1].split("?")[0]
    drive = get_drive()
    in_file = drive.CreateFile({"id": file_id})
    csv_content = in_file.GetContentString(mimetype="text/csv")
    analyze(csv_content, out_path=out_path)
    out_file = drive.CreateFile(
        {
            "title": Path(out_path).name,
            "mime_type": "text/html",
            "parents": [{"id": in_file["parents"][0]["id"]}],
        }
    )
    out_file.SetContentFile(out_path)
    out_file.Upload()
