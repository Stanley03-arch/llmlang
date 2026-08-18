"""Deploy tool — zip a site for hosting."""
from __future__ import annotations
from typing import Any, Dict, Optional
import os, zipfile
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITES = os.path.join(ROOT, "examples", "websites")
DEPLOY = os.path.join(ROOT, "examples", "deploy")

def deploy_site(name: str, include_backend: bool = True, out_name: Optional[str] = None) -> Dict[str, Any]:
    site = os.path.join(SITES, name)
    if not os.path.isdir(site):
        return {"ok": False, "error": f"site not found: {name}"}
    os.makedirs(DEPLOY, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_name = out_name or f"{name}_{stamp}.zip"
    out_path = os.path.join(DEPLOY, out_name)
    written = []
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(site):
            dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__", "data")]
            if not include_backend and ("backend" in dirpath.replace("\\", "/")):
                continue
            for fn in filenames:
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, site)
                zf.write(full, arcname=os.path.join(name, rel))
                written.append(rel)
    return {"ok": True, "site": name, "zip": os.path.relpath(out_path, ROOT),
            "bytes": os.path.getsize(out_path), "files": len(written),
            "include_backend": include_backend, "message": f"Deploy pack ready: {out_path}"}

def list_deployments() -> Dict[str, Any]:
    os.makedirs(DEPLOY, exist_ok=True)
    items = [{"name": fn, "bytes": os.path.getsize(os.path.join(DEPLOY, fn)),
              "path": os.path.relpath(os.path.join(DEPLOY, fn), ROOT)}
             for fn in sorted(os.listdir(DEPLOY)) if fn.endswith(".zip")]
    return {"deployments": items, "root": os.path.relpath(DEPLOY, ROOT)}

DEPLOY_TOOLS = {
    "deploy_site": {"name": "deploy_site", "description": "Zip website for deploy", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "include_backend": {"type": "boolean"}}, "required": ["name"]}, "function": deploy_site},
    "list_deployments": {"name": "list_deployments", "description": "List deploy zips", "parameters": {"type": "object", "properties": {}}, "function": list_deployments},
}
