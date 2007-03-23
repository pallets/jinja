#
# Jinja Makefile
# ~~~~~~~~~~~~~~
#
# Shortcuts for various tasks.
#
# :copyright: 2007 by Armin Ronacher.
# :license: BSD, see LICENSE for more details.
#

test:
	@(cd tests; py.test $(TESTS))

documentation:
	@(cd docs; ./generate.py)

webpage:
	@(cd www; ./generate.py)

release:
	@(python2.3 setup.py release bdist_egg; python2.4 setup.py release bdist_egg; python2.5 setup.py release bdist_egg sdist)
