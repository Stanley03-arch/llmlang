"""Full-stack website scaffold: SPA frontend + REST API + SQLite."""
from __future__ import annotations
from typing import Any, Dict
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# prefer project-local
PROJECT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITES = os.path.join(PROJECT, "examples", "websites")

def _safe_site(name: str) -> str:
    name = name.strip().replace("..", "").replace("/", "_")
    path = os.path.abspath(os.path.join(SITES, name))
    if not path.startswith(os.path.abspath(SITES)):
        raise PermissionError("invalid site name")
    return path

BACKEND_PY = '''#!/usr/bin/env python3
import json, os, sqlite3, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
PORT = int(os.environ.get("PORT", "8787"))
DB = os.path.join(os.path.dirname(__file__), "..", "data", "app.db")
def db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, body TEXT DEFAULT '', done INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    return conn
class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code); self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def _read(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n).decode() or "{}") if n else {}
    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", "/api/health"):
            return self._json(200, {"ok": True, "service": "llmlang-api"})
        if path == "/api/items":
            conn = db(); rows = conn.execute("SELECT * FROM items ORDER BY id DESC").fetchall(); conn.close()
            return self._json(200, {"items": [dict(r) for r in rows]})
        if path.startswith("/api/items/"):
            item_id = path.rsplit("/", 1)[-1]
            conn = db(); row = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone(); conn.close()
            return self._json(404 if not row else 200, {"error": "not found"} if not row else dict(row))
        return self._json(404, {"error": "not found"})
    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/api/items":
            data = self._read(); title = (data.get("title") or "").strip()
            if not title: return self._json(400, {"error": "title required"})
            conn = db(); cur = conn.execute("INSERT INTO items (title, body) VALUES (?, ?)", (title, data.get("body") or ""))
            conn.commit(); item_id = cur.lastrowid
            row = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone(); conn.close()
            return self._json(201, dict(row))
        return self._json(404, {"error": "not found"})
    def do_PUT(self):
        path = urllib.parse.urlparse(self.path).path
        if path.startswith("/api/items/"):
            item_id = path.rsplit("/", 1)[-1]; data = self._read(); conn = db()
            row = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
            if not row: conn.close(); return self._json(404, {"error": "not found"})
            conn.execute("UPDATE items SET title=?, body=?, done=? WHERE id=?", (data.get("title", row["title"]), data.get("body", row["body"]), int(bool(data.get("done", row["done"]))), item_id))
            conn.commit(); row = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone(); conn.close()
            return self._json(200, dict(row))
        return self._json(404, {"error": "not found"})
    def do_DELETE(self):
        path = urllib.parse.urlparse(self.path).path
        if path.startswith("/api/items/"):
            item_id = path.rsplit("/", 1)[-1]; conn = db()
            conn.execute("DELETE FROM items WHERE id=?", (item_id,)); conn.commit(); conn.close()
            return self._json(200, {"ok": True, "deleted": item_id})
        return self._json(404, {"error": "not found"})
    def log_message(self, fmt, *args):
        print("[api]", fmt % args)
if __name__ == "__main__":
    print(f"LlmLang API on http://127.0.0.1:{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
'''

FRONTEND_HTML = '''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title><link rel="stylesheet" href="styles.css"/></head>
<body><header><strong>{title}</strong><nav>
<a href="#" data-view="home">Home</a><a href="#" data-view="items">Items</a></nav></header>
<main><section class="hero"><h1>{title}</h1><p>{tagline}</p>
<button id="btn-load" class="btn">Load items from API</button></section>
<section id="items-panel" class="panel hidden"><h2>Items</h2>
<form id="add-form"><input name="title" placeholder="Title" required/>
<input name="body" placeholder="Notes"/><button type="submit">Add</button></form>
<ul id="list"></ul></section></main>
<script>window.API_BASE="{api_base}";</script><script src="app.js"></script></body></html>
'''

