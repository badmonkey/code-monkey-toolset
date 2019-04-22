import configparser
import os
from typing import Dict

SectionType = Dict[str, str]
ConfigType = Dict[str, SectionType]


class Config:
    def __init__(self, values):
        self.values = values

    def get_section(self, name: str) -> SectionType:
        if name in self.values:
            return self.values[name]
        return {}

    def get_merged_section(self, name: str, exename: str = None) -> SectionType:
        section = {}

        if name in self.values:
            section.update(self.values[name])

        subname = f"{name}:*"
        if subname in self.values:
            section.update(self.values[subname])

        if exename:
            subname = f"{name}:{exename}"
            if subname in self.values:
                section.update(self.values[subname])

        return section


def load(toolname: str = "monkey", configname: str = "wrench.conf") -> Config:
    config = {}

    iniconfig = configparser.ConfigParser()

    inipath = os.path.expanduser(f"~/.config/{toolname}/{configname}")
    if os.path.exists(inipath):
        iniconfig.read(inipath)

        update_dict_from_config(config, iniconfig)

        iniconfig = configparser.ConfigParser()

    if os.path.exists("setup.cfg"):
        iniconfig.read("setup.cfg")

        update_dict_from_config(config, iniconfig, whiteprefix=toolname)

        iniconfig = configparser.ConfigParser()

    return Config(config)


def update_dict_from_config(adict, config, whiteprefix=None):
    if whiteprefix:
        _white_check = f"{whiteprefix}."
        _white_len = len(_white_check)

        def white_check(x):
            return x.startswith(_white_check)

        def white_trim(x):
            return x[_white_len:]

    else:

        def white_check(x):
            return True

        def white_trim(x):
            return x

    for section in config.sections():
        if not white_check(section):
            continue

        newsection = white_trim(section)
        adict.setdefault(newsection, {})
        for key, val in config.items(section):
            # place to do some typed conversions
            adict[newsection][key] = val


def as_set(param):
    if isinstance(param, (tuple, list)):
        itemset = set()
        for x in param:
            itemset = itemset | as_set(x)
        return itemset
    if isinstance(param, str):
        if "," in param:
            return set(param.split(","))
        return set([param])
    raise Exception(f"No idea what to do with {param}")


def as_list(value):
    return [x.strip() for x in value.splitlines() if x]
