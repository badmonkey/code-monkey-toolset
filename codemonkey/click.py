import functools
import os
import shlex
import sys
from string import Template
from typing import Dict, List, Tuple

import click
from click import (  # noqa:W0611
    UNPROCESSED,
    Context,
    argument,
    option,
    pass_context,
    pass_obj,
    version_option,
)
from click_didyoumean import DYMGroup
from click_help_colors import HelpColorsCommand, HelpColorsGroup

SectionType = Dict[str, str]
ConfigType = Dict[str, SectionType]
ArgvType = List[str]


class WrenchGroup(DYMGroup, HelpColorsGroup, click.Group):
    def format_help(self, ctx, formatter):
        self.format_usage(ctx, formatter)
        self.format_help_text(ctx, formatter)
        self.format_options(ctx, formatter)
        self.format_aliases(ctx, formatter)
        self.format_epilog(ctx, formatter)

    def format_aliases(self, ctx, formatter):
        if hasattr(self, "aliases"):
            helpdata = getattr(self, "aliases")
            if not helpdata:
                return
            with formatter.section("Aliases"):
                formatter.write_dl(helpdata)


class WrenchCommand(HelpColorsCommand, click.Command):
    pass


def group(name=None, **attrs):
    attrs.setdefault("cls", WrenchGroup)
    attrs.setdefault("help_headers_color", "yellow")
    attrs.setdefault("help_options_color", "green")
    return click.group(name, **attrs)


def command(name=None, **attrs):
    attrs.setdefault("cls", WrenchCommand)
    attrs.setdefault("help_options_color", "blue")
    return click.command(name, **attrs)


def catch_exception(exception, exit_code=1, message=None):
    """A decorator that gracefully handles exceptions, exiting
    with :py:obj:`exit_codes.OTHER_FAILURE`.
    """

    def decorator(f):
        @click.pass_context
        def new_func(ctx, *args, **kwargs):
            try:
                return ctx.invoke(f, *args, **kwargs)
            except exception as e:
                click.echo(message if message else f"{e}")
                ctx.exit(code=exit_code)

        return functools.update_wrapper(new_func, f)

    return decorator


def format_command_tree(ctx):
    treedata = _build_command_tree(ctx.find_root().command)

    output = []
    _format_tree(output, treedata)

    formatter = ctx.make_formatter()
    formatter.write_dl(output)

    return formatter.getvalue()


class _TreeData:
    def __init__(self, click_command):
        self.name = click_command.name
        self.children = []
        self.short_help = None

        if isinstance(click_command, click.Command):
            self.short_help = click_command.get_short_help_str()


def _build_command_tree(click_command):
    data = _TreeData(click_command)

    if isinstance(click_command, click.Group):
        data.children = [_build_command_tree(cmd) for _, cmd in click_command.commands.items()]

    return data


def _format_tree(output, treedata, depth=0, is_last_item=False, is_last_parent=False):
    if depth == 0:
        prefix = ""
        tree_item = ""
    else:
        prefix = "    " if is_last_parent else "│   "
        tree_item = "└── " if is_last_item else "├── "

    help_str = ("  \t" + treedata.short_help) if treedata.short_help else ""
    output.append((prefix * (depth - 1) + tree_item + treedata.name, help_str))

    for i, child in enumerate(sorted(treedata.children, key=lambda x: x.name)):
        _format_tree(
            output,
            child,
            depth=(depth + 1),
            is_last_item=(i == (len(treedata.children) - 1)),
            is_last_parent=is_last_item,
        )


def format_argv(args=None):
    args = args or sys.argv[:]
    args[0] = os.path.basename(args[0])
    args = [f'"{x}"' if " " in x else x for x in args]
    return " ".join(args)


class AliasedArgv:
    def __init__(self):
        self.original: ArgvType = sys.argv[:]
        self.aliased: ArgvType = sys.argv
        self.exename: str = os.path.basename(sys.argv[0])
        self.other_tmpl: str = "*"
        self.alias_help = []

    def __str__(self):
        return format_argv(self.aliased)

    def update(self, aliases, exename=None, change_argv=False):
        update_argv_aliases(self, aliases, exename=exename, change_argv=change_argv)

    def is_unchanged(self):
        return False


