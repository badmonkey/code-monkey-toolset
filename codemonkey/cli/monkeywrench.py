import codemonkey.click as click
import codemonkey.config as cfglib

from .gitcmds import entry as gitcmds
from .pipcmds import entry as pipcmds
from .venvcmds import entry as venvcmds


class Wrench(click.Bootstrap):
    def __init__(self):
        super().__init__()
        self.config = None
        self.gitrepo = None


def init():

    bootobj = Wrench()
    bootobj.config = cfglib.load()

    exename = bootobj.argv.exename

    if exename == "wrench":
        aliases = None
    else:
        aliases = bootobj.config.get_merged_section("alias", exename=exename)

    bootobj.run(main, exename=exename, aliases=aliases)


@click.group()
@click.version_option()
@click.pass_context
def main(obj):
    """ MonkeyWrench is a set of utility tools to help with development tasks """


main.add_command(gitcmds)
main.add_command(pipcmds)
main.add_command(venvcmds)


@main.command("tree")
@click.pass_context
def main_tree(ctx):
    """ Print command structure as a tree """

    print(click.format_command_tree(ctx))


@main.command("shell", context_settings=dict(ignore_unknown_options=True))
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def main_shell(obj, args):
    """ Run cmdline as a shell command """

    print("SHELL", args)


@main.command("ignore", context_settings=dict(ignore_unknown_options=True))
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def main_ignore(obj, args):
    """ Do nothing but print sys.argv """

    print(f"sys.argv as typed: {click.format_argv(obj.argv.original)}")
    print(f"sys.argv as run:   {click.format_argv(obj.argv.aliased)}")
