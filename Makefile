PYTHON ?= python3

.PHONY: all test plots clean

all: test

test:
	mkdir -p build
	$(PYTHON) scripts/check.py

plots: test
	$(PYTHON) scripts/plot.py

clean:
	rm -rf build/*
