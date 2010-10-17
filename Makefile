test:
	python setup.py test

upload-docs:
	$(MAKE) -C docs html dirhtml
	cd docs/_build/; mv html jinja-docs; zip -r jinja-docs.zip jinja-docs; mv jinja-docs html
	scp -r docs/_build/dirhtml/* pocoo.org:/var/www/jinja.pocoo.org/
	scp -r docs/_build/jinja-docs.zip pocoo.org:/var/www/jinja.pocoo.org/

.PHONY: test
