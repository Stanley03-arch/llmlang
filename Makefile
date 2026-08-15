# LlmLang — common targets
.PHONY: demo eval version tools run-hello run-tools run-agent all

ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
export PYTHONPATH := $(ROOT):$(PYTHONPATH)

demo:
	python -m llm_lang --demo

version:
	python -m llm_lang --version

eval:
	python -m llm_lang --eval

tools:
	python -m llm_lang --tools

run-hello:
	python -m llm_lang --run examples/hello.ll

run-tools:
	python -m llm_lang --run examples/tools.ll

run-agent:
	python -m llm_lang --run examples/agent_loop.ll

all: version eval demo tools
	@echo "\nAll green."
