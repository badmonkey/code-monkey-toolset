import os
import click
from clickclick import OutputFormat, Action
from clickclick.console import print_table
import subprocess
import pygit2
import ssh_agent_setup


class DataObject(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(kwargs)

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    # end

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]

    # end


# end


def fix_branch_name(namegen):
    for name in namegen:
        fixed = remove_prefix("origin/", name)
        if not fixed.startswith("HEAD"):
            yield fixed, name
    # end


# end


def get_merged(remote=False):
    if remote:
        cmd = ["git", "branch", "-r", "--merged", "master"]
    else:
        cmd = ["git", "branch", "--merged", "master"]

    for name in subprocess.check_output(cmd, universal_newlines=True).splitlines():
        if name.startswith("*"):
            name = name[1:]
        name = name.strip()
        yield name
    # end


# end


def remove_prefix(prefix, txt):
    if txt.startswith(prefix):
        return txt[len(prefix) :]
    return txt


# end


def newInfo(name):
    return DataObject(
        name=name,
        key=name,
        local=False,
        remote=False,
        head=False,
        target=None,
        gone=False,
        pushed=False,
        up2date=False,
        merged=False,
    )


def branch_info(b, islocal):
    if b is None:
        return {}

    def get(x, nm):
        return getattr(x, nm) if hasattr(x, nm) else "--"

    out = {
        "islocal": islocal,
        "target": get(b, "target"),
        "head": b.is_head(),
        "branch_name": get(b, "branch_name"),
        "upstream_name": get(b, "upstream_name") if islocal else "NA",
        "checkout_out": b.is_checked_out(),  # if islocal else "NA",
        "upstream": branch_info(b.upstream, False) if islocal else "NA",
    }
    return out


# end


def fill_branch_info(info, branches, islocal=True):
    for name, realname in fix_branch_name(branches.local if islocal else branches.remote):
        if name not in info:
            info[name] = newInfo(name)

        info[name].key = realname

        branch = branches[realname]
        if info[name].target is None:
            info[name].target = branch.target

        if islocal:
            info[name].local = True
            if branch.upstream is None:
                info[name].gone = True
            elif branch.target == branch.upstream.target:
                info[name].pushed = True
            # end
        else:
            info[name].remote = True
        # end

        #        import pprint
        #        pprint.pprint( branch_info(branch, islocal) )

        if branch.is_head():
            info[name].head = True
    # end


# end


def fill_merged_info(info, isremote=False):
    try:
        for name, _ in fix_branch_name(get_merged(remote=isremote)):
            if name not in info:
                info[name] = newInfo(name)

            if isremote:
                info[name].merged = True
            else:
                info[name].up2date = True
    except subprocess.CalledProcessError:
        pass


# end


def first_line(s):
    return s.splitlines()[0]


@click.group()
@click.version_option()
def main():
    pass


class SSHAgentCallbacks(pygit2.RemoteCallbacks):
    def credentials(self, url, username_from_url, allowed_types):
        if allowed_types & pygit2.credentials.GIT_CREDTYPE_USERNAME:
            return pygit2.Username(username_from_url)
        elif pygit2.credentials.GIT_CREDTYPE_SSH_KEY & allowed_types:
            if "SSH_AUTH_SOCK" in os.environ:
                # Use ssh agent for authentication
                print(f"SSH_AUTH_SOCK set {username_from_url} {url} {os.environ['SSH_AUTH_SOCK']}")
                return pygit2.KeypairFromAgent(username_from_url)
            else:
                print("default")
                ssh = os.path.join(os.path.expanduser("~"), ".ssh")
                pubkey = os.path.join(ssh, "id_rsa.pub")
                privkey = os.path.join(ssh, "id_rsa")
                # check if ssh key is available in the directory
                if os.path.isfile(pubkey) and os.path.isfile(privkey):
                    return pygit2.Keypair(username_from_url, pubkey, privkey, "")
                else:
                    raise Exception(
                        "No SSH keys could be found, please specify SSH_AUTH_SOCK or add keys to "
                        + "your ~/.ssh/"
                    )
            # end
        # end
        raise Exception("Only unsupported credential types allowed by remote end")

    # end


