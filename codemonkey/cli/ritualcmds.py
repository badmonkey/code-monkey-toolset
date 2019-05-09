import codemonkey.click as click


@click.group("ritual")
def entry():
    """ Commands for working with venv """


@entry.command("test")
@click.pass_context
def ritual_test(context):
    print("TEST", context)
