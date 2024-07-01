import asyncio
from pathlib import Path

import pytest
import trio

from jinja2 import loaders
from jinja2.environment import Environment


def _asyncio_run(async_fn, *args):
    return asyncio.run(async_fn(*args))


@pytest.fixture(params=[_asyncio_run, trio.run], ids=["asyncio", "trio"])
def run_async_fn(request):
    return request.param


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
