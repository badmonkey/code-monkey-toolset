import pkgutil
import site
import sys

import click


def init():
    print(sys.argv)

    main()  # noqa


@click.group()
@click.version_option()
@click.pass_context
def main(context):
    pass


@main.command("imports")
@click.argument("filep")
def main_imports(filep):
    from codemonkey.python import ast_imports

    print(ast_imports(filep))


@main.command("site")
def main_site():
    print(site.getsitepackages())
    # for m in list(pkgutil.iter_modules()):
    #    if m.ispkg:
    #        print(f"MOD {m}")


@main.command("config")
def main_config():
    import codemonkey.lib.config as cfg

    print(cfg.load())
