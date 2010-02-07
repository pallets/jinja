test:
	nosetests --with-doctest jinja2 tests

2to3:
	rm -rf py3k
	mkdir py3k
	cp -R jinja2 py3k
	cp -R tests py3k
	2to3 jinja2 tests > py3k/convert.patch
	cd py3k; patch -p0 < convert.patch

.PHONY: test
