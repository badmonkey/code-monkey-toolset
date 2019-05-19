from codemonkey.lib.bus import EventBase, bus


class GitEvent(EventBase):
    pass


class GitMakeBranchEvent(GitEvent):
    pass


@bus.handler("git-make-branch", GitMakeBranchEvent)
def evtMakeBranch(evt: GitMakeBranchEvent) -> int:
    return 0
