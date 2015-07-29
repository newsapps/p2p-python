.PHONY: test

test:
	clear
	pep8 p2p
	pyflakes p2p
	coverage run setup.py test
	coverage report -m
