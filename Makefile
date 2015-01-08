#!/usr/bin/make
PYTHON := /usr/bin/env python

sync-charm-helpers: scripts/charm_helpers_sync.py
	@$(PYTHON) scripts/charm_helpers_sync.py -c charm-helpers.yaml
