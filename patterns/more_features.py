"""Extra task features: history, retry, README, stubs, batch do."""
from __future__ import annotations
from typing import Any, Dict, List
import json, os, re
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def task_history(limit: int = 15) -> Dict[str, Any]:
    from library.task_memory import load
    data = load()
    return {"ok": True, "history": (data.get("history") or [])[:limit],
            "failures": (data.get("failures") or [])[:limit],
            "last_paths": (data.get("last_paths") or [])[:10], "prefs": data.get("prefs") or {}}

def retry_last_failure() -> Dict[str, Any]:
    from library.task_memory import load
    from patterns.do_task import do_task
    fails = load().get("failures") or []
    if not fails:
        return {"ok": False, "error": "no failures recorded"}
    task = fails[0].get("task") or ""
    report = do_task(task)
    return {"ok": report.ok, "retried": task, "report": report.to_dict()}

def recipe_write_readme(ctx):
    out = os.path.join(ROOT, "README_GENERATED.md")
    try:
        from patterns.recipes import recipe_project_stats
        stats = recipe_project_stats({"path": os.path.join(ROOT, "language")}).get("result") or {}
    except Exception:
        stats = {}
    body = f"# LlmLang (generated)\n\nGenerated: {datetime.now(timezone.utc).isoformat()}\n\n## Stats\n\n{json.dumps(stats, default=str)[:400]}\n\n## Commands\n\n```bash\npython __main__.py --do \"project stats\"\npython __main__.py --recipes --list\n```\n"
    open(out, "w", encoding="utf-8").write(body)
    return {"ok": True, "step": "write_readme", "result": {"path": out, "bytes": len(body)}}

def recipe_add_function_stub(ctx):
    name = ctx.get("func") or ctx.get("name") or "new_helper"
    name = re.sub(r"[^a-zA-Z0-9_]", "_", str(name))
    name = re.sub(r"^[^a-zA-Z_]+", "", name) or "new_helper"
    target = ctx.get("file") or os.path.join(ROOT, "library", "stubs.py")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    if not os.path.isfile(target):
        open(target, "w").write('"""Auto-generated stubs from LlmLang tasks."""\n\n')
    src = open(target, encoding="utf-8").read()
    if f"def {name}(" in src:
        return {"ok": True, "step": "add_function_stub", "result": {"already": True, "file": target, "func": name}}
    open(target, "a").write(f'\n\ndef {name}(*args, **kwargs):\n    """Stub created by LlmLang."""\n    raise NotImplementedError("{name}")\n')
    return {"ok": True, "step": "add_function_stub", "result": {"file": target, "func": name, "patched": True}}

def recipe_list_sites(ctx):
    sites_dir = os.path.join(ROOT, "examples", "websites")
    os.makedirs(sites_dir, exist_ok=True)
    sites = [d for d in sorted(os.listdir(sites_dir)) if os.path.isdir(os.path.join(sites_dir, d))]
    return {"ok": True, "step": "list_sites", "result": {"sites": sites, "count": len(sites)}}

def batch_do(intents: List[str]) -> Dict[str, Any]:
    from patterns.do_task import do_task
    results = [do_task(i).to_dict() for i in intents]
    return {"ok": all(x.get("ok") for x in results) if results else False, "count": len(results), "results": results}

def register_extra_recipes() -> None:
    from patterns import recipes as R
    R.RECIPES.update({
        "write_readme": {"name": "write_readme", "description": "Generate README_GENERATED.md", "run": recipe_write_readme},
        "add_function_stub": {"name": "add_function_stub", "description": "Add function stub to library/stubs.py", "run": recipe_add_function_stub},
        "list_sites": {"name": "list_sites", "description": "List scaffolded websites", "run": recipe_list_sites},
    })
    _orig = R.match_recipe
    def match_recipe(intent: str):
        t = intent.lower()
        if any(k in t for k in ("write readme", "generate readme", "make readme")): return "write_readme"
        if any(k in t for k in ("add function", "function stub", "add stub")): return "add_function_stub"
        if any(k in t for k in ("list sites", "list websites", "show sites")): return "list_sites"
        return _orig(intent)
    R.match_recipe = match_recipe
