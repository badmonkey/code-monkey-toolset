import codemonkey.click as click


@click.group("gitlab")
def entry():
    """ Commands for working with gitlab """


@entry.command("test")
@click.pass_context
def gitlab_test(context):
    print("TEST", context)
