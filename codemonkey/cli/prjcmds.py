import codemonkey.lib.click as click


@click.group("prj")
def entry():
    """ [group] Commands for working with projects """


@entry.command("test")
@click.pass_context
def prj_test(context):
    print("TEST", context)
