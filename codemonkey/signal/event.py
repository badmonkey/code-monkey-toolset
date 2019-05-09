import signaling


class Event:
    def __init__(self):
        self._stop_processing = False
        self._valid = True

    def __bool__(self):
        return self._valid

    def done(self):
        pass

    def cancel(self):
        pass


class EventDispatch:
    def __init__(self, evt_type):
        pass

    def connect(self, f):
        """ decorator for making func a handler """
        pass

    def add(self, f):
        pass

    def emit(self, *args, **kwargs):
        pass


################################


class TestEvent(Event):
    pass


testevnt = EventDispatch(TestEvent)


@testevnt.connect
def handler(evt: TestEvent):
    pass


testevnt.emit(TestEvent())

testevnt.emit(arg1=1, arg2=2, arg3=3)
