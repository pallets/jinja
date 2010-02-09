test:
	nosetests --with-doctest jinja2 tests

2to3:
	rm -rf build/lib
	python3 setup.py build

.PHONY: test
