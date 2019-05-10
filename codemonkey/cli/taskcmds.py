import codemonkey.lib.click as click


@click.group("task")
def entry():
    """ [group] Commands for working with tasks """


@entry.command("test")
@click.pass_context
def task_test(context):
    print("TEST", context)
