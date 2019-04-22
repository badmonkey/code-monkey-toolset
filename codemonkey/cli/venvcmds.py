import codemonkey.click as click


@click.group("venv")
def entry():
    """ Commands for working with venv """


@entry.command("test")
@click.pass_context
def venv_test(context):
    print("TEST", context)
