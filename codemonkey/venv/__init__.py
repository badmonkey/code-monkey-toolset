import sys


def is_in_venv():
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


# WORKON_HOME
# VIRTUAL_ENV


# list venvs in WORKON_HOME
# get home of venv XXX
# create new venv
