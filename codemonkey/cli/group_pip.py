import click


@click.group("pip")
def group_pip():
    """ Commands for working with pip """


@group_pip.command("test")
@click.pass_context
def pip_test(context):
    print("TEST", context)