# end


@main.command("list")
@click.option("--local/--all", default=True)
def main_list(local):
    ssh_agent_setup.setup()

    repo_path = pygit2.discover_repository(os.getcwd())
    repo = pygit2.Repository(repo_path)

    prune = False  # havn't got the cred callback working

    if prune:
        with Action("Pruning old remotes...") as action:
            for remote in repo.remotes:
                remote.fetch(prune=pygit2.GIT_FETCH_PRUNE, callbacks=SSHAgentCallbacks())
                action.progress()
        # end
    # end

    print(repo.describe())

    info = {}

    fill_branch_info(info, repo.branches, islocal=True)
    fill_branch_info(info, repo.branches, islocal=False)

    fill_merged_info(info, isremote=False)
    fill_merged_info(info, isremote=True)

    rows = []

    for name in info.keys():
        data = info[name]

        if local and not data.local:
            continue

        rows.append(
            {
                "flags": "{}{}{}{}.".format(
                    "*" if data.head else " ",
                    "M" if data.up2date or data.merged else ".",
                    "P" if data.pushed else ".",
                    "D" if data.gone else ".",
                ),
                "local": "local" if data.local else ".....",
                "remote": "remote" if data.remote else "......",
                "name": name,
                "log": first_line(repo[data.target].message),
            }
        )
    # end

    max_width, _ = os.get_terminal_size(0)

    used = 5 + 1 + 5 + 1 + 6 + 1 + 30 + 1
    remaining = max_width - 1 - used

    WIDTHS = {"flags": 5, "local": 5, "remote": 6, "name": 30, "log": remaining}

    with OutputFormat("text"):
        print_table(["flags", "local", "remote", "name", "log"], rows, max_column_widths=WIDTHS)

    click.secho(" " * (max_width - 1), fg="black", bg="white")
    print("* = current checkout, M = branch is merged into master")
    print("P = local has been pushed into it's remote, D = No matching upstream branch for local")


# end


@main.command("clean")
@click.option("--delete/--dry-run", default=False)
def main_clean(delete):
    repo_path = pygit2.discover_repository(os.getcwd())
    repo = pygit2.Repository(repo_path)

    info = {}

    fill_branch_info(info, repo.branches, islocal=True)
    fill_branch_info(info, repo.branches, islocal=False)

    fill_merged_info(info, isremote=False)
    fill_merged_info(info, isremote=True)

    rows = []
    issafe = True

    for name in info.keys():
        data = info[name]
        if not data.gone:
            continue

        rows.append(
            {
                "flags": "{}local".format("*" if data.head else " "),
                "name": name,
                "log": first_line(repo[data.target].message),
            }
        )
        if data.head:
            issafe = False
    # end

    if not rows:
        print("No work to be done")
        return

    max_width, _ = os.get_terminal_size(0)

    used = 6 + 1 + 40 + 1
    remaining = max_width - 1 - used

    WIDTHS = {"flags": 6, "name": 40, "log": remaining}

    with OutputFormat("text"):
        print_table(["flags", "name", "log"], rows, max_column_widths=WIDTHS)

    if delete:
        print("Deleting local branches...")
        if not issafe:
            print("Current checkout includes a branch to be deleted.")
            return

        click.confirm("Do you want to continue?", abort=True)

        for name in info.keys():
            data = info[name]
            if not data.gone:
                continue

            repo.branches[data.key].delete()
        # end
    # end


# end


"""
http://docs.paramiko.org/en/2.4/api/config.html
http://docs.paramiko.org/en/2.4/api/agent.html
https://www.programcreek.com/python/example/52880/paramiko.SSHConfig
https://github.com/libgit2/pygit2/blob/master/test/test_credentials.py
https://github.com/MichaelBoselowitz/pygit2-examples/blob/master/examples.py
"""
