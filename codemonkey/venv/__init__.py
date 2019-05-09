import os
import sys
from pathlib import Path
from typing import List

TDirPath = Path


def running_in_venv() -> bool:
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


# sys.prefix vs sys.base_prefix is the definitive paths for the virtualenv
# but ... environ var override ... ".venv" lesser override ... so we can do things
# to a venv from another venv or work with a deactivated venv


def running_path() -> TDirPath:
    """
    Path of the current running virtual env.
    Not influenced by VIRTUAL_ENV or pressence of a ".venv"
    """
    if hasattr(sys, "base_prefix"):
        if sys.base_prefix != sys.prefix:
            return Path(sys.prefix)
    raise RuntimeError("Not running in a virtual env")


def path(allow_anon=True) -> TDirPath:
    """
    Path of current venv.
    Can be overridden with VIRTUAL_ENV or .venv in local dir
    """
    return (
        environ_to_path("VIRTUAL_ENV") or (_local_venv() if allow_anon else None) or running_path()
    )


def home() -> TDirPath:
    """
    Return path of where venv's are stored. Is influenced by VIRTUAL_ENV
    If all we have is a anon venv then return none
    todo what if VIRTUAL_ENV points to a anon venv, home should be None
    """
    return environ_to_path("WORKON_HOME") or path(allow_anon=False).parent


def name() -> str:
    """
    """
    try:
        return str(path().relative_to(home()))
    except ValueError:
        pass
    return "<anon>"


def is_activated(p: Path) -> bool:
    return p and p.is_dir() and hasattr(sys, "base_prefix") and sys.prefix == p.resolve()


def is_venv(p: Path) -> bool:
    return (
        p
        and p.is_dir()
        and p.joinpath("pyvenv.cfg").is_file()
        and p.joinpath("bin").is_dir()
        and p.joinpath("lib").is_dir()
    )


def list() -> List[TDirPath]:
    hm = home_path() or []
    return [p for p in hm.iterdir() if is_venv(p)]


def environ_to_path(name: str) -> Path:
    value = os.getenv(name)
    if value:
        value = Path(value)
        if value.is_dir():
            return value.resolve()

    return None


def _local_venv() -> TDirPath:
    p = Path(".venv").resolve()
    if p.is_dir():
        return p
    return None


# list venvs in WORKON_HOME
# get home of venv XXX
# create new venv
