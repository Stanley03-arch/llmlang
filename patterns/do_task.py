"""One command: do this task — intent → tools → verify → summary."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import os, re, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@dataclass
class StepResult:
    name: str
    ok: bool
    detail: Any = None
    ms: float = 0.0
    def to_dict(self):
        return {"name": self.name, "ok": self.ok, "detail": self.detail, "ms": round(self.ms, 2)}

@dataclass
class TaskReport:
    ok: bool
    intent: str
    summary: str
    steps: List[StepResult] = field(default_factory=list)
    files_changed: List[str] = field(default_factory=list)
    recipe: Optional[str] = None
    verify: Optional[Dict[str, Any]] = None
    def to_dict(self):
        return {"ok": self.ok, "intent": self.intent, "summary": self.summary, "recipe": self.recipe,
                "files_changed": self.files_changed, "verify": self.verify,
                "steps": [s.to_dict() for s in self.steps]}

def _ensure_defaults():
    try:
        from library.task_memory import prefs, set_pref
        p = prefs()
        if "use_go_tools" not in p: set_pref("use_go_tools", True)
        if "use_cache" not in p: set_pref("use_cache", True)
        if p.get("use_go_tools", True):
            try:
                from library.go_tools import start_daemon
                start_daemon()
            except Exception:
                pass
    except Exception:
        pass

def _extract_query(intent):
    t = intent
    for p in ("search for", "find", "locate", "where is"):
        if p in t.lower():
            t = t[t.lower().index(p)+len(p):].strip(" :")
            break
    m = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", t)
    stop = {"the", "and", "for", "with", "from", "this", "code", "file", "test", "add", "route"}
    cands = [x for x in m if x.lower() not in stop]
    return cands[0] if cands else "def"

def _real_patch_add_comment(path, note):
    if not os.path.isfile(path): return False, "missing"
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".py", ".ll", ".md", ".txt", ".js", ".go"): return False, "skip"
    src = open(path, encoding="utf-8").read()
    if "llmlang-task:" in src: return True, "already annotated"
    line = f"\n# llmlang-task: {note}\n" if ext in (".py", ".ll", ".md", ".txt") else f"\n// llmlang-task: {note}\n"
    if not os.path.abspath(path).startswith(ROOT): return False, "outside"
    open(path, "a", encoding="utf-8").write(line)
    return True, path

def _patch_from_search(intent, matches, max_files=3):
    changed = []
    note = re.sub(r"\s+", " ", intent)[:80]
    for m in matches[:max_files]:
        fp = m.get("file") or m.get("path")
        if not fp: continue
        if not os.path.isabs(fp): fp = os.path.join(ROOT, fp)
        # search results may be "path:line:text" strings
        if isinstance(m, str):
            fp = m.split(":")[0]
            if not os.path.isabs(fp): fp = os.path.join(ROOT, "..", fp) if not os.path.isfile(fp) else fp
        ok, info = _real_patch_add_comment(fp if isinstance(fp, str) else "", note)
        if ok and info != "already annotated":
            changed.append(os.path.relpath(str(info), ROOT) if os.path.isfile(str(info)) else str(info))
    return changed

def do_task(intent: str, apply_patches: bool = True) -> TaskReport:
    _ensure_defaults()
    t0 = time.perf_counter()
    steps, files_changed = [], []
    recipe_id, test_info = None, None
    from patterns.recipes import match_recipe, run_recipe, list_recipes, recipe_project_stats, recipe_search, recipe_fix_test
    from library.task_memory import remember_success, remember_failure, prefs
    rid = match_recipe(intent)
    if rid:
        recipe_id = rid
        t1 = time.perf_counter()
        ctx = {}
        if rid == "search": ctx["query"] = _extract_query(intent)
        if rid == "add_api_route":
            m = re.search(r"(/api/[\w/]+)", intent)
            ctx["route"] = m.group(1) if m else "/api/hello"
            ctx["name"] = "shop"
        if rid in ("scaffold_shop", "deploy"):
            ctx["name"] = "shop"
        try:
            rr = run_recipe(rid, **ctx)
            ok = bool(rr.get("ok"))
            steps.append(StepResult("recipe:" + rid, ok, rr, (time.perf_counter()-t1)*1000))
            res = rr.get("result") or {}
            if isinstance(res, dict):
                if res.get("files"): files_changed.extend(res["files"] if isinstance(res["files"], list) else [])
                for k in ("path", "dir", "zip"):
                    if res.get(k): files_changed.append(str(res[k]))
        except Exception as e:
            steps.append(StepResult("recipe:" + rid, False, str(e), (time.perf_counter()-t1)*1000))
    coding_like = any(k in intent.lower() for k in ("find", "search", "fix", "patch", "code"))
    if coding_like or not rid:
        t1 = time.perf_counter()
        st = recipe_project_stats({"path": os.path.join(ROOT, "language")})
        steps.append(StepResult("stats", bool(st.get("ok")), st.get("result"), (time.perf_counter()-t1)*1000))
        t1 = time.perf_counter()
        se = recipe_search({"query": _extract_query(intent), "path": os.path.join(ROOT, "language")})
        steps.append(StepResult("search", bool(se.get("ok")), se.get("result"), (time.perf_counter()-t1)*1000))
        matches = (se.get("result") or {}).get("matches") or [] if isinstance(se.get("result"), dict) else []
        if apply_patches and any(k in intent.lower() for k in ("fix", "patch", "annotate", "mark")):
            t1 = time.perf_counter()
            changed = _patch_from_search(intent, matches, int(prefs().get("max_patch_files") or 3))
            files_changed.extend(changed)
            steps.append(StepResult("patch", True, {"changed": changed}, (time.perf_counter()-t1)*1000))
    if any(k in intent.lower() for k in ("test", "fix", "verify")):
        t1 = time.perf_counter()
        tr = recipe_fix_test({})
        test_info = tr
        steps.append(StepResult("test", bool(tr.get("ok")), tr.get("result") or tr.get("error"), (time.perf_counter()-t1)*1000))
    ok = all(s.ok for s in steps) if steps else False
    summary = f"do_task: recipe={recipe_id or '—'} steps={len(steps)} files={len(files_changed)} ok={ok} ms={round((time.perf_counter()-t0)*1000,1)}"
    try:
        if ok: remember_success(intent, summary, files_changed)
        else: remember_failure(intent, "do_task", summary)
    except Exception:
        pass
    return TaskReport(ok=ok, intent=intent, summary=summary, steps=steps, files_changed=files_changed, recipe=recipe_id,
                      verify={"files": files_changed, "tests": test_info})
