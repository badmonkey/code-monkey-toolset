import codemonkey.click as click
import codemonkey.config as cfglib
import codemonkey.slugify as slugify

from .gitcmds import entry as gitcmds
from .gitlabcmds import entry as gitlabcmds
from .pipcmds import entry as pipcmds
from .prjcmds import entry as prjcmds
from .ritualcmds import entry as ritualcmds
from .taskcmds import entry as taskcmds
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
main.add_command(gitlabcmds)
main.add_command(pipcmds)
main.add_command(prjcmds)
main.add_command(ritualcmds)
main.add_command(taskcmds)
main.add_command(venvcmds)


@main.command("tree")
@click.pass_context
def main_tree(ctx):
    """ Print command structure as a tree """

    print(click.format_command_tree(ctx))


@main.command("config")
@click.option("--raw", is_flag=True)
@click.pass_context
def main_config(ctx, raw):
    """ Print config data """
    obj = ctx.obj

    from pprint import pprint

    if raw:
        pprint(obj.config.values)
    else:

        def _print_section(name):
            cfg = obj.config.get_merged_section(name, obj.argv.exename)
            if cfg:
                print(f"Config for [{name}]")
                pprint(cfg)
                print()

        _print_section("wrench")
        _print_section("wrench.git")
        _print_section("wrench.gitlab")
        _print_section("wrench.pip")
        _print_section("wrench.prj")
        _print_section("wrench.venv")

        obj.argv.print_help(ctx)


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


@main.command("slug")
@click.argument("text")
@click.pass_obj
def main_shell(obj, text):
    """ Generate a branch name from some text """

    print("SLUG", slugify.for_branch_uri(text))
