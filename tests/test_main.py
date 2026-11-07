from pathlib import Path
from unittest.mock import Mock

import pandas as pd
from click.testing import CliRunner
from matplotlib.figure import Figure

import lab_student_survey.analyze as analyze_module
import lab_student_survey.cli as cli_module
import lab_student_survey.gdrive as gdrive_module
import lab_student_survey.main as main_module
from lab_student_survey.analyze import analyze, export_multiple_frames_to_html, find_best_k
from lab_student_survey.cli import cli
from lab_student_survey.main import create_or_get_file, get_file, main


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0


def test_cli_callback(monkeypatch) -> None:
    called = Mock()
    monkeypatch.setattr(cli_module, "main", called)
    monkeypatch.setenv("LAB_STUDENT_SURVEY_FILE_URL", "https://drive/file-id")

    callback = cli.callback
    assert callback is not None
    callback()

    called.assert_called_once_with(
        "https://drive/file-id",
        folder_url=None,
        out_path="output.html",
        privacy_scopes=None,
        pdf=True,
    )


def test_gdrive_authentication(monkeypatch, tmp_path: Path) -> None:
    auth = Mock()
    monkeypatch.setattr(gdrive_module, "GoogleAuth", lambda **_: auth)
    monkeypatch.setenv("GDRIVE_SERVICE_SECRETS", "{}")
    monkeypatch.chdir(tmp_path)

    assert gdrive_module.get_auth() is auth
    assert (tmp_path / "service-secrets.json").read_text() == "{}"
    auth.ServiceAuth.assert_called_once()


def test_drive_file_helpers() -> None:
    candidate = {"title": "report"}
    drive = Mock()
    drive.ListFile.return_value.GetList.return_value = [candidate]

    assert get_file(drive, "report", "folder") is candidate
    assert create_or_get_file(drive, "report", "folder", "text/html") is candidate

    drive.ListFile.return_value.GetList.return_value = []
    created = {"title": "new"}
    drive.CreateFile.return_value = created
    assert create_or_get_file(drive, "new", "folder", "text/html") is created
    drive.CreateFile.assert_called_once_with({
        "title": "new",
        "mime_type": "text/html",
        "parents": [{"id": "folder"}],
    })


def test_main(monkeypatch, tmp_path: Path) -> None:
    input_file = Mock()
    input_file.__getitem__ = Mock(return_value=[{"id": "folder"}])
    input_file.GetContentString.return_value = "timestamp,privacy,supervisor\n"
    drive = Mock()
    drive.CreateFile.return_value = input_file
    drive.ListFile.return_value.GetList.return_value = []
    monkeypatch.setattr(main_module, "get_drive", lambda: drive)
    analyze_mock = Mock()
    monkeypatch.setattr(main_module, "analyze", analyze_mock)
    monkeypatch.setattr(main_module, "IS_CI", True)
    monkeypatch.chdir(tmp_path)

    main("https://drive/file-id", pdf=False)

    analyze_mock.assert_called_once_with(
        "timestamp,privacy,supervisor\n",
        out_path="output.html",
        pdf=False,
        privacy_scopes=None,
    )
    assert drive.CreateFile.call_count == 2


def test_analyze_and_export(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    csv_content = pd.DataFrame({
        "タイムスタンプ": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "公開範囲": ["public", "public", "public"],
        "supervisor": ["A", "B", "C"],
        "q1": ["全く当てはまる", "当てはまる", "どちらともいえない"],
        "q2": ["当てはまる", "どちらともいえない", "あまり当てはまらない"],
    }).to_csv(index=False)
    pd.DataFrame(
        {"group": [None, "group", "group"], "higher_is_better": [False, True, True]},
        index=["公開範囲", "q1", "q2"],
    ).to_csv("metadata.csv")
    export_mock = Mock()
    monkeypatch.setattr(analyze_module, "export_multiple_frames_to_html", export_mock)

    analyze(csv_content, pdf=False)
    best_k, scores, _ = find_best_k(pd.DataFrame([[0.0, 1.0], [1.0, 0.0]]), max_k=2)

    assert best_k in {1, 2}
    assert len(scores) == 2
    export_mock.assert_called_once()

    output_path = tmp_path / "output.html"
    export_multiple_frames_to_html(["title", pd.DataFrame({"value": [1]}), Figure()], output_path)
    assert output_path.exists()
