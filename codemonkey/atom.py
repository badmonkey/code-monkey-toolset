import sys as _sys


def _valid_name(name):
    import keyword

    if name:
        name = _sys.intern(str(name))
        if name.isidentifier() and not keyword.iskeyword(name) and not name.startswith("_"):
            return name
    raise AttributeError(f"Atom({name}) must be identifier, !keyword, and doesn't start with '_'")


if _sys.version_info >= (3, 8):

    def __getattr__(name):
        if name.startswith("__"):
            if name not in globals():
                raise AttributeError(f"No {name} in {__name__}")

        name = _valid_name(name)
        if name not in globals():
            globals()[name] = name

        return globals()[name]


else:

    class Wrapper:
        def __init__(self, wrapped):
            self._wrapped = wrapped

        def __getattr__(self, name):
            if name.startswith("__"):
                return self.__getattribute__(name)

            name = _valid_name(name)
            setattr(self, name, name)

            return name

        def __getitem__(self, item):
            return item

    _sys.modules[__name__] = Wrapper(_sys.modules[__name__])