class Bootstrap:
    def __init__(self):
        self.argv = AliasedArgv()

    def run(self, cmdline_group, exename: str = None, aliases: SectionType = None, **kwargs):
        context = Context(cmdline_group)

        try:
            if aliases:
                self.argv.update(aliases, exename=exename, change_argv=True)
            elif exename:
                self.argv.exename = exename
        except Exception as e:
            # make pretty again
            print(e)
            sys.exit(1)

        if exename:
            kwargs.setdefault("prog_name", exename)

        if isinstance(cmdline_group, WrenchGroup):
            setattr(cmdline_group, "aliases", self.argv.alias_help)

        context.obj = self

        kwargs["parent"] = context

        return cmdline_group.main(**kwargs)


def _match(pattern: ArgvType, args: ArgvType) -> Tuple[bool, ArgvType]:
    env = {}
    for term in pattern:
        if term.startswith("$"):
            if args:
                env[term[1:]] = args.pop(0)
                continue
            return False, env
        if term.startswith("?"):
            k = term[1:]
            if args:
                env[k] = args.pop(0)
            else:
                env[k] = None
            continue
        if not args or args[0] != term:
            return False, env
        args.pop(0)

    env["*"] = args
    return True, env


def _replace(tmpl: ArgvType, env) -> ArgvType:
    if not tmpl:
        return []
    output = []
    for term in tmpl:
        if term.startswith("$"):
            k = term[1:]
            if k == "*":
                raise Exception(f"'$*' is invalid")
            if k not in env:
                raise Exception(f"No value for '{term}'")
            v = env[k]
            if v:
                output.append(v)
            continue
        if term == "*":
            output.extend(env["*"])
            continue
        if "$" in term:
            t = Template(term)
            err = ""
            try:
                output.append(t.substitute(env))
                continue
            except ValueError as e1:
                err = f"{e1} of '{term}'"
            except KeyError as e2:
                err = f"Unknown variable ${str(e2)[1:-1]} in '{term}'"

            raise Exception(err)

        output.append(term)
    return output


def _strip_options(value: ArgvType) -> ArgvType:
    output = []
    for x in value:
        if x == "*" or x.startswith("-") or "=" in x or " " in x:
            return output
        output.append(x)
    return output


def _format_alias(subst, pass_any):
    output = {}
    for k, v in subst:
        fk = f"'{format_argv(k)}'"
        if v:
            output[fk] = f"'{format_argv(v)}'"
        else:
            output[fk] = "Command is ignored"
    output = sorted(output.items(), key=lambda x: x[0])
    if pass_any:
        if len(pass_any) == 1 and pass_any[0] == "*":
            output.append(("Other", f"args are forwarded"))
        else:
            output.append(("Other", f"args are forwarded as '{format_argv(pass_any)}'"))
    else:
        output.append(("Other", "All other commands are ignored"))
    return output


def update_argv_aliases(
    argv: AliasedArgv, cfg: SectionType, exename: str = None, change_argv=False
) -> None:
    exename = exename or os.path.basename(sys.argv[0])
    argv.exename = exename
    argv.aliased[0] = exename

    subst = {}

    for k, v in cfg.items():
        subst[k] = (shlex.split(k), shlex.split(v))

    if "*" in subst:
        argv.other_tmpl = subst["*"][1]
        del subst["*"]

    subst = sorted(subst.values(), key=lambda x: len(x[0]), reverse=True)

    argv.alias_help = _format_alias(subst, argv.other_tmpl)

    newargv = False

    for k, v in subst:
        ismatch, env = _match(k, sys.argv[1:])
        if ismatch:
            argv.aliased = [exename] + _replace(v, env)
            newargv = True
            break

    if not newargv:
        argv.aliased = [exename] + _replace(argv.other_tmpl, {"*": sys.argv[1:]})

    if change_argv:
        sys.argv = argv.aliased
