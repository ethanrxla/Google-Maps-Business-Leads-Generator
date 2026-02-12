.PHONY: sanity stabilize test-all

sanity:
	. .venv/bin/activate && python cli.py --help >/dev/null
	. .venv/bin/activate && pytest -q tests/test_cli.py tests/test_paths.py

stabilize:
	. .venv/bin/activate && pytest -v tests/test_repositories.py tests/test_pipeline_models.py tests/test_quality_gates.py tests/test_domain_resolver.py

test-all:
	. .venv/bin/activate && pytest -v tests/