FRONTEND_CSS = '''body{margin:0;font-family:system-ui;background:#0f1419;color:#e7ecf3}
header{display:flex;justify-content:space-between;padding:1rem 1.5rem;border-bottom:1px solid #2a3548}
a{color:#8b9bb4;margin-left:1rem;text-decoration:none}.hero{max-width:640px;margin:3rem auto;text-align:center}
.btn,button{background:#5b9fd4;color:#fff;border:0;border-radius:8px;padding:.6rem 1rem;cursor:pointer}
.panel{max-width:640px;margin:2rem auto;padding:0 1rem}.hidden{display:none}
#list{list-style:none;padding:0}#list li{background:#1a2332;border:1px solid #2a3548;border-radius:10px;padding:.75rem;margin:.5rem 0;display:flex;justify-content:space-between}
#add-form{display:flex;gap:.5rem;flex-wrap:wrap}#add-form input{flex:1;padding:.5rem;border-radius:8px;border:1px solid #2a3548;background:#1a2332;color:#e7ecf3}
'''

FRONTEND_JS = '''const API=window.API_BASE||"http://127.0.0.1:8787";
async function api(path,opts={}){const r=await fetch(API+path,{headers:{"Content-Type":"application/json"},...opts});if(!r.ok)throw new Error(await r.text());return r.json();}
function showItems(){document.querySelector(".hero")?.classList.add("hidden");document.getElementById("items-panel")?.classList.remove("hidden");}
async function loadItems(){showItems();const data=await api("/api/items");const ul=document.getElementById("list");ul.innerHTML="";
for(const it of data.items||[]){const li=document.createElement("li");li.innerHTML=`<span><strong>${it.title}</strong><div>${it.body||""}</div></span><button data-id="${it.id}" class="del">Delete</button>`;ul.appendChild(li);}
ul.querySelectorAll(".del").forEach(btn=>{btn.onclick=async()=>{await api("/api/items/"+btn.dataset.id,{method:"DELETE"});loadItems();};});}
document.getElementById("btn-load")?.addEventListener("click",()=>loadItems().catch(e=>alert(e.message)));
document.getElementById("add-form")?.addEventListener("submit",async e=>{e.preventDefault();const fd=new FormData(e.target);await api("/api/items",{method:"POST",body:JSON.stringify({title:fd.get("title"),body:fd.get("body")})});e.target.reset();loadItems();});
document.querySelectorAll("[data-view]").forEach(a=>a.addEventListener("click",e=>{e.preventDefault();if(a.dataset.view==="items")loadItems();}));
'''

def scaffold_fullstack(name="fullstack_app", title="LlmLang App", tagline="Full-stack by LlmLang", api_port=8787, **kwargs):
    site = _safe_site(name)
    for d in ("frontend", "backend", "data"):
        os.makedirs(os.path.join(site, d), exist_ok=True)
    api_base = f"http://127.0.0.1:{int(api_port)}"
    files = []
    def write(rel, content):
        path = os.path.join(site, rel)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        files.append(os.path.relpath(path, PROJECT))
    write("frontend/index.html", FRONTEND_HTML.format(title=title, tagline=tagline, api_base=api_base))
    write("frontend/styles.css", FRONTEND_CSS)
    write("frontend/app.js", FRONTEND_JS)
    write("backend/server.py", BACKEND_PY)
    write("README.md", f"# {title}\n\nAPI: `cd backend && python3 server.py`\nUI: `cd frontend && python3 -m http.server 8080`\n")
    return {"ok": True, "name": name, "title": title, "dir": os.path.relpath(site, PROJECT), "files": files,
            "stack": {"frontend": "SPA", "backend": "JSON API", "database": "SQLite", "api": api_base},
            "message": f"Full-stack site '{name}' ready"}

def run_fullstack_api(name="fullstack_app", port=8787):
    import threading, subprocess
    server = os.path.join(_safe_site(name), "backend", "server.py")
    if not os.path.isfile(server):
        return {"ok": False, "error": "scaffold first"}
    env = os.environ.copy(); env["PORT"] = str(port)
    threading.Thread(target=lambda: subprocess.Popen(["python3", server], cwd=os.path.dirname(server), env=env),
                     daemon=True).start()
    return {"ok": True, "port": port, "url": f"http://127.0.0.1:{port}/api/health"}

FULLSTACK_TOOLS = {
    "scaffold_fullstack": {"name": "scaffold_fullstack", "description": "SPA+API+SQLite full-stack site", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "title": {"type": "string"}, "tagline": {"type": "string"}, "api_port": {"type": "integer"}}, "required": ["name"]}, "function": scaffold_fullstack},
    "run_fullstack_api": {"name": "run_fullstack_api", "description": "Start full-stack API", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "port": {"type": "integer"}}, "required": ["name"]}, "function": run_fullstack_api},
}
