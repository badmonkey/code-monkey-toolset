import builtins

import deprecated as deprecate_module
from public import install

install()

if not hasattr(builtins, "deprecated"):
    builtins.deprecated = deprecate_module.deprecated
