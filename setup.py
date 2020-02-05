import re

from setuptools import find_packages
from setuptools import setup

with open("src/jinja2/__init__.py", "rt", encoding="utf8") as f:
    version = re.search(r'__version__ = "(.*?)"', f.read(), re.M).group(1)

setup(
    name="Jinja2",
    version=version,
    url="https://palletsprojects.com/p/jinja/",
    project_urls={
        "Documentation": "https://jinja.palletsprojects.com/",
        "Code": "https://github.com/pallets/jinja",
        "Issue tracker": "https://github.com/pallets/jinja/issues",
    },
    license="BSD-3-Clause",
    maintainer="Pallets",
    maintainer_email="contact@palletsprojects.com",
    description="A very fast and expressive template engine.",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: HTML",
    ],
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=["MarkupSafe>=1.1"],
    extras_require={"i18n": ["Babel>=2.1"]},
    entry_points={"babel.extractors": ["jinja2 = jinja2.ext:babel_extract[i18n]"]},
)
