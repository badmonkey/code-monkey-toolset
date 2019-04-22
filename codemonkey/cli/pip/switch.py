import pprint

import click

import codemonkey.lib as lib

# import requirements


@click.command()
@click.version_option()
@click.argument("require", nargs=-1)
@click.option("-r", "--requirements", multiple=True)
@click.option("-e", "--edit", multiple=True, help="Install package as editable")
@click.option("-i", "--install", multiple=True, help="Install package  pack[==1.0.0]")
@click.option("-k", "--keep", multiple=True, help="Don't uninstall package")
@click.option(
    "--use-dev-reqs/--ignore-dev-reqs", default=True, help="Look for a requirements-dev.txt file"
)
@click.option("--allow-missing/--fail-missing", default=True)
def main(use_dev_reqs, allow_missing, **kwargs):
    pprint.pprint(kwargs)

    rfiles = set(kwargs["require"]) | set(kwargs["requirements"])
    if not rfiles:
        if use_dev_reqs:
            rfiles = set(["requirements.txt", "requirements-dev.txt"])
        else:
            rfiles = set(["requirements.txt"])
    # end
    pprint.pprint(rfiles)

    print("keep", lib.option_to_set(kwargs["keep"]))
    print("install", lib.option_to_set(kwargs["install"]))
    print("edit", lib.option_to_set(kwargs["edit"]))


#    with open(require, 'r') as fd:
#        for req in requirements.parse(fd):
#            print(req.name, req.specs)
# end
# end


"""

pip-switch -e piptools,gittools,devtools[advanced]  requirements.txt

"""
