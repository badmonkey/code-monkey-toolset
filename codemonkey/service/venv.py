from dataclasses import dataclass, field
from typing import Set

from codemonkey.lib.bus import EventBase, bus

from .util import current


@dataclass
class UninstallEvent(EventBase):
    dry_run: bool = False
    dists_to_remove: Set[str] = field(default_factory=set)


@bus.handler("venv-uninstall", UninstallEvent)
def evtPurge(evt: UninstallEvent) -> EventBase:
    evt.cancel()
    print("EVT", current.config.get_merged_section("wrench.venv"))
    return evt
