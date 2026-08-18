# LlmLang task features

## One command

```bash
python __main__.py --do "project stats"
python __main__.py --do "scaffold shop"
python __main__.py --do "add api route /api/hello to shop"
python __main__.py --do "write readme"
python __main__.py --do "add function stub helper_parse"
python __main__.py --do "list sites"
python __main__.py --do "search for CodeObject"
python __main__.py --do "fix test"
```

## Recipes

```bash
python __main__.py --recipes --list
```

- fix_test, scaffold_shop, add_api_route, project_stats, search, deploy
- write_readme, add_function_stub, list_sites

## Memory & batch

```bash
python __main__.py --history
python __main__.py --retry
python __main__.py --batch "project stats && list sites"
```

## Other

```bash
python __main__.py --code "Find CodeObject"
python __main__.py --fullstack myapp "My App"
python __main__.py --deploy myapp
python __main__.py --beat --n 100000
python __main__.py --go-tools
```
