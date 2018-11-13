import click
import sys
import pylava.main
from pylava.core import LOGGER
from pylava.config import CURDIR
from pylava.errors import PATTERN_NUMBER
from os import path as op
import collections


def process_paths(options, candidates=None, error=True):
    """Process files and log errors."""
    errors = pylava.main.check_path(options, rootdir=CURDIR, candidates=candidates)

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


@click.command()
@click.version_option()
@click.option("-c", is_flag=True)
@click.option("--msg-template")
@click.option("--reports")
@click.option("--output-format")
@click.option("--rcfile")
@click.argument("files", nargs=-1)
def main(rcfile, files, **ignored):
    pylava.main.process_paths = process_paths

    pylava.main.shell(args=["-o", rcfile] + list(files))


# end
