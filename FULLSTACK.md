# Full-stack websites in LlmLang

```bash
python __main__.py --fullstack shop_demo "Shop Demo"
```

Creates SPA + REST API + SQLite under `examples/websites/<name>/`.

Run API: `cd backend && python3 server.py`  
Run UI: `cd frontend && python3 -m http.server 8080`

Pure `.ll` compute still routes to Go codegen when pure (can beat CPython).
