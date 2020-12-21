
# Default/Help message
help:
	@echo "The dna Makefile. The following rules are available:"
	@echo "|- venv            make the Python dev environment"
	@echo "|- lint            run linters (currently: black)"
	@echo "|- clean           delete all build files"
	@echo "|  |- clean_dna    delete all dna build files"
	@echo "|  \`- clean_docs   delete all documentation build files"
	@echo "|- all             compile package and documentation"
	@echo "|  |- dna          compile package"
	@echo "|  \`- docs         compile documentation"
	@echo "|- dev             develop documentation"
	@echo "|- upload          upload the compiled package to PyPI"
	@echo "|- key_up          upload with $(shell pwd)/.pypirc"
	@echo "\`- deploy          alias for venv all key_up"

# Set up the development environment
venv:
	python3 -m venv env
	env/bin/pip install -r requirements.txt

# Run black
lint:
	env/bin/black .

# Clean build files for DNA
clean_dna:
	rm -rf build dist docker_dna.egg-info
	rm -rf dna/__pycache__ dna/utils/__pycache__

# Clean build files for documentation
clean_sphinx:
	cd docs && ${MAKE} clean

# Clean build files for DNA and documentation
clean: clean_dna clean_sphinx

# Build DNA package
dna: clean_dna lint
	env/bin/python setup.py sdist bdist_wheel

# Build documentation
docs: clean_sphinx
	cd docs && ${MAKE} dirhtml

# Build DNA package and documentation
all: dna docs

# Develop documentation
dev:
	cd docs && ${MAKE} live

# Upload DNA package to PyPI
upload:
	env/bin/twine upload dist/*

# Upload using .pypirc
key_up:
	env/bin/twine upload dist/* --config-file .pypirc

pypi: venv all key_up
