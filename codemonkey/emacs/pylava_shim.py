import re
import sys
from os import path as op

import click

try:
    import pylava.main as pylama
    from pylava.core import LOGGER
    from pylava.config import CURDIR
    from pylava.errors import PATTERN_NUMBER
    from pylava.libs.inirama import INIScanner
except:
    import pylama.main as pylama
    from pylama.core import LOGGER
    from pylama.config import CURDIR
    from pylama.errors import PATTERN_NUMBER
    from pylama.libs.inirama import INIScanner


def process_paths(options, candidates=None, error=True):
    """Process files and log errors."""
    errors = pylama.check_path(options, rootdir=CURDIR, candidates=candidates)

    pattern = "%(filename)s:%(lnum)s:%(col)s:%(type)s:%(number)s:%(text)s"

    for er in errors:
        text = er._info["text"].split()
        if PATTERN_NUMBER.match(text[0]):
            er._info["text"] = " ".join(text[1:])

        if options.abspath:
            er._info["filename"] = op.abspath(er.filename)
        LOGGER.warning(pattern, er._info)

    if error:
        sys.exit(int(bool(errors)))

    return errors


# pylama.inirama didn't like spaces in the key part
for n, pattern in enumerate(INIScanner.patterns):
    if pattern[0] == "KEY_VALUE":
        INIScanner.patterns[n] = ("KEY_VALUE", re.compile(r"[^=]+\s*[:=].*"))
        break


@click.command()
@click.version_option()
@click.option("-c", is_flag=True)
@click.option("--msg-template")
@click.option("--reports")
@click.option("--output-format")
@click.option("--rcfile")
@click.argument("files", nargs=-1)
def main(rcfile, files, **ignored):
    """ Runs pylava but accepts pylint cmdline options """

    pylama.process_paths = process_paths

    rcargs = []
    if rcfile:
        for f in rcfile.split(","):
            if op.exists(f):
                rcargs = ["-o", op.abspath(f)]
                break

    with open("/tmp/shim.log", "a") as f:
        f.write(f"cmd {rcargs}\n")

    pylama.shell(args=rcargs + list(files))
