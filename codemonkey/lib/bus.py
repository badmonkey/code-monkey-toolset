import asyncio
from typing import Any, Callable, List, Mapping, Type


class EventBase:
    def __init__(self):
        self._stop_processing: bool = False
        self._valid: bool = True

    def run_immediately(self):
        self._stop_processing = True

    def cancel(self):
        self._valid = False
        self._stop_processing = True

    @property
    def valid(self) -> bool:
        return self._valid

    @property
    def stopped(self) -> bool:
        return self._stop_processing


CheckType = Callable[[EventBase], None]
ProcessorType = Callable[[EventBase], Any]
NotifyType = Callable[[EventBase, Any], None]


def _is_coro(o):
    return asyncio.iscoroutine(o) or asyncio.iscoroutinefunction(o)


def _as_coro(o):
    if _is_coro(o):
        return o
    return asyncio.coroutine(o)


def _sync_call(f, *args, **kwargs):
    if _is_coro(f):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))
    return f(*args, **kwargs)


class Slot:
    def __init__(self, parent, evtname: str, evttype: Type[EventBase], handler: ProcessorType):
        self.parent = parent
        self.evtname: str = evtname
        self.evttype: Type[evttype] = evttype
        self.checks: List[CheckType] = []
        self.handler: ProcessorType = handler
        self.notifies: List[NotifyType] = []

    def __call__(self, evt):
        result = None

        for checkf in self.checks:
            _sync_call(checkf, evt)
            if evt.stopped:
                break

        if evt.valid:
            result = _sync_call(self.handler, evt)

            for notifyf in self.notifies:
                _sync_call(notifyf, evt, result)

        return result

    @asyncio.coroutine
    def _call_and_notify(self, evt):
        result = _sync_call(self.handler, evt)

        for notifyf in self.notifies:
            notifyf = _as_coro(notifyf)
            asyncio.create_task(notifyf(evt, result))

    @asyncio.coroutine
    def async_emit(self, evt):
        for checkf in self.checks:
            _sync_call(checkf, evt)
            if evt.stopped:
                break

        if evt.valid:
            return asyncio.create_task(self._call_and_notify(evt))
        return None

    def _add(self, where: List, f: Callable):
        if f in where:
            raise Exception("Already subscribed")
        where.append(f)

    def check(self, f):
        self._add(self.checks, f)
        return f

    def notify(self, f):
        self._add(self.notifies, _as_coro(f))
        return f


class Bus:
    def __init__(self):
        self.slots: Mapping[str, Slot] = {}
        self.loop = asyncio.get_event_loop()

    def emit(self, evtname, *args, **kwargs):
        if evtname not in self.slots:
            raise Exception(f"No handler for event {evtname}")
        slot = self.slots[evtname]
        evt = Bus._make_event(slot.evttype, *args, **kwargs)

        return slot(evt)

    def async_emit(self, evtname, *args, **kwargs):
        if evtname not in self.slots:
            raise Exception(f"No handler for event {evtname}")
        slot = self.slots[evtname]
        evt = Bus._make_event(slot.evttype, *args, **kwargs)

        return asyncio.create_task(slot.async_emit(evt))

    def wait(self):
        while True:
            pending_tasks = asyncio.all_tasks(self.loop)
            print("TASKS", len(pending_tasks))
            if not pending_tasks:
                break
            self.loop.run_until_complete(asyncio.gather(*pending_tasks))

        self.loop.close()

    @staticmethod
    def _make_event(evttype, *args, **kwargs):
        if args:
            if isinstance(args[0], evttype):
                return args[0]
            return evttype(*args, **kwargs)
        return evttype(**kwargs)

    def handler(self, evtname: str, evttype: Type[EventBase] = EventBase):
        def decorator(f):
            if evtname in self.slots:
                raise Exception(f"Already an event handler for {evtname}")
            slot = Slot(self, evtname, evttype, f)
            self.slots[evtname] = slot
            return slot

        return decorator


bus = Bus()
