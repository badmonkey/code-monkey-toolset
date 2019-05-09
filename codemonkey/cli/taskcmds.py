import codemonkey.click as click


@click.group("task")
def entry():
    """ Commands for working with tasks """


@entry.command("test")
@click.pass_context
def task_test(context):
    print("TEST", context)
