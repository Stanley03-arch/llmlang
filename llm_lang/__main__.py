#!/usr/bin/env python3
"""CLI entrypoint for LlmLang."""

from __future__ import annotations
import argparse
import sys
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from llm_lang import __version__
from language.interpreter import run_source
from backends import get_backend, probe_backend
from tools.registry import list_tools
from library.trace import Trace, set_trace


def cmd_version(_args):
    print(f"LlmLang {__version__}")


def cmd_demo(_args):
    demo = '''
model helper {
  system: "You are a helpful assistant. Be concise."
  temperature: 0.2
  mode: "free"
  min_conf: 0.5
  max_retries: 1
}

result = helper("What is 2 + 2? Answer with just the number.")
print result
print "confidence:", conf(result)
print "attempts:", result

r = calc("10 + 5")
print "tool calc:", r
'''
    print("=== Running LlmLang demo ===\n")
    trace = Trace(enabled=True)
    set_trace(trace)
    run_source(demo, backend_name="mock", base_dir=_ROOT, trace=trace)
    print("\n=== Trace summary ===")
    print(trace)
    print(trace.summary())
    print("=== Demo finished ===")


def cmd_eval(_args):
    src = '''
model m {
  system: "You answer with a single word."
  mode: "free"
  min_conf: 0.5
}
r = m("Say hello")
assert conf(r) >= 0, "confidence must be non-negative"
assert schema_ok(r)
t = calc("2+2")
assert t, "calc should succeed"
print "eval ok"
'''
    run_source(src, backend_name="mock", base_dir=_ROOT)


def cmd_probe(_args):
    info = probe_backend()
    for k, v in info.items():
        print(f"{k}: {v}")


def cmd_tools(_args):
    for name in list_tools():
        print(name)


def cmd_live(args):
    if not (os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")):
        print("Set OPENAI_API_KEY (or LLM_API_KEY) first.")
        sys.exit(1)
    src = '''
model assistant {
  system: "You are concise and accurate."
  temperature: 0.3
  mode: "free"
}
answer = assistant("In one sentence, what is LlmLang?")
print answer
print "confidence:", conf(answer)
'''
    trace = Trace(enabled=True) if args.trace else None
    run_source(src, backend_name="openai", base_dir=_ROOT, trace=trace,
               trace_path=args.trace if isinstance(args.trace, str) else None)


def cmd_run(args):
    path = args.file
    if not os.path.isfile(path):
        print(f"File not found: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    backend_name = args.backend or "auto"
    base = os.path.dirname(os.path.abspath(path)) or "."
    trace = None
    trace_path = None
    if args.trace:
        trace = Trace(enabled=True)
        set_trace(trace)
        if isinstance(args.trace, str) and args.trace not in ("1", "true", "True"):
            trace_path = args.trace
        else:
            trace_path = path + ".trace.json"
    run_source(src, backend_name=backend_name, base_dir=base, trace=trace, trace_path=trace_path)


def main():
    parser = argparse.ArgumentParser(
        prog="llm_lang",
        description="LlmLang — programming language whose runtime is an LLM + tools",
    )
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--eval", action="store_true")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--tools", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--run", metavar="FILE")
    parser.add_argument("--backend", default=None, help="mock|openai|auto")
    parser.add_argument(
        "--trace",
        nargs="?",
        const="1",
        default=None,
        help="Enable execution trace; optional path for JSON output",
    )

    args = parser.parse_args()

    if args.version:
        cmd_version(args)
    elif args.demo:
        cmd_demo(args)
    elif args.eval:
        cmd_eval(args)
    elif args.probe:
        cmd_probe(args)
    elif args.tools:
        cmd_tools(args)
    elif args.live:
        cmd_live(args)
    elif args.run:
        args.file = args.run
        cmd_run(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
