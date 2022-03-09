from pathlib import Path

import pytest

from jinja2 import loaders
from jinja2.environment import Environment


@pytest.fixture
def env():
    """returns a new environment."""
    return Environment()


@pytest.fixture
def dict_loader():
    """returns DictLoader"""
    return loaders.DictLoader({"justdict.html": "FOO"})


@pytest.fixture
def package_loader():
    """returns PackageLoader initialized from templates"""
    return loaders.PackageLoader("res", "templates")


@pytest.fixture
def filesystem_loader():
    """returns FileSystemLoader initialized to res/templates directory"""
    here = Path(__file__).parent.resolve()
    return loaders.FileSystemLoader(here / "res" / "templates")


@pytest.fixture
def function_loader():
    """returns a FunctionLoader"""
    return loaders.FunctionLoader({"justfunction.html": "FOO"}.get)


@pytest.fixture
def choice_loader(dict_loader, package_loader):
    """returns a ChoiceLoader"""
    return loaders.ChoiceLoader([dict_loader, package_loader])


@pytest.fixture
def prefix_loader(filesystem_loader, dict_loader):
    """returns a PrefixLoader"""
    return loaders.PrefixLoader({"a": filesystem_loader, "b": dict_loader})


@pytest.fixture
def custom_escape_func():
    """Return a simple custom escape function"""

    def dollar_to_eur(s):
        return str(s).replace("$", "€")

    return dollar_to_eur


@pytest.fixture
def return_custom_autoescape(custom_escape_func):
    """return a simple example for a custom escape function"""

    def do_return_autoescape(suffix):
        return custom_escape_func

    return do_return_autoescape


@pytest.fixture
def env_custom_autoescape(return_custom_autoescape):
    """return a simple example for a custom escape function"""
    return Environment(autoescape=return_custom_autoescape)
