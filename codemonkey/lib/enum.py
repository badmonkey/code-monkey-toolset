import collections
import sys


def _valid_name(name):
    import keyword

    if name:
        name = sys.intern(str(name))
        if name.isidentifier() and not keyword.iskeyword(name) and not name.startswith("_"):
            return name
    raise ValueError(f"Enum({name}) must be identifier, !keyword, and doesn't start with '_'")


def make(*args, _uppercase=False, _cls=None, **kwargs):
    if args:
        keys = [_valid_name(k) for k in args]
        if _uppercase:
            values = [sys.intern(k.upper()) for k in keys]
        else:
            values = keys
    elif kwargs:
        keys = [_valid_name(k) for k in kwargs]
        values = list(kwargs.values())
    else:
        raise TypeError("No enum members given")

    if _cls:
        values = [_cls(k, v) for k, v in zip(keys, values)]

    Enum = collections.namedtuple("Enum", keys)
    return Enum(*values)
