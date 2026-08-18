"""Task recipes — fix_test, scaffold_shop, add_api_route, etc."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import os, re, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def recipe_fix_test(ctx):
    from library.tool_executor import ToolExecutor
    ex = ToolExecutor(timeout_s=90)
    tr = ex.execute_one({"id": "t", "function": {"name": "run_pytest", "arguments": json.dumps({"path": os.path.join(ROOT, "tests")})}})
    return {"ok": tr.ok, "step": "fix_test", "result": tr.result, "error": tr.error}

def recipe_scaffold_shop(ctx):
    from tools.fullstack import scaffold_fullstack
    r = scaffold_fullstack(name=ctx.get("name") or "shop", title=ctx.get("title") or "Shop")
    return {"ok": r.get("ok"), "step": "scaffold_shop", "result": r}

def recipe_add_api_route(ctx):
    name = ctx.get("name") or ctx.get("site") or "shop"
    route = ctx.get("route") or "/api/hello"
    site = os.path.join(ROOT, "examples", "websites", name, "backend", "server.py")
    if not os.path.isfile(site):
        from tools.fullstack import scaffold_fullstack
        scaffold_fullstack(name=name, title=name)
    if not os.path.isfile(site):
        return {"ok": False, "step": "add_api_route", "error": "no backend"}
    src = open(site, encoding="utf-8").read()
    if f'path == "{route}"' in src:
        return {"ok": True, "step": "add_api_route", "result": {"already": True, "route": route, "path": site}}
    snippet = f'''\n        if path == "{route}":\n            return self._json(200, {{"ok": True, "route": "{route}"}})\n'''
    if "return self._json(404" in src:
        src = src.replace('return self._json(404, {"error": "not found"})', snippet + '        return self._json(404, {"error": "not found"})', 1)
    open(site, "w", encoding="utf-8").write(src)
    return {"ok": True, "step": "add_api_route", "result": {"path": site, "route": route, "patched": True}}

def recipe_project_stats(ctx):
    path = ctx.get("path") or os.path.join(ROOT, "language")
    try:
        from library.go_tools import run_tools_go, start_daemon
        from library.task_memory import prefs
        if prefs().get("use_go_tools", True):
            start_daemon()
            r = run_tools_go([{"name": "project_stats", "args": {"path": path}}], parallel=False)
            if r.get("ok") and r.get("results"):
                return {"ok": True, "step": "project_stats", "result": r["results"][0].get("result")}
    except Exception:
        pass
    from library.tool_executor import ToolExecutor
    tr = ToolExecutor(timeout_s=30).execute_one({"id": "s", "function": {"name": "project_stats", "arguments": json.dumps({"path": path})}})
    return {"ok": tr.ok, "step": "project_stats", "result": tr.result, "error": tr.error}

def recipe_search(ctx):
    q = ctx.get("query") or "def"
    path = ctx.get("path") or os.path.join(ROOT, "language")
    from library.tool_executor import ToolExecutor
    tr = ToolExecutor(timeout_s=30).execute_one({"id": "s", "function": {"name": "search_code", "arguments": json.dumps({"query": q, "path": path})}})
    return {"ok": tr.ok, "step": "search", "result": tr.result, "error": tr.error}

def recipe_deploy(ctx):
    from tools.deploy import deploy_site
    return {"ok": True, "step": "deploy", "result": deploy_site(ctx.get("name") or "shop")}

RECIPES = {
    "fix_test": {"name": "fix_test", "description": "Run tests", "run": recipe_fix_test},
    "scaffold_shop": {"name": "scaffold_shop", "description": "Full-stack shop app", "run": recipe_scaffold_shop},
    "add_api_route": {"name": "add_api_route", "description": "Add GET API route", "run": recipe_add_api_route},
    "project_stats": {"name": "project_stats", "description": "Project stats", "run": recipe_project_stats},
    "search": {"name": "search", "description": "Search code", "run": recipe_search},
    "deploy": {"name": "deploy", "description": "Zip site", "run": recipe_deploy},
}

def list_recipes():
    return [{"name": k, "description": v["description"]} for k, v in RECIPES.items()]

def run_recipe(recipe_id: str, **ctx):
    if recipe_id not in RECIPES:
        return {"ok": False, "error": f"unknown recipe {recipe_id}", "available": list(RECIPES)}
    return RECIPES[recipe_id]["run"](ctx)

def match_recipe(intent: str):
    t = intent.lower().strip()
    rules = [
        (("fix test", "run tests", "pytest"), "fix_test"),
        (("scaffold shop", "create shop", "shop app"), "scaffold_shop"),
        (("add api", "api route", "add route"), "add_api_route"),
        (("deploy", "zip site"), "deploy"),
        (("project stats", "how big", "repo size"), "project_stats"),
        (("search for", "find symbol", "where is"), "search"),
    ]
    for keys, rid in rules:
        if any(k in t for k in keys):
            return rid
    return None
