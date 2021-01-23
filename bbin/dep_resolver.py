"""Resolve dependencies"""
import shutil
from typing import Dict, List, Union

COMPILER_MAP = {"cpp": ["clang++", "g++"], "c": ["clang", "gcc"]}


def resolve_compiler(compiler_info: Dict[str, Union[str, List[str]]]) -> str:
    """Resolve the compiler with given information"""
    # TODO: Figure bootstrap
    if "for" in compiler_info:
        compiler = compiler_info["for"]
        assert isinstance(compiler, str)
        compiler = compiler.lower()
        return resolve_exe(COMPILER_MAP[compiler])
    names = compiler_info["name"]
    assert isinstance(names, list)
    return resolve_exe(names)


def resolve_exe(exe_names: List[str]) -> str:
    """Resolve executable (from a list of names) for the system"""
    output = None
    for name in exe_names:
        output = shutil.which(name)
        if output is not None:
            return output
