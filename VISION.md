# LlmLang — Design Vision

> A programming language whose computational model is *a large language model plus tools*, not a von Neumann machine with an LLM bolted on.

## Core semantic commitments

- A `CallResult` is a first-class value: text + confidence + tool provenance + fingerprint.
- `if conf(x) > θ` is a real control-flow construct.
- `parallel { ... }` means independent model work can overlap.
- Models are declared, not scattered as magic strings.

## Non-goals

- Replacing Python for ordinary computation
- Being a full general-purpose language

## Success metric

Express a multi-step, tool-using agent more clearly than typical framework soup — and still read the whole language implementation in an afternoon.

## On power

LlmLang does **not** try to out-power C++, Rust, or Python as a general-purpose language. It aims to be the most capable language for programs whose primary computer is an LLM + tools.
