from click.testing import CliRunner

from lab_student_survey.cli import cli


def test_main() -> None:
    runner = CliRunner()
    runner.invoke(cli)
