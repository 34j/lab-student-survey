import re

from click.testing import CliRunner

from lab_student_survey.cli import cli


def test_main() -> None:
    runner = CliRunner()
    result = runner.invoke(cli)
    try:
        assert result.exit_code == 0
    except AssertionError:
        # hide URL in error message
        raise AssertionError(
            re.sub(r"https://[^\s]+", "https://...", result.output)
        ) from None
