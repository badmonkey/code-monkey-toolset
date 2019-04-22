import codemonkey.click as click
import codemonkey.config as cfglib

from .group_pip import group_pip


class Wrench(click.Bootstrap):
    def __init__(self):
        super().__init__()
        self.config = None
        self.gitrepo = None


def init():

    bootobj = Wrench()
    bootobj.config = cfglib.load()

    aliases = bootobj.config.get_merged_section("alias", exename="ved")
    bootobj.run(main, exename="ved", aliases=aliases)


@click.group()
@click.version_option()
@click.catch_exception(Exception)
@click.pass_context
def main(obj):
    """ MonkeyWrench is a set of utility tools to help with development tasks """


main.add_command(group_pip)


@main.command("test")
@click.pass_context
def main_test(context):
    print("TEST", context)


@main.command("ignore", context_settings=dict(ignore_unknown_options=True))
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def main_ignore(obj, args):
    print("CONFIG", obj.config.get_merged_section("wrench", exename="ved"))
    print(f"ORIGINAL [{click.format_argv(obj.argv.original)}]")
    print(f"ALIASED [{click.format_argv(obj.argv.aliased)}]")
