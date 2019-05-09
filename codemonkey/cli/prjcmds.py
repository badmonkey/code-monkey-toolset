import codemonkey.click as click


@click.group("prj")
def entry():
    """ Commands for working with projects """


@entry.command("test")
@click.pass_context
def prj_test(context):
    print("TEST", context)
