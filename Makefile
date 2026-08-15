# LlmLang — common targets
.PHONY: demo test eval version run-hello run-math all

ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
export PYTHONPATH := $(ROOT):$(PYTHONPATH)

demo:
	python -m llm_lang --demo

version:
	python -m llm_lang --version

eval:
	python -m llm_lang --eval

run-hello:
	python -m llm_lang --run examples/hello.ll

run-math:
	python -m llm_lang --run examples/math.ll

all: version eval demo
	@echo "\nAll green."
