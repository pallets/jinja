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

test-coverage:
	@(cd tests; py.test -C $(TESTS))

html-documentation:
	@(cd docs; make html)

pdf-documentation:
	@(cd docs; make latex; cd _build/latex; make all-pdf)

webpage:
	@(cd ../www; ./generate.py)

pylint:
	@pylint --rcfile scripts/pylintrc jinja
