# LlmLang — common targets
.PHONY: demo test eval web tools version showcase all

ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
export PYTHONPATH := $(ROOT):$(PYTHONPATH)

demo:
	cd $(ROOT)/.. && python -m llm_lang --demo

test:
	cd $(ROOT)/.. && python -m llm_lang --test

eval:
	cd $(ROOT) && python tests/eval_suite.py

web:
	cd $(ROOT)/.. && python -m llm_lang --web

tools:
	cd $(ROOT)/.. && python -m llm_lang --tools

version:
	cd $(ROOT)/.. && python -m llm_lang --version

showcase:
	cd $(ROOT) && python examples/run_language.py examples/ultimate_showcase.ll

all: version test eval demo
	@echo "\nAll green."
