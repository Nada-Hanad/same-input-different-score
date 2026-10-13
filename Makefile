PYTHON ?= python3
.PHONY: verify test build-site manifest package serve
verify:
	$(PYTHON) tools/verify_publication.py
	$(PYTHON) tools/privacy_scan.py
test:
	$(MAKE) -C reproducibility_artifact validate test
	npm --prefix research_companion ci
	npm --prefix research_companion run typecheck
	npm --prefix research_companion test
	$(PYTHON) -m unittest discover -s tools -p 'test_*.py'
build-site:
	npm --prefix research_companion run build
	$(PYTHON) tools/build_site.py
manifest:
	$(PYTHON) tools/refresh_manifest.py
package:
	$(PYTHON) tools/package_publication.py
serve:
	$(PYTHON) tools/serve_prefix.py
