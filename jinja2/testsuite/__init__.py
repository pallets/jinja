# -*- coding: utf-8 -*-
"""
    jinja2.testsuite
    ~~~~~~~~~~~~~~~~

    All the unittests of Jinja2.  These tests can be executed by
    either running run-tests.py using multiple Python versions at
    the same time.

    :copyright: (c) 2010 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import os
import sys
import unittest
from jinja2 import loaders


here = os.path.dirname(os.path.abspath(__file__))

dict_loader = loaders.DictLoader({
    'justdict.html':        'FOO'
})
package_loader = loaders.PackageLoader('jinja2.testsuite.res', 'templates')
filesystem_loader = loaders.FileSystemLoader(here + '/res/templates')
function_loader = loaders.FunctionLoader({'justfunction.html': 'FOO'}.get)
choice_loader = loaders.ChoiceLoader([dict_loader, package_loader])
prefix_loader = loaders.PrefixLoader({
    'a':        filesystem_loader,
    'b':        dict_loader
})


class JinjaTestCase(unittest.TestCase):

    ### use only these methods for testing.  If you need standard
    ### unittest method, wrap them!

    def assert_equal(self, a, b):
        return self.assertEqual(a, b)

    def assert_raises(self, *args, **kwargs):
        return self.assertRaises(*args, **kwargs)


def suite():
    from jinja2.testsuite import ext, filters, core_tags, loader
    suite = unittest.TestSuite()
    suite.addTest(ext.suite())
    suite.addTest(filters.suite())
    suite.addTest(core_tags.suite())
    suite.addTest(loader.suite())
    return suite
