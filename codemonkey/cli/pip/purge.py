import subprocess
import sys

import click

import codemonkey.lib as lib
import codemonkey.pip.dists as dists


@click.command()
@click.version_option()
@click.option(
    "-c",
    "--config",
    "cfgpath",
    default="tools.ini",
    help="Use this config file. Otherwise search for tools.ini, setup.cfg, or tox.ini",
    metavar="<none|file path|filename>",
)
@click.option("-n", "--dry-run", is_flag=True, help="Don't make changes")
@click.option(
    "-k", "--keep", multiple=True, help="Don't uninstall these packages", metavar="<package list>"
)
@click.option("--clear-all/--safe-clear", default=False, help="Clear all the packages")
def main(cfgpath, dry_run, keep, clear_all):
    """ Uninstall most packages from the virtualenv """

    if not lib.running_under_virtualenv():
        print("for safety, we require an active virtualenv")
        sys.exit(-1)

    try:
        config = lib.get_config_section(cfgpath, "piptools:purge")
    except Exception as e:
        print(f"Unable to read config: {e}")
        sys.exit(-1)

    skipset = dists.VIRTUALENV_PKGS | lib.option_to_set(keep)

    if not clear_all:
        skipset = skipset | dists.COMMON_PKGS | dists.PIPTOOLS_PKGS | set(config.getlist("keep"))

    packages = dists.get_package_names(ignore=skipset, virtualenv=True)

    if not packages:
        print("No work needs doing")
        sys.exit(0)

    if dry_run:
        keep = ",".join(skipset)
        print(f"Keeping {keep}")
        uninstall = ",".join(packages)
        print(f"Uninstalling {uninstall}")
    else:
        subprocess.run(["pip", "uninstall", "-y"] + packages)


# end
