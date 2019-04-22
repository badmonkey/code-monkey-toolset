import os
import subprocess
import sys

import pkg_resources

"""
It has been noted several times in the setuptools "forums", that that 3rd-party tools shouldn't
 be using pip._internal.get_installed_distributions, instead they should be using
pkg_resources.working_set ... which is all well and good, except get_installed_distributions
allows filtering of editables packages, while working_set does not. Given the likely-hood
that pip._internals will change and break code, i've replicated some of the package filtering code.


In a newly created virtual-env
> pip list
pip           18.0
pkg-resources 0.0.0
setuptools    40.4.3
wheel         0.32.0

Which matches what pkg_resources.working_set returns.
We should avoid removing these packages (it will likely break the virtualenv).

"""

# Some platforms may list these packages, they should always be ignored.
# From pip/_internal/utils/compat.py#193
STDLIB_PKGS = {"python", "wsgiref", "argparse"}

# Minimium packages for a virtualenv (they shouldn't be uninstalled)
VIRTUALENV_PKGS = {"pip", "pkg-resources", "setuptools", "wheel"}

# packages that are super common in a virtualenv
COMMON_PKGS = {"six", "click", "setupmeta"}

# packages required running piptools (us)
PIPTOOLS_PKGS = {"piptools", "click", "setupmeta", "requirements-parser"}


def canonical(path, resolve_symlinks=True):
    """
    Convert a path to its canonical, case-normalized, absolute version.
    """
    path = os.path.expanduser(path)
    if resolve_symlinks:
        path = os.path.realpath(path)
    else:
        path = os.path.abspath(path)
    return os.path.normcase(path)


# end


def dist_is_editable(dist):
    """Is distribution an editable install?"""

    for path_item in sys.path:
        egg_link = os.path.join(path_item, dist.project_name + ".egg-link")
        if os.path.isfile(egg_link):
            return True
    return False


# end


def filter_by_lambdas(x, Funs):
    for f in Funs:
        if not f(x):
            return False
    return True


# end


def filter_none(x):
    return True


def _not(f):
    return lambda x: not f(x)


def _ignore(ignore):
    return lambda x: x.key not in ignore


def _in_location(locations):
    if not isinstance(locations, list):
        locations = [canonical(locations)]
    else:
        locations = [canonical(p) for p in locations]

    return lambda x: any(canonical(x.location).startswith(p) for p in locations)


# end


SYS_PREFIX = canonical(sys.prefix)


def running_under_virtualenv():
    """
    Return True if we're running inside a virtualenv, False otherwise.
    """
    if hasattr(sys, "real_prefix"):
        return True
    elif sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        return True

    return False


# end


def _in_virtualenv():
    if running_under_virtualenv():
        return lambda x: canonical(x.location).startswith(SYS_PREFIX) or dist_is_editable(x)
    else:
        return filter_none


# end


def get_distributions(ignore=None, editable=None, location=None, virtualenv=None):
    """
    Get a list of Distributions of installed packages
    None - don't use that filter
    ignore: an in'able container of dist names to ignore
    editable: True = only editable, False = only not editable
    location: container of paths to test if dist.location is in

    based on pip/_internal/utils/misc.py#340
    """

    filters = []

    if ignore is not None:
        filters.append(_ignore(ignore))

    if editable is not None:
        if editable:
            filters.append(dist_is_editable)
        else:
            filters.append(_not(dist_is_editable))
    # end

    if location is not None:
        filters.append(_in_location(location))

    if virtualenv:
        filters.append(_in_virtualenv())

    return get_filtered_distributions(*filters)


# end


def get_filtered_distributions(*filters):
    if not filters:
        filters = [filter_none]
    elif len(filters) == 1 and isinstance(filters[0], list):
        filters = filters[0]
    # end

    return sorted(
        [
            d
            for d in pkg_resources.working_set
            if d.key not in STDLIB_PKGS and filter_by_lambdas(d, filters)
        ],
        key=lambda x: x.key,
    )


# end


def get_package_names(**kwargs):
    return [p.key for p in get_distributions(**kwargs)]


def distributions():
    return {d.key: d for d in get_distributions()}


def what_installed(pkgspec):
    try:
        reqs = pkg_resources.Requirement.parse(pkgspec)
        return {d.key for d in pkg_resources.working_set.resolve([reqs])}
    except Exception:
        return set()


# end


def extras_installed(d):
    try:
        base = what_installed(d.key)
        extras = []
        for extra in d.extras:
            extra_diff = what_installed(f"{d.key}[{extra}]") - base
            if extra_diff:
                extras.append(extra)
        return extras
    except Exception:
        return []


# end


def fix_location(path):
    newp = os.path.relpath(path)
    if newp.startswith(".."):
        return path
    return newp


# end


def make_spec(d):
    extras = extras_installed(d)
    extras_spec = "[{}]".format(",".join(extras)) if extras else ""
    if dist_is_editable(d):
        location = fix_location(d.location)
        return f"-e {location}{extras_spec}"
    else:
        return f"{d.project_name}=={d.version}{extras_spec}"


# end


###############################################


class DataObject(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(kwargs)

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError(f"No such attribute: {name}")

    # end

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]

    # end


# end


class DevPackage(DataObject):
    def __init__(self, path):
        super().__init__()

        self.path = path

        self.name = self.run(["python", "setup.py", "--name"], stdout="capture")
        self.dist = None

    # end

    def run(self, cmdlist, check=False, stdout=None):
        if stdout == "capture":
            out = subprocess.run(
                cmdlist, cwd=self.path, check=True, encoding="utf-8", stdout=subprocess.PIPE
            )
            return out.stdout.strip()
        if stdout == "stdout" or stdout == "print":
            subprocess.run(cmdlist, cwd=self.path, check=check)
        else:
            subprocess.run(cmdlist, cwd=self.path, check=check, stdout=subprocess.DEVNULL)
        # end
        return True

    # end


# end


class Context(DataObject):
    def __init__(self, path, exclude_pkg=None, exclude_dir=None):
        super().__init__(path=path)

        self.out = None
        self.exclude_pkg = [] if exclude_pkg is None else exclude_pkg
        self.exclude_dir = [] if exclude_dir is None else exclude_dir
        self.installed = distributions()

    # end

    def find_packages(self):
        for x in os.listdir(self.path):
            if x.startswith(".") or x in self.exclude_dir:
                continue
            pack_path = os.path.join(self.path, x)
            if os.path.isdir(pack_path):
                setup_path = os.path.join(pack_path, "setup.py")
                if os.path.isfile(setup_path):
                    new_pack = self._make_package(pack_path)
                    if new_pack.name not in self.exclude_pkg:
                        yield new_pack
                # end
            # end
        # end

    # end

    def _make_package(self, path):
        pack = DevPackage(path)
        if pack.name in self.installed:
            pack.dist = self.installed[pack.name]

        return pack

    # end


# end
