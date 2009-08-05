test:
	cd tests; nosetests -v

2to3:
	rm -rf py3k
	mkdir py3k
	cp -R jinja2 py3k
	2to3 jinja2 > py3k/convert.patch
	cd py3k; patch -p0 < convert.patch

.PHONY: test
