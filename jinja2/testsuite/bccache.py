# -*- coding: utf-8 -*-
"""
    jinja2.testsuite.bccache
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Tests the bytecode cache.

    :copyright: (c) 2010 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import unittest
import tempfile
import shutil

from jinja2.testsuite import JinjaTestCase, package_loader

from jinja2 import Environment, FileSystemBytecodeCache


class FilesystemCacheTestCase(JinjaTestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cache = FileSystemBytecodeCache(self.tmp)
        self.env = Environment(loader=package_loader,
                               bytecode_cache=self.cache)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_render_template(self):
        # templates should render normally if a cache is configured
        tmpl = self.env.get_template('foo/test.html')
        assert tmpl.render() == 'FOO'


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(FilesystemCacheTestCase))
    return suite
