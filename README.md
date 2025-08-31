Personal Server (Standard Library HTTP API)

Features
- Run shell commands via `/run`
- Log notes to `notes/` + `notes.csv` via `/notes`
- Log transactions to `transactions/transactions.csv` via `/transactions`
- Ping health check via `/ping`
- Scrape a URL and store HTML + text in `scrapes/` + `scrapes.csv` via `/scrape`
- Log weight entries to `weights/weights.csv` via `/weights`

Quick Start
- Run: `python3 main.py` (env: `PERSONAL_SERVER_HOST`, `PERSONAL_SERVER_PORT` optional)
- Default address: `http://127.0.0.1:8080`

API Examples (curl)
- Ping:
  - `curl http://127.0.0.1:8080/ping`

- Run command:
  - `curl -X POST http://127.0.0.1:8080/run -H 'Content-Type: application/json' -d '{"cmd":"ls -la"}'`

- Add note:
  - `curl -X POST http://127.0.0.1:8080/notes -H 'Content-Type: application/json' -d '{"title":"Idea","content":"My note body","tags":["personal","ideas"]}'`

- Log transaction (flexible keys):
  - `curl -X POST http://127.0.0.1:8080/transactions -H 'Content-Type: application/json' -d '{"date":"2025-08-31","amount":12.95,"merchant":"Coffee","category":"Food","notes":"Latte"}'`

- Scrape URL:
  - `curl -X POST http://127.0.0.1:8080/scrape -H 'Content-Type: application/json' -d '{"url":"https://example.com"}'`

- Weight:
  - `curl -X POST http://127.0.0.1:8080/weights -H 'Content-Type: application/json' -d '{"date":"2025-08-31","weight":180,"unit":"lb","body_fat":18.2,"notes":"morning"}'`

Storage Layout
- `notes/notes.csv` with columns: id,title,filename,created_at,tags; individual notes saved as Markdown with frontmatter
- `transactions/transactions.csv` with columns: id,date,amount,merchant,category,account,notes,raw_json
- `scrapes/scrapes.csv` with columns: id,url,fetched_at,filename_html,filename_txt,title
- `weights/weights.csv` with columns: id,date,weight_kg,weight_lb,body_fat_pct,source,notes,raw_json

Design Notes
- Uses Python standard library only (no external deps)
- Threaded HTTP server; JSON I/O; minimal routing
- CSV helpers auto-create headers and directories
# PersonalServer
# PersonalServer
# PersonalServer
# PersonalServer
