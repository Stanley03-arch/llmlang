#!/usr/bin/env python3
"""Run an LlmLang (.ll) program."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from language.interpreter import run_source

def main():
    if len(sys.argv) < 2:
        path = os.path.join(os.path.dirname(__file__), "hello.ll")
    else:
        path = sys.argv[1]
    with open(path) as f:
        source = f.read()
    print("=== Running LlmLang program ===\n")
    interp = run_source(source, mock=True)
    print("\n=== Program finished ===")
    if interp.output:
        print("Captured output:")
        for line in interp.output:
            print(" ", line)

if __name__ == "__main__":
    main()
