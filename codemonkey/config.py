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

        if exename:
            subname = f"{name}:*"
            if subname in self.values:
                section.update(self.values[subname])

            subname = f"{name}:{exename}"
            if subname in self.values:
                section.update(self.values[subname])

        return section

    def subsections(self, name: str, exename: str = None, show_all: bool = False):
        test = f"{name}."
        exetest = f":{exename}" if exename else None
        subset = set()
        for section, _ in self.values.items():
            if section.startswith(test):
                section = section[len(test) :].replace(":", ".:").split(".")

                if exetest and section[-1] == exetest:
                    section = section[:-1]
                elif ":" in section[-1]:
                    continue

                len_section = len(section)
                if len_section == 1:
                    subset.add(section[0])
                elif show_all:
                    subset.add(".".join(section))

        return subset


def load(toolname: str = "monkey", configname: str = "wrench.ini", prefix: str = None) -> Config:
    prefix = prefix or toolname

    config = {}

    iniconfig = configparser.ConfigParser()

    inipath = os.path.expanduser(f"~/.config/{toolname}/{configname}")
    if os.path.isfile(inipath):
        iniconfig.read(inipath)

        update_dict_from_config(config, iniconfig)

        iniconfig = configparser.ConfigParser()

    if os.path.exists("setup.cfg"):
        iniconfig.read("setup.cfg")

        update_dict_from_config(config, iniconfig, whiteprefix=prefix)

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
            adict[newsection][key] = as_typed(val)


def as_typed(value):
    if value.startswith("list:"):
        value = as_list(value[5:])
    elif value.startswith("set:"):
        value = as_set(value[4:])
    elif value.startswith("tuple:"):
        value = as_tuple(value[6:])
    elif value.startswith("int:"):
        value = int(value[4:].strip())
    elif "\n" in value:
        value = as_list(value)
    else:
        value = maybe_as_bool(value)

    return value


def as_set(value):
    if isinstance(value, str):
        if "\n" in value:
            return as_set(as_list(value))
        if "," in value:
            return set(x.strip() for x in value.split(","))
        return set([value])
    if isinstance(value, (tuple, list)):
        itemset = set()
        for x in value:
            itemset = itemset | as_set(x)
        return itemset
    raise Exception(f"No idea what to do with {value}")


def as_list(value: str):
    return [x.strip() for x in value.splitlines() if x]


def as_tuple(value: str):
    if "\n" in value:
        return tuple(as_typed(x) for x in as_list(value))
    if "," in value:
        return tuple(as_typed(x.strip()) for x in value.split(","))
    return (value,)


def maybe_as_bool(value: str):
    tstvalue = value.lower()
    if tstvalue in ("true", "yes", "1"):
        return True
    if tstvalue in ("false", "no", "0"):
        return False
    return value
