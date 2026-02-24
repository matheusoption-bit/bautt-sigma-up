.PHONY: test test-atlas test-delta test-api

test:
	bash scripts/run_tests.sh

test-atlas:
	cd services/atlas-engine && PYTHONPATH=src pytest tests -v

test-delta:
	cd services/delta-engine && PYTHONPATH=src pytest tests -v

test-api:
	cd services/atlas-api && PYTHONPATH=src:../atlas-engine/src:../delta-engine/src pytest tests -v
