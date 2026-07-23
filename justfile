set shell := ["bash", "-cu"]

lint:
	python3 -m unittest tests/test_skills_index.py

precommit:
	just lint
