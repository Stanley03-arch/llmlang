"""GitHub workflow tools — gh CLI or GITHUB_TOKEN REST API."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import json
import os
import shutil
import subprocess
import urllib.request
import urllib.error

def _gh_available() -> bool:
    return shutil.which("gh") is not None

def _token() -> Optional[str]:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

def _api(path: str, method: str = "GET", body: Any = None) -> Dict[str, Any]:
    token = _token()
    if not token:
        return {"ok": False, "error": "No GITHUB_TOKEN/GH_TOKEN and gh CLI unavailable"}
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        f"https://api.github.com{path}", data=data, method=method,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                 "User-Agent": "LlmLang/1.6", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return {"ok": True, "status": resp.status, "data": json.loads(raw) if raw else {}}
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": e.read().decode()[:500], "status": e.code}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _run_gh(args: List[str]) -> Dict[str, Any]:
    try:
        proc = subprocess.run(["gh"] + args, capture_output=True, text=True, timeout=60)
        out, err = (proc.stdout or "").strip(), (proc.stderr or "").strip()
        if proc.returncode != 0:
            return {"ok": False, "error": err or out, "exit": proc.returncode}
        try:
            return {"ok": True, "data": json.loads(out)}
        except json.JSONDecodeError:
            return {"ok": True, "text": out}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def github_status() -> Dict[str, Any]:
    if _gh_available():
        return {"ok": True, "via": "gh", "detail": _run_gh(["auth", "status"])}
    if _token():
        me = _api("/user")
        return {"ok": me.get("ok", False), "via": "token", "detail": me}
    return {"ok": False, "error": "GitHub not configured. Install gh or set GITHUB_TOKEN."}

def github_search_code(query: str, limit: int = 5) -> Dict[str, Any]:
    if _gh_available():
        return _run_gh(["search", "code", query, "--limit", str(limit), "--json", "repository,path,url"])
    return _api(f"/search/code?q={urllib.request.quote(query)}")

def github_search_repos(query: str, limit: int = 5) -> Dict[str, Any]:
    if _gh_available():
        return _run_gh(["search", "repos", query, "--limit", str(limit), "--json", "fullName,description,url,stargazersCount"])
    return _api(f"/search/repositories?q={urllib.request.quote(query)}&per_page={limit}")

def github_repo_tree(owner: str, repo: str, recursive: bool = True) -> Dict[str, Any]:
    q = "?recursive=1" if recursive else ""
    if _gh_available():
        return _run_gh(["api", f"/repos/{owner}/{repo}/git/trees/HEAD{q}"])
    return _api(f"/repos/{owner}/{repo}/git/trees/HEAD{q}")

def github_get_file(owner: str, repo: str, path: str, ref: str = None) -> Dict[str, Any]:
    suffix = f"?ref={ref}" if ref else ""
    if _gh_available():
        return _run_gh(["api", f"/repos/{owner}/{repo}/contents/{path}{suffix}"])
    return _api(f"/repos/{owner}/{repo}/contents/{path}{suffix}")

GITHUB_TOOLS: Dict[str, Dict[str, Any]] = {
    "github_status": {"name": "github_status", "description": "Check GitHub auth.", "parameters": {"type": "object", "properties": {}, "required": []}, "function": github_status},
    "github_search_code": {"name": "github_search_code", "description": "Search code on GitHub.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}, "function": github_search_code},
    "github_search_repos": {"name": "github_search_repos", "description": "Search GitHub repositories.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}, "function": github_search_repos},
    "github_repo_tree": {"name": "github_repo_tree", "description": "Get repository file tree.", "parameters": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "recursive": {"type": "boolean"}}, "required": ["owner", "repo"]}, "function": github_repo_tree},
    "github_get_file": {"name": "github_get_file", "description": "Get file contents from GitHub.", "parameters": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "path": {"type": "string"}, "ref": {"type": "string"}}, "required": ["owner", "repo", "path"]}, "function": github_get_file},
}
