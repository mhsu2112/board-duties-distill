"""T0 smoke tests: the CLI surface is registered and importable."""

from __future__ import annotations

import cli


def test_cli_app_exists() -> None:
    assert cli.app is not None


def test_all_commands_registered() -> None:
    names = {command.name for command in cli.app.registered_commands}
    expected = {
        "validate-fixtures",
        "run-fixture",
        "render-package",
        "verify",
        "eval-fixture",
        "import-inventory",
    }
    assert expected <= names
