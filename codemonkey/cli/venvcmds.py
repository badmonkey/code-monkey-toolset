import codemonkey.lib.click as click


@click.group("venv")
def entry():
    """ [group] Commands for working with venv """


@entry.command("test")
@click.pass_context
def venv_test(context):
    print("TEST", context)
