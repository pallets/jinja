# -*- coding: utf-8 -*-
"""
    Jinja fabfile
    ~~~~~~~~~~~~~

    Shortcuts for various tasks.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""


def test():
    """Run the testsuite."""
    local("cd tests; py.test")


def pylint():
    """Run pylint."""
    local("pylint --rcfile scripts/pylintrc jinja")


def release(**kwargs):
    """Release, tag and upload Jinja2 to the Cheeseshop."""
    import re
    _version_re = re.compile(r'VERSION\s*=\s["\'](.*?)["\']')
    f = file("setup.py")
    try:
        for line in f:
            match = _version_re.match(line)
            if match is not None:
                version = match.group(1)
                break
        else:
            raise RuntimeError('no version def in setup.py :-/')
    finally:
        f.close()

    local('hg tag -m "%s" "%s"' % ('tagged %r' % version, version))
    local('python setup.py release sdist upload')
