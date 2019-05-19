import asyncio
from typing import Callable, List, Type, TypeVar, Union

from codemonkey.atom import NOTIFY, SLOT  # noqa:E0611

T = TypeVar("T")


def _is_coro(o):
    return asyncio.iscoroutine(o) or asyncio.iscoroutinefunction(o)


class Base:
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


def Manager(evt_type: Type[Base], processor, name: str = None):  # noqa:C901
    class Signal:
        Name = name
        EventType = evt_type
        SlotType = Callable[[EventType], None]
        ProcessorType = Callable[[EventType], T]
        NotifyType = Callable[[T, EventType], None]
        Processor: ProcessorType = processor

        def __init__(self):
            self.slots: List[Signal.SlotType] = []
            self.subscribers: List[Signal.NotifyType] = []

        def is_connected(self, x: Union[SlotType, NotifyType]):
            """ Check if a slot is connected to this signal """
            return SLOT if x in self.slots else NOTIFY if x in self.subscribers else False

        def connect(self, slot: SlotType):
            """ decorator for connecting a ``slot`` to this signal """

            if not self.is_connected(slot):
                self.slots.append(slot)
            return slot

        def subscribe(self, sub: NotifyType):
            if sub not in self.subscribers:
                self.subscribers.append(sub)
            return sub

        def emit(self, *args, **kwargs):
            evt = Signal._make_Event(*args, **kwargs)
            result = None

            for slotf in self.slots:
                slotf(evt)
                if evt.stopped:
                    break
            if evt.valid:
                result = Signal.Processor(evt)

                for notifyf in self.subscribers:
                    notifyf(result, evt)
            return result, evt

        def __repr__(self):
            return u"<Signal: '{}'. Slots={} Notify={}>".format(
                Signal.Name or "anonymous", len(self.slots), len(self.subscribers)
            )

        @staticmethod
        def _make_Event(*args, **kwargs):
            if args:
                if isinstance(args[0], Signal.EventType):
                    return args[0]
                return Signal.EventType(*args, **kwargs)
            return Signal.EventType(**kwargs)

    return Signal()
