test:
	python setup.py test

website:
	$(MAKE) -C docs dirhtml SPHINXOPTS=-Awebsite=1

.PHONY: test
