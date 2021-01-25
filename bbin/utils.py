"""Utilities."""

import hashlib
import os
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any, List, Optional

import halo  # type: ignore


def check_hash(thing: bytes, checksum: str) -> bool:
    return hashlib.sha256(thing).hexdigest() == checksum


def run_subprocess(
    args: List[str],
    loading_text: str = "Loading",
    fail_text: str = "Error",
    success_text: str = "Done",
    with_spinner: bool = True,
    spinner_color: Optional[str] = None,
    text_color: Optional[str] = None,
    **kwargs: Any
) -> Optional[subprocess.CalledProcessError]:
    """Run a subprocess with a spinner."""
    with halo.Halo(text=loading_text, enabled=with_spinner, color=spinner_color, text_color=text_color) as spinner:  # type: ignore
        try:
            subprocess.run(args, check=True, **kwargs)  # type: ignore
        except subprocess.CalledProcessError as exception:
            spinner.fail(fail_text)  # type: ignore
            return exception
        else:
            spinner.succeed(success_text)  # type: ignore
            return None


def is_an_executable(path: Path) -> bool:
    return path.is_file() and os.access(path, os.F_OK | os.X_OK)


def get_folder_name_from_url(url: str) -> str:
    assert url.endswith(".git")
    return urllib.parse.urlparse(url).path.split("/")[-1]
