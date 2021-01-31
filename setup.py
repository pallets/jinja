import re

from setuptools import setup

with open("src/jinja2/__init__.py", encoding="utf8") as f:
    version = re.search(r'__version__ = "(.*?)"', f.read(), re.M).group(1)

# Metadata goes in setup.cfg. These are here for GitHub's dependency graph.
setup(
    name="Jinja2",
    version=version,
    install_requires=["MarkupSafe>=1.1"],
    extras_require={"i18n": ["Babel>=2.1"]},
)
