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
