import configparser
import os
from dataclasses import dataclass
from typing import Dict

SectionType = Dict[str, str]
ConfigType = Dict[str, SectionType]


@dataclass
class ConfigInfo:
    key: str
    value: str
    src: str
    vartype: str

    def format(self):
        return f"{self.src} | {self.key};{self.vartype}: {self.value}"


def make_info_dict(vals, srcs, types):
    data = {}

    for k, v in vals.items():
        data[k] = ConfigInfo(key=k, value=v, src=srcs[k], vartype=types[k])
    return data


class Config:
    def __init__(self, values, where, types):
        self.values = values
        self.fromwhere = where
        self.types = types

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

    def get_section_info(self, name: str, exename: str = None) -> SectionType:
        section = {}

        if name in self.values:
            section.update(
                make_info_dict(self.values[name], self.fromwhere[name], self.types[name])
            )

        if exename:
            subname = f"{name}:*"
            if subname in self.values:
                section.update(
                    make_info_dict(
                        self.values[subname], self.fromwhere[subname], self.types[subname]
                    )
                )

            subname = f"{name}:{exename}"
            if subname in self.values:
                section.update(
                    make_info_dict(
                        self.values[subname], self.fromwhere[subname], self.types[subname]
                    )
                )

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
    which = {}
    types = {}

    def read_and_merge(fname, ourprefix=None):
        inipath = os.path.expanduser(fname)
        if os.path.isfile(inipath):
            iniconfig = configparser.ConfigParser()
            iniconfig.read(inipath)

            update_dict_from_config(config, which, types, iniconfig, fname, ourprefix=ourprefix)
            return True
        return False

    read_and_merge(f"~/.config/{toolname}/{configname}")

    read_and_merge(f".project/{configname}")

    read_and_merge(configname)
    read_and_merge("setup.cfg", ourprefix=prefix)

    return Config(config, which, types)


def update_dict_from_config(adict, srcdict, types, config, filename, ourprefix=None):
    if ourprefix:
        _our_check = f"{ourprefix}."
        _our_len = len(_our_check)

        def check_if_our(x):
            return x.startswith(_our_check)

        def trim_our(x):
            return x[_our_len:]

    else:

        def check_if_our(x):
            return True

        def trim_our(x):
            return x

    for section in config.sections():
        if not check_if_our(section):
            continue

        newsection = trim_our(section)
        adict.setdefault(newsection, {})
        srcdict.setdefault(newsection, {})
        types.setdefault(newsection, {})

        for key, val in config.items(section):
            key, val, vtype = process_keyvalue(key, val)
            adict[newsection][key] = val
            types[newsection][key] = vtype
            srcdict[newsection][key] = f"{filename}[{section}]"


def fix_type(ktype, vtype):
    if ktype:
        if vtype:
            if ktype == vtype:
                return ktype
            raise Exception(f"type {ktype} doesn't match {vtype}")
        return ktype

    return vtype


def get_value_type(value, force_tuple=False):
    if ";" in value:
        vtype, _, partvalue = value.partition(";")

        if force_tuple:
            return ("tuple", partvalue) if vtype == "tuple" else ("tuple", value)

        partvalue = partvalue.lstrip()
        return vtype, partvalue
    return ("tuple" if force_tuple else None), value


def process_keyvalue(key, value):
    ktype = None
    vtype = None

    if ";" in key:
        key, _, ktype = key.rpartition(";")

    vtype, value = get_value_type(value, force_tuple=(ktype == "tuple"))
    print(key, "|", ktype, "|", vtype, "|", value)

    vtype = fix_type(ktype, vtype)
    vtype, value = as_typed(vtype, value)

    return key, value, vtype


def process_value(value):
    vtype = None

    if ";" in value:
        vtype, _, value = value.partition(";")
        value = value.lstrip()

    return as_typed(vtype, value)


def as_typed(vtype, value):
    if vtype == "list":
        return vtype, as_list(value)
    if vtype == "set":
        return vtype, as_set(value)
    if vtype == "tuple":
        return vtype, as_tuple(value)
    if vtype == "int":
        return vtype, int(value.strip())
    if vtype == "str":
        return vtype, str(value)
    if "\n" in value:
        return "list", as_list(value)

    return maybe_as_bool(value)


def as_list(value: str):
    return [x.strip() for x in value.splitlines() if x]


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


def as_tuple(value: str):
    if "\n" in value:
        # valid types: str/bool, int, set, tuple
        return tuple(process_value(x) for x in as_list(value))
    if "," in value:
        # valid types: str/bool, int
        return tuple(process_value(x.strip()) for x in value.split(","))
    return (value,)


def maybe_as_bool(value: str):
    tstvalue = value.lower()
    if tstvalue in ("true", "yes", "1"):
        return "bool", True
    if tstvalue in ("false", "no", "0"):
        return "bool", False
    return "str", value
