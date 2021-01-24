"""Git interaction"""
import shutil
from os import getenv
from pathlib import Path
from typing import Any, Optional

from . import interface, utils

GIT = shutil.which("git")

if not GIT:
    callback = Path(getenv("BBIN_GIT_CALLBACK", "/usr/bin/git"))
    if getenv("BBIN_NO_WARN_GIT") != "1":
        interface.warn(
            "You do not have git installed! "
            f"BBin will use the default `{callback}` callback. "
            "You can change this by setting `BBIN_GIT_CALLBACK` to your Git executable.\n"
            "You can disable this warning in the future by setting `BBIN_NO_WARN_GIT` to `1`."
        )


def clone(
    url: str,
    directory: Optional[str] = None,
    silent: bool = True,
    with_spinner: bool = True,
    **kwargs: Any,  # type: ignore
) -> None:
    """Clone a repository using the given URL"""
    args = [GIT, "clone", url]
    if directory is not None:
        assert isinstance(directory, str)
        args.append(directory)
    if silent:
        args.append("--quiet")
    utils.run_subprocess(
        args, loading_text=f"Cloning {url}", with_spinner=with_spinner, **kwargs  # type: ignore
    )


def pull(
    repo: str,
    silent: bool = True,
    with_spinner: bool = False,
    **kwargs: Any,  # type: ignore
) -> None:
    """Update a repository"""
    args = [GIT, "-C", repo, "pull"]
    if silent:
        args.append("--quiet")
    utils.run_subprocess(
        args, loading_text="Pulling {repo}", with_spinner=with_spinner, **kwargs
    )


def checkout(
    repo: str, tag: str, silent: bool = True, with_spinner: bool = False
) -> None:
    args = [GIT, "-C", repo, "checkout", tag]
    if silent:
        args.append("--quiet")
    utils.run_subprocess(
        args,
        loading_text=f"Switching branch to {tag} at {repo}",
        with_spinner=with_spinner,
    )
