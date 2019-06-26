# pylint: disable=W0212,W0702
import os
import os.path as ospath
import re
import sys
from pathlib import Path

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
            er._info["filename"] = ospath.abspath(er.filename)
        LOGGER.warning(pattern, er._info)

    if error:
        sys.exit(int(bool(errors)))

    return errors


# pylama.ini doesn't like spaces in the key part
for n, keypattern in enumerate(INIScanner.patterns):
    if keypattern[0] == "KEY_VALUE":
        INIScanner.patterns[n] = ("KEY_VALUE", re.compile(r"[^=]+\s*[:=].*"))
        break


@click.command()
@click.version_option()
@click.option("--debug", is_flag=True)
@click.option("-c", is_flag=True)
@click.option("--msg-template")
@click.option("--reports")
@click.option("--output-format")
@click.option("--rcfile")
@click.argument("files", nargs=-1)
def main(debug, rcfile, files, **ignored):
    """ Runs pylava but accepts pylint cmdline options """

    pylama.process_paths = process_paths

    preamble = None
    rcargs = []
    files = list(files)
    venv = find_venv()

    if files:
        if files[0].startswith("import "):
            preamble = files.pop(0)

    wd = os.getcwd()

    if rcfile:
        rc_try = [ospath.join(wd, "pylava.ini"), rcfile, ospath.join(wd, "setup.cfg")]
        rc_try = [x for x in rc_try if ospath.exists(x)]
        if rc_try:
            rcargs = ["-o", rc_try[0]]

    if files:
        newargs = rcargs + files
    else:
        newargs = ["Determining", "pylint", "path"]

    debug = True
    if debug:
        with open("/tmp/pylava-shim.log", "a") as f:

            def _p(s):
                f.write(f"{s}\n")
                print(s)

            _p("---------------->>>>>")
            _p(" ".join(sys.argv))
            _p("----------------")
            _p(f"wd: {os.getcwd()}")
            _p(f"venv: {venv}")
            _p(f"rcargs: {rcargs}")
            _p(f"preamble: {preamble}")
            _p(f"files: {files}")
            _p(f"ignored: {ignored}")
            _p(f"pylama: {pylama.__file__}")
            _p("----------------")
            _p(f"pylama: {' '.join(newargs)}")
            _p("<<<<<----------------")
            _p("")

    if not files:
        print(sys.argv[0])
    else:
        pylama.shell(args=newargs)


def find_venv():
    venv = os.getenv("VIRTUAL_ENV")
    vhome = os.getenv("WORKON_HOME")

    if venv and vhome:
        venv = Path(venv).resolve()
        vhome = Path(vhome).resolve()
        return str(venv.relative_to(vhome))
    return None


if __name__ == "__main__":
    main()  # noqa:E1120
