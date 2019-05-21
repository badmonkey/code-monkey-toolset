import codemonkey.lib.click as click


class Current:
    def __init__(self):
        self._obj = None

    @property
    def obj(self):
        if not self._obj:
            self._obj = click.current_obj()
            if not self._obj:
                raise RuntimeError("Missing context object")
        return self._obj

    @property
    def config(self):
        return self.obj.config

    @property
    def gitrepo(self):
        return self.obj.gitrepo


current = Current()
