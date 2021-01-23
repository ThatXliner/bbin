"""Utility classes for interacting with `package.json`s"""
import platform
from abc import ABC
from pathlib import Path
from typing import Dict, Generic, List, TypeVar


class PlatformNotSupportedError(Exception):
    """Your platform is not supported."""


class VersionNotSupportedError(PlatformNotSupportedError):
    """This version of the OS is not supported."""


def _get_os_release_info() -> Dict[str, str]:
    def clean(string: str) -> str:
        if string[0] in {"'", '"'}:
            string = string[1:]
        if string[-1] in {"'", '"'}:
            string = string[:-2]
        return string

    release_info = Path("/etc/os-release").read_text()
    output = {}
    for line in release_info.splitlines():
        key, value = line.split("=")
        output[key] = clean(value.strip())
    return output


def get_system() -> str:
    """A thin wrapper around platform.system with Linux support."""
    return platform.system()


def get_platform_version() -> str:
    """Get the current platform's version."""
    if not platform.system() == "Linux":
        return (
            platform.mac_ver()[0] or platform.win32_ver()[1] or platform.java_ver()[0]
        )
    return _get_os_release_info()["VERSION_ID"]


KindOfData = TypeVar("KindOfData")


class DataParser(ABC, Generic[KindOfData]):
    """A generic base class for parsing data."""

    def __init__(self, data: Dict[str, Dict[str, KindOfData]]) -> None:
        self._data = data

    def get_for_platform(
        self, target_platform: str = get_system().lower()
    ) -> Dict[str, KindOfData]:
        """Get a dictionary of the data for the target platform"""

    def get(self) -> KindOfData:
        """Get the data for the current platform's version.

        Default to `generic` if not available.
        """


class Hashes(DataParser[str]):
    """A parser object for hashes."""

    def get_for_platform(self, target_platform: str = get_system()) -> Dict[str, str]:
        """Get a dictionary of hashes for a target platform"""
        try:
            platform_hashes = self._data[target_platform]
            assert isinstance(platform_hashes, dict)
            return platform_hashes
        except KeyError as exception:
            raise PlatformNotSupportedError(
                f"No hashes available for {platform.system()!r}"
            ) from exception

    def get(self) -> str:
        """Get the hash for the current platform version.

        Default to the platform's generic hash if not available.
        """
        platform_hashes = self.get_for_platform()
        platform_hash = platform_hashes.get(
            get_platform_version(), platform_hashes["generic"]
        )
        assert isinstance(platform_hash, str)

        return platform_hash


class BuildInstructions(DataParser[List[str]]):
    """A parser object for build scripts."""

    def get_for_platform(
        self, target_platform: str = get_system()
    ) -> Dict[str, List[str]]:
        """Get a dictionary of build scripts for a target platform"""
        try:
            platform_build_script = self._data[target_platform]
            assert isinstance(platform_build_script, dict)
            return platform_build_script
        except KeyError as exception:
            raise PlatformNotSupportedError(
                f"No build script available for {platform.system()!r}"
            ) from exception

    def get(self) -> List[str]:
        """Get the build script for the current platform version.

        Default to the platform's generic build script if not available.
        """
        build_scripts = self.get_for_platform()
        build_script = build_scripts.get(
            get_platform_version(), build_scripts["generic"]
        )
        assert isinstance(build_script, list)
        return build_script
