PYTHON ?= python3
NODE ?= node
NPM ?= npm
FIGURE_PYTHON ?= .figure-env/bin/python
.PHONY: validate test install-scorers replay figure-env figures website integrity reproduce
validate:
	$(PYTHON) scripts/validate.py
	$(PYTHON) scripts/reference_aggregates.py
test:
	$(PYTHON) -m unittest discover -s scripts -p 'test_*.py'
install-scorers:
	$(NODE) examples/install.mjs
replay:
	$(NODE) examples/run.mjs
figure-env:
	$(PYTHON) -m venv .figure-env
	.figure-env/bin/python -m pip install --requirement requirements-figures.txt
figures:
	$(FIGURE_PYTHON) scripts/figures_public.py --out generated/figures
website:
	$(NPM) --prefix ../research_companion ci
	$(NPM) --prefix ../research_companion test
	$(NPM) --prefix ../research_companion run build
	$(PYTHON) ../tools/build_site.py
integrity:
	$(PYTHON) scripts/verify_bundle.py ..
reproduce: validate test integrity
