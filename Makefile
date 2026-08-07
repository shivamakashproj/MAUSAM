# Makefile for Mausam Weather Dashboard

# Variables
VENV_DIR := venv
PYTHON := $(VENV_DIR)\\Scripts\\python
PIP := $(VENV_DIR)\\Scripts\\pip

# Default target
.PHONY: all
all: run

# Create virtual environment
.PHONY: venv
venv:
	python -m venv $(VENV_DIR)

# Install dependencies
.PHONY: install
install: venv
	$(PIP) install -r requirements.txt

# Run the Flask app
.PHONY: run
run: install
	$(PYTHON) app.py

# Clean generated files
.PHONY: clean
clean:
	rmdir /s /q $(VENV_DIR) || true
	del /f /q *.pyc || true
