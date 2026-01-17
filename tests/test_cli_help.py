from __future__ import annotations

import pytest

from generate_prompts import __version__, build_arg_parser


def test_help_runs_without_error(capsys) -> None:
    parser = build_arg_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--help"])
    assert exc.value.code == 0

    captured = capsys.readouterr()
    assert "generate_prompts" in captured.out
    assert "--input" in captured.out
    assert "--output" in captured.out


def test_version_outputs_version(capsys) -> None:
    parser = build_arg_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--version"])
    assert exc.value.code == 0

    captured = capsys.readouterr()
    assert __version__ in captured.out
