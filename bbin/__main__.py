"""Main entry point."""
import os
import os.path
from pathlib import Path
from typing import Optional, Tuple, Union

import click

from . import bbin, enums, git, utils


class Installable(click.ParamType):
    name = "installable"

    def convert(
        self,
        value: str,
        _: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> Tuple[enums.InstallType, str]:
        if value.startswith("git+"):
            if not value.endswith(".git"):
                self.fail("Invalid git url")
            output = value[5:]
            return enums.InstallType.URL, output
        if utils.is_an_executable(Path(value)):
            return enums.InstallType.EXE, value
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
@click.option(
    "--index-path",
    default=lambda: os.getenv("BBIN_PATH", os.path.expanduser("~/.config/bbin")),
)
@click.option(
    "--bin-path", default=lambda: os.getenv("BIN_PATH", os.path.expanduser("~/bin"))
)
@click.option(
    "--app-path", default=lambda: os.getenv("APP_PATH", os.path.expanduser("~/app"))
)
def install(
    thing: Tuple[enums.InstallType, str],
    action: str,
    index_path: str,
    bin_path: str,
    app_path: str,
) -> None:
    """Install a package. THING must be a URL, a path to an executable, or a package's name."""
    index = bbin.Index(bbin_path=index_path, bin_path=bin_path, app_path=app_path)

    if thing[0] == enums.InstallType.PKG:
        package_name = thing[1]
        assert isinstance(package_name, str)
        url = index.get_url(package_name)
        if url is None:
            raise click.BadParameter("Invalid package name: package not found")

        index.install(index.build(index.download(package_name, url)), action.lower())
    elif thing[0] == enums.InstallType.URL:
        assert isinstance(thing[1], str)
        url = thing[1]
        package_name = utils.get_folder_name_from_url(url)

        index.install(index.build(index.download(package_name, url)), action.lower())

    elif thing[0] == enums.InstallType.EXE:
        assert isinstance(thing[1], str)
        index.install(thing[1], action.lower())


if __name__ == "__main__":
    main()
