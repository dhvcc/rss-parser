from importlib import import_module
from importlib.metadata import version

_pydantic_version = version("pydantic")


def import_v1_pydantic(relative_submodule_path: str = ""):
    if _pydantic_version[0] == "2":
        return import_module("pydantic.v1" + relative_submodule_path)
    else:
        return import_module("pydantic" + relative_submodule_path)
