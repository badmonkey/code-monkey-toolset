import codemonkey.lib.click as click
import codemonkey.service.git as gitservice


@click.group("git")
def entry():
    """ [group] Commands for working with git """


@entry.command("test")
@click.pass_context
def git_test(context):
    print("SRV", gitservice.evtMakeBranch(gitservice.GitMakeBranchEvent()))
    print("TEST", context)
