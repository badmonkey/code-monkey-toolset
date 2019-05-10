import codemonkey.lib.click as click


@click.group("git")
def entry():
    """ [group] Commands for working with git """


@entry.command("test")
@click.pass_context
def git_test(context):
    print("TEST", context)
