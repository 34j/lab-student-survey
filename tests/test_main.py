from click.testing import CliRunner

from lab_student_survey.cli import cli


def test_main() -> None:
    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0
