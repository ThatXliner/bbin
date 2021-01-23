"""Enumerations"""
import enum


class InstallType(enum.Enum):
    EXE = "EXE"
    PKG = "PKG"
    URL = "URL"


class InstallAction(enum.Enum):
    move = "move"
    symlink = "symlink"
    copy = "copy"


class DepType(enum.Enum):
    compiler = "compiler"
    executable = "executable"
    package = "package"
