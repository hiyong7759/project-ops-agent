from __future__ import annotations

import subprocess
from pathlib import Path

from .models import CommandResult, CommandsSettings


class CommandRunner:
    def __init__(self, commands: CommandsSettings) -> None:
        self.commands = commands

    def install_commands(self) -> list[str]:
        return [self.commands.install] if self.commands.install else []

    def verification_commands(self) -> list[str]:
        return [command for command in (self.commands.lint, self.commands.test) if command]

    def run_many(self, commands: list[str], cwd: Path) -> list[CommandResult]:
        return [self.run(command, cwd) for command in commands]

    def run(self, command: str, cwd: Path) -> CommandResult:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            text=True,
            capture_output=True,
            check=False,
        )
        return CommandResult(
            command=command,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )

