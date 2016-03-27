#!/usr/bin/env bash
# Ideally, be sure you are in a virtualenv (activate with `source venv/bin/activate`)
pip install -r dev-requirements.txt
pip install -r requirements.txt
# prepare fixture, which has to be downloaded manually
src/python/btank/tests/fixtures/setup_fixtures
git clone --branch=v0.17.3 https://github.com/shotgunsoftware/tk-core
