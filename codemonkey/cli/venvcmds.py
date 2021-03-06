import codemonkey.lib.click as click
import codemonkey.service.venv as venvservice


@click.group("venv")
def entry():
    """ [group] Commands for working with virtual envs """


@entry.command("compile")
@click.option("--include-devel/--just-pip-packages", "editables", default=False)
@click.option(
    "-i", "--ignore", multiple=True, help="Don't list these packages", metavar="<package list>"
)
@click.option("-p", "--show", multiple=True, help="list these packages", metavar="<package list>")
@click.pass_obj
def venv_compile(obj, **kwargs):
    """ Build a requirements.txt from current venv """

    showset = lib.option_to_set(show)
    ignoreset = lib.option_to_set(ignore)
    keepset = dists.VIRTUALENV_PKGS | dists.COMMON_PKGS | showset

    if editables:
        skipset = ignoreset
        distlist = dists.get_distributions(ignore=skipset)
    else:
        skipset = (dists.PIPTOOLS_PKGS - keepset) | ignoreset
        distlist = dists.get_distributions(ignore=skipset, editable=False)

    print(f"# This file autogenerated by pip-chill")
    print(f'# at {datetime.datetime.now()} with "{lib.cmdline()}"')
    print("#\n")

    for d in distlist:
        print(dists.make_spec(d))


### ======================================================== ###


@entry.command("purge")
@click.option("-n", "--dry-run", is_flag=True, help="Don't make changes")
@click.option(
    "-k", "--keep", multiple=True, help="Don't uninstall these packages", metavar="<package list>"
)
@click.option("--clear-all/--safe-clear", default=False, help="Clear all the packages")
@click.pass_obj
def venv_purge(obj, **kwargs):
    """ Remove all packages from current venv """

    if not lib.running_under_virtualenv():
        print("for safety, we require an active virtualenv")
        sys.exit(-1)

    try:
        config = lib.get_config_section(cfgpath, "piptools:purge")
    except Exception as e:
        print(f"Unable to read config: {e}")
        sys.exit(-1)

    skipset = dists.VIRTUALENV_PKGS | lib.option_to_set(keep)

    if not clear_all:
        skipset = skipset | dists.COMMON_PKGS | dists.PIPTOOLS_PKGS | set(config.getlist("keep"))

    packages = dists.get_package_names(ignore=skipset, virtualenv=True)

    if not packages:
        print("No work needs doing")
        sys.exit(0)

    if dry_run:
        keep = ",".join(skipset)
        print(f"Keeping {keep}")
        uninstall = ",".join(packages)
        print(f"Uninstalling {uninstall}")
    else:
        subprocess.run(["pip", "uninstall", "-y"] + packages)


### ======================================================== ###


@entry.command("switch")
@click.argument("require", nargs=-1)
@click.option("-r", "--requirements", multiple=True)
@click.option("-e", "--edit", multiple=True, help="Install package as editable")
@click.option("-i", "--install", multiple=True, help="Install package  pack[==1.0.0]")
@click.option("-k", "--keep", multiple=True, help="Don't uninstall package")
@click.option(
    "--use-dev-reqs/--ignore-dev-reqs", default=True, help="Look for a requirements-dev.txt file"
)
@click.option("--allow-missing/--fail-missing", default=True)
@click.pass_obj
def venv_switch(obj, **kwargs):
    """ Remove or install packages to make the current venv match a requirements.txt """

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


### ======================================================== ###


@entry.command("test")
@click.pass_obj
def venv_test(obj, **kwargs):
    x = venvservice.UninstallEvent()
    print(x)
    print(venvservice.evtPurge(x))
