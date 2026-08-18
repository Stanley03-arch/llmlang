"""Go lltools client — local tools outside Python."""
from __future__ import annotations
from typing import Any, Dict, List
import json, os, subprocess, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GO_SRC = os.path.join(ROOT, "runtime", "lltools", "main.go")
DAEMON = os.environ.get("LLTOOLS_URL", "http://127.0.0.1:9876")
_BIN = None

def ensure_binary() -> str:
    global _BIN
    if _BIN and os.path.isfile(_BIN):
        return _BIN
    for c in ("/tmp/lltools", os.path.join(ROOT, "runtime", "lltools", "lltools")):
        try:
            subprocess.check_call(["go", "build", "-o", c, GO_SRC], cwd=os.path.dirname(GO_SRC),
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.chmod(c, 0o755)
            _BIN = c
            return c
        except Exception:
            continue
    raise RuntimeError("build lltools failed")

def daemon_up() -> bool:
    try:
        urllib.request.urlopen(DAEMON + "/health", timeout=0.3)
        return True
    except Exception:
        return False

def start_daemon() -> bool:
    if daemon_up():
        return True
    bin_path = ensure_binary()
    subprocess.Popen([bin_path, "-daemon", "127.0.0.1:9876"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(20):
        time.sleep(0.1)
        if daemon_up():
            return True
    return False

def run_tools_go(tools: List[Dict[str, Any]], parallel: bool = True, use_daemon: bool = True) -> Dict[str, Any]:
    payload = json.dumps({"tools": tools, "parallel": parallel}).encode()
    t0 = time.perf_counter()
    if use_daemon:
        start_daemon()
        if daemon_up():
            req = urllib.request.Request(DAEMON + "/tools", data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode())
            data["wall_ms"] = (time.perf_counter() - t0) * 1000
            data["transport"] = "daemon"
            return data
    bin_path = ensure_binary()
    proc = subprocess.run([bin_path], input=payload.decode(), capture_output=True, text=True, timeout=120)
    wall = (time.perf_counter() - t0) * 1000
    if not proc.stdout:
        return {"ok": False, "error": proc.stderr, "wall_ms": wall}
    data = json.loads(proc.stdout)
    data["wall_ms"] = wall
    data["transport"] = "subprocess"
    return data
