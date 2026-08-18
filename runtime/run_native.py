"""Run pure LlmLang via Go direct codegen (can beat CPython)."""

from __future__ import annotations
from typing import Any, Dict, Optional
import json, os, subprocess, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_codegen_build(source: str) -> Dict[str, Any]:
    from runtime.codegen_go import codegen_go
    t0 = time.perf_counter()
    go_src = codegen_go(source)
    d = tempfile.mkdtemp(prefix="ll_go_b_")
    path = os.path.join(d, "main.go")
    bin_path = os.path.join(d, "prog")
    with open(path, "w") as f:
        f.write(go_src)
    subprocess.check_call(["go", "build", "-o", bin_path, path], cwd=d)
    build_ms = (time.perf_counter() - t0) * 1000
    t1 = time.perf_counter()
    out = subprocess.check_output([bin_path], text=True)
    run_ms = (time.perf_counter() - t1) * 1000
    data = json.loads(out)
    data["build_ms"] = build_ms
    data["run_ms"] = run_ms
    data["mode"] = "go_codegen_build"
    return data


def benchmark_vs_python(n: int = 500_000) -> Dict[str, Any]:
    ll = f"s = 0\ni = 0\nwhile i < {n} {{\n  s = s + i\n  i = i + 1\n}}\nprint s\n"
    results: Dict[str, Any] = {"n": n}
    t0 = time.perf_counter()
    s = 0
    i = 0
    while i < n:
        s = s + i
        i = i + 1
    results["hand_python_ms"] = (time.perf_counter() - t0) * 1000
    results["hand_out"] = str(s)
    from language.fast_path import run_fast
    t0 = time.perf_counter()
    fr = run_fast(ll)
    results["fast_path_ms"] = (time.perf_counter() - t0) * 1000
    results["fast_out"] = fr.output[-1] if fr.output else None
    try:
        g = run_codegen_build(ll)
        results["go_codegen_build_ms"] = g.get("build_ms")
        results["go_codegen_run_ms"] = g.get("run_ms")
        results["go_codegen_inner_ms"] = g.get("ms")
        results["go_ok"] = g.get("ok")
        results["go_out"] = (g.get("output") or [None])[-1] if g.get("output") else None
    except Exception as e:
        results["go_error"] = str(e)
    hp = results["hand_python_ms"] or 1
    if results.get("go_codegen_run_ms"):
        results["go_vs_hand"] = round(results["go_codegen_run_ms"] / hp, 3)
        results["beats_python"] = results["go_codegen_run_ms"] < hp
    results["claim"] = (
        "Go direct codegen run time vs hand Python: "
        + ("FASTER" if results.get("beats_python") else "not yet faster on this host/n")
    )
    return results
