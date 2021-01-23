"""Main entry point."""
from pathlib import Path
from typing import Optional, Tuple, Union

import click

from . import bbin, enums, utils


class Installable(click.ParamType):
    name = "installable"

    def convert(
        self,
        value: str,
        _: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> Tuple[enums.InstallType, Union[Path, str]]:
        if value.startswith("git+"):
            if not value.endswith(".git"):
                self.fail("Invalid git url")
            output = value[5:]
            return enums.InstallType.URL, output
        if utils.is_an_executable(Path(value)):
            return enums.InstallType.EXE, Path(value)
        return enums.InstallType.PKG, value


@click.group()
def main() -> None:
    """A binary package manager"""


@main.command()  # type: ignore
@click.argument("thing", type=Installable())
@click.option(
    "--action",
    default="move",
    type=click.Choice(["move", "symlink", "copy"], case_sensitive=False),
)
def install(thing: Tuple[enums.InstallType, Union[Path, str]], action: str) -> None:
    """Install a package"""
    if thing[0] == enums.InstallType.PKG:
        package_name = thing[1]
        assert isinstance(package_name, str)
        index = bbin.Index()
        url = index.get_url(package_name)
        if url is None:
            raise click.BadParameter("Invalid package name: package not found")
        index.install(index.build(index.download(package_name, url)), action.lower())
    elif thing[0] == enums.InstallType.URL:
        assert isinstance(thing[1], str)
        ...
    elif thing[0] == enums.InstallType.EXE:
        assert isinstance(thing[1], Path)
        ...


if __name__ == "__main__":
    main()
