# -*- coding: utf-8 -*-
"""
    jinja.translators
    ~~~~~~~~~~~~~~~~~

    The submodules of this module provide translators for the jinja ast.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""


class Translator(object):
    """
    Base class of all translators.
    """

    def process(environment, tree):
        """
        Process the given ast with the rules defined in
        environment and return a translated version of it.
        The translated object can be anything. The python
        translator for example outputs Template instances,
        a javascript translator would probably output strings.

        This is a static function.
        """
        pass
    process = staticmethod(process)
