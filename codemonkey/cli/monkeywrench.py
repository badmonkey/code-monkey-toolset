from blessed import Terminal

import codemonkey.lib.click as click
import codemonkey.lib.config as cfglib
import codemonkey.lib.slugify as slugify

from .gitcmds import entry as gitcmds
from .gitlabcmds import entry as gitlabcmds
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
@click.option("--explain", is_flag=True)
@click.pass_context
def main_config(ctx, raw, explain):
    """ Print config data """
    obj = ctx.obj

    from pprint import pprint

    if raw:
        pprint(obj.config.values)
    else:

        if explain:

            def _print_section(name):
                info = obj.config.get_section_info(name, obj.argv.exename)
                if info:
                    title = f"Config for [{name}]"
                    print(title)
                    print("=" * len(title))
                    for v in info.values():
                        print(v.format())
                    print()

        else:

            def _print_section(name):
                cfg = obj.config.get_merged_section(name, obj.argv.exename)
                if cfg:
                    title = f"Config for [{name}]"
                    print(title)
                    print("=" * len(title))
                    for k, v in cfg.items():
                        print(f"{k}: {v}")
                    print()

        _print_section("wrench")
        _print_section("wrench.git")
        _print_section("wrench.gitlab")
        _print_section("wrench.prj")
        _print_section("wrench.venv")

        obj.argv.print_help(ctx)


@main.command("shell", context_settings=dict(ignore_unknown_options=True))
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def main_shell(obj, args):
    """ Run remaining cmdline as a shell command """

    print("SHELL", args)


@main.command("ignore", context_settings=dict(ignore_unknown_options=True))
@click.option("--info", is_flag=True, default=False)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def main_ignore(obj, info, args):
    """ Do nothing. Maybe print some info about sys.argv """

    if info:
        t = Terminal()
        orig = t.red if obj.argv.is_changed() else ""
        click.secho(f"sys.argv as {t.blue('typed')}: {orig}{click.format_argv(obj.argv.original)}")
        click.secho(
            f"sys.argv as {t.blue('run')}:   {t.green}{click.format_argv(obj.argv.aliased)}"
        )


@main.command("slug")
@click.argument("text")
@click.pass_obj
def main_slug(obj, text):
    """ Generate a branch name from some text """

    print("SLUG", slugify.for_branch_uri(text))


@main.command("test")
@click.pass_obj
def main_test(obj):
    """ test some code """

    print("---\n")

    from codemonkey.lib.bus import bus, EventBase

    class TestEvent(EventBase):
        def __init__(self, *args, docancel=False, **kwargs):
            super().__init__()
            self.docancel = docancel
            self.result = f"args: {args}, kwargs: {kwargs}"

    @bus.handler("test", TestEvent)
    def evtTest(evt):
        print("HANDLE", evt.result)
        return "all good!"

    @evtTest.check
    def frog(evt):
        print("CHECK1")

    @evtTest.check
    def bad(evt):
        print("CHECK2", evt.docancel)
        if evt.docancel:
            evt.cancel()

    @evtTest.notify
    def blah(evt, result):
        print("NOTIFY", result)

    print("TEST1", evtTest(TestEvent(name="test1")), "\n")

    print("TEST2", bus.emit("test", TestEvent(name="test2")), "\n")
    print("TEST3", bus.emit("test", 1, 2, name="test3"), "\n")
    print("TEST4", bus.emit("test", 1, 2, docancel=True, name="test4"), "\n")
