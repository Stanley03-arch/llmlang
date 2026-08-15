#!/usr/bin/env python3
"""CLI entrypoint for LlmLang."""

from __future__ import annotations
import argparse
import sys
import os

# Ensure repo root is on path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from llm_lang import __version__
from language.interpreter import run_source
from backends import get_backend, probe_backend


def cmd_version(_args):
    print(f"LlmLang {__version__}")


def cmd_demo(_args):
    demo = '''
# LlmLang demo
model helper {
  system: "You are a helpful assistant. Be concise."
  temperature: 0.2
  mode: "free"
}

result = helper("What is 2 + 2? Answer with just the number.")
print result
print conf(result)

if conf(result) > 0.5 {
  print "High confidence answer"
} else {
  print "Low confidence, be careful"
}
'''
    print("=== Running LlmLang demo ===\n")
    run_source(demo, backend_name="mock")
    print("\n=== Demo finished ===")


def cmd_eval(_args):
    src = '''
model m {
  system: "You answer with a single word."
  mode: "free"
}
r = m("Say hello")
print r
assert conf(r) >= 0, "confidence must be non-negative"
print "eval ok"
'''
    run_source(src, backend_name="mock")


def cmd_probe(_args):
    info = probe_backend()
    for k, v in info.items():
        print(f"{k}: {v}")


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
    run_source(src, backend_name="openai")


def cmd_run(args):
    path = args.file
    if not os.path.isfile(path):
        print(f"File not found: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    backend_name = args.backend or "auto"
    run_source(src, backend_name=backend_name)


def main():
    parser = argparse.ArgumentParser(
        prog="llm_lang",
        description="LlmLang — programming language whose runtime is an LLM + tools",
    )
    parser.add_argument("--version", action="store_true", help="Show version")
    sub = parser.add_subparsers(dest="command")

    # also support flags for quick use
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--eval", action="store_true")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--run", metavar="FILE", help="Run a .ll file")
    parser.add_argument("--backend", default=None, help="mock|openai|auto")

    args = parser.parse_args()

    if args.version or args.command == "version":
        cmd_version(args)
    elif args.demo:
        cmd_demo(args)
    elif args.eval:
        cmd_eval(args)
    elif args.probe:
        cmd_probe(args)
    elif args.live:
        cmd_live(args)
    elif args.run:
        args.file = args.run
        cmd_run(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
