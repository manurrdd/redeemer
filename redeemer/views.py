from __future__ import annotations

from html import escape

CSS = """
:root {
  color-scheme: light dark;
  --bg: #f6f7f9; --panel: #fff; --line: #e3e5ea; --ink: #14161a; --muted: #6b7280;
  --accent: #3b5bdb; --accent-ink: #fff; --ok: #16794a; --bad: #c0392b; --bar: #c7d2fe;
  --radius: 12px;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #101216; --panel: #171a20; --line: #262a33; --ink: #e9ecf1; --muted: #939aa6;
          --accent: #5c7cfa; --bar: #313a5c; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
       font: 15px/1.5 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
header { display: flex; align-items: center; gap: 20px; padding: 0 24px; height: 56px;
         background: var(--panel); border-bottom: 1px solid var(--line); }
header .brand { font-weight: 650; letter-spacing: -.01em; }
header nav { display: flex; gap: 16px; }
header nav a { color: var(--muted); }
header form { margin-left: auto; }
main { max-width: 1040px; margin: 0 auto; padding: 28px 24px 64px; }
h1 { font-size: 22px; margin: 0; letter-spacing: -.02em; }
h2 { font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted);
     margin: 32px 0 10px; font-weight: 600; }
.page-head { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }
.page-head form { margin-left: auto; }
.sub { color: var(--muted); margin: 0 0 4px; font-size: 13px; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius);
        padding: 16px 18px; }
.card + .card { margin-top: 12px; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; }
.stat { background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius);
        padding: 14px 16px; }
.stat b { display: block; font-size: 24px; font-weight: 650; letter-spacing: -.02em;
          font-variant-numeric: tabular-nums; }
.stat span { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .06em; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 760px) { .grid2 { grid-template-columns: 1fr; } }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; font-size: 12px; font-weight: 600; color: var(--muted);
     text-transform: uppercase; letter-spacing: .05em; padding: 0 10px 8px; }
td { padding: 9px 10px; border-top: 1px solid var(--line); vertical-align: middle; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
td.right, th.right { text-align: right; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.muted { color: var(--muted); }
.empty { color: var(--muted); padding: 14px 10px; }
.pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px;
        border: 1px solid var(--line); }
.pill.on { color: var(--ok); border-color: color-mix(in srgb, var(--ok) 35%, transparent); }
.pill.off { color: var(--bad); border-color: color-mix(in srgb, var(--bad) 35%, transparent); }
form.row { display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-end; }
label { display: flex; flex-direction: column; gap: 5px; font-size: 12px; color: var(--muted); }
label.check { flex-direction: row; align-items: center; gap: 7px; padding-bottom: 10px; }
input, select { padding: 8px 10px; border: 1px solid var(--line); border-radius: 8px;
                background: var(--bg); color: var(--ink); font: inherit; }
input:focus, select:focus { outline: 2px solid var(--accent); outline-offset: -1px; }
button { padding: 9px 16px; border: 1px solid transparent; border-radius: 8px;
         background: var(--accent); color: var(--accent-ink); font: inherit; font-weight: 550;
         cursor: pointer; }
button.ghost { background: transparent; color: var(--ink); border-color: var(--line); }
button.link { background: none; border: 0; color: var(--muted); padding: 2px 4px; cursor: pointer; }
button.danger { background: transparent; color: var(--bad); border-color: var(--line); }
.bars { display: grid; gap: 8px; }
.bars .b { display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 10px;
           position: relative; padding: 4px 8px; border-radius: 6px; overflow: hidden; }
.bars .fill { position: absolute; inset: 0 auto 0 0; background: var(--bar); border-radius: 6px; }
.bars .b > span { position: relative; }
.bars .n { font-variant-numeric: tabular-nums; color: var(--muted); }
.error { color: var(--bad); font-size: 14px; margin: 0 0 12px; }
.login { max-width: 340px; margin: 15vh auto; }
.login h1 { text-align: center; margin-bottom: 18px; }
.login button { width: 100%; }
.actions { display: flex; gap: 8px; justify-content: flex-end; }
"""


def layout(title: str, body: str, *, nav: bool = True) -> str:
    head = (
        '<header><span class="brand">Redeemer</span><nav>'
        '<a href="/">Overview</a><a href="/global">Global codes</a></nav>'
        '<form method="post" action="/logout"><button class="link">Sign out</button></form>'
        "</header>"
        if nav
        else ""
    )
    return (
        "<!doctype html><html lang=en><meta charset=utf-8>"
        '<meta name=viewport content="width=device-width,initial-scale=1">'
        f"<title>{escape(title)} · Redeemer</title><link rel=stylesheet href=/style.css>"
        f"{head}<main>{body}</main>"
        "<script>document.addEventListener('submit',e=>{"
        "const m=e.target.dataset.confirm;if(m&&!confirm(m))e.preventDefault()});</script></html>"
    )


def login_page(error: str = "") -> str:
    return layout(
        "Sign in",
        f"""<div class="login"><h1>Redeemer</h1><div class="card">
        {_error(error)}
        <form method="post" action="/login">
          <label>Password<input type="password" name="password" autofocus></label>
          <p><button>Sign in</button></p>
        </form></div></div>""",
        nav=False,
    )


def _error(message: str) -> str:
    return f'<p class="error">{escape(message)}</p>' if message else ""


def _stats(items: list[tuple[str, object]]) -> str:
    cells = "".join(f"<div class=stat><b>{value}</b><span>{escape(label)}</span></div>"
                    for label, value in items)
    return f'<div class="stats">{cells}</div>'


def _flag(country: str) -> str:
    if len(country) != 2 or not country.isalpha():
        return ""
    return "".join(chr(0x1F1E6 + ord(c) - 65) for c in country.upper()) + " "


def bars(rows, title: str, *, flags: bool = False) -> str:
    if not rows:
        return f'<h2>{escape(title)}</h2><div class="card"><p class="empty">No data yet</p></div>'
    top = max(row["count"] for row in rows) or 1
    items = "".join(
        f'<div class="b"><div class="fill" style="width:{row["count"] * 100 // top}%"></div>'
        f'<span>{_flag(row["value"]) if flags else ""}{escape(row["value"])}</span>'
        f'<span class="n">{row["count"]}</span></div>'
        for row in rows
    )
    return f'<h2>{escape(title)}</h2><div class="card"><div class="bars">{items}</div></div>'


def _device(device_id) -> str:
    if not device_id:
        return '<td class="muted">anonymous</td>'
    return f'<td class="mono muted">{escape(device_id[:8])}…</td>'


def _uses(row) -> str:
    return f'{row["uses"]} / {"∞" if row["max_uses"] is None else row["max_uses"]}'


def _state(row) -> str:
    if not row["enabled"]:
        return '<span class="pill off">off</span>'
    return '<span class="pill on">on</span>'


def code_table(codes) -> str:
    head = ("<tr><th>Code</th><th>Note</th><th class=num>Uses</th><th>Expires</th>"
            "<th>State</th><th class=right>Actions</th></tr>")
    if not codes:
        return f'<table>{head}</table><p class="empty">No codes yet</p>'
    rows = []
    for c in codes:
        code = escape(c["code"])
        rows.append(
            "<tr>"
            f'<td class="mono"><a href="/c/{code}">{code}</a></td>'
            f'<td>{escape(c["note"]) or "<span class=muted>—</span>"}</td>'
            f'<td class="num">{_uses(c)}</td>'
            f'<td class="muted">{escape((c["expires_at"] or "—")[:10])}</td>'
            f"<td>{_state(c)}</td>"
            '<td><div class="actions">'
            f'<form method="post" action="/c/{code}/toggle">'
            f'<button class="link">{"disable" if c["enabled"] else "enable"}</button></form>'
            f'<form method="post" action="/c/{code}/delete" data-confirm="Delete {code}?">'
            '<button class="link">delete</button></form>'
            "</div></td></tr>"
        )
    return f"<table>{head}{''.join(rows)}</table>"


def redemption_table(redemptions, *, with_app: bool = False, with_code: bool = True) -> str:
    columns = (["When"] + (["App"] if with_app else []) + (["Code"] if with_code else [])
               + ["Platform", "Version", "Country", "Device"])
    head = "<tr>" + "".join(f"<th>{c}</th>" for c in columns) + "</tr>"
    if not redemptions:
        return f'<table>{head}</table><p class="empty">No redemptions yet</p>'
    rows = []
    for r in redemptions:
        country = r["country"] or ""
        rows.append(
            "<tr>"
            f'<td class="mono muted">{escape(r["redeemed_at"][:16].replace("T", " "))}</td>'
            + (f'<td class="mono">{escape(r["app_slug"])}</td>' if with_app else "")
            + (f'<td class="mono"><a href="/c/{escape(r["code"])}">{escape(r["code"])}</a></td>'
               if with_code else "")
            + f'<td>{escape(r["platform"] or "—")}</td>'
            f'<td class="mono muted">{escape(r["app_version"] or "—")}</td>'
            f'<td>{_flag(country)}{escape(country or "—")}</td>'
            + _device(r["device_id"])
            + "</tr>"
        )
    return f"<table>{head}{''.join(rows)}</table>"


def code_form(action: str) -> str:
    return f"""
    <form class="row" method="post" action="{action}">
      <label>Code<input name="code" placeholder="auto-generated" class="mono"></label>
      <label>How many<input name="quantity" type="number" min="1" max="500" value="1" style="width:6.5em"></label>
      <label>Note<input name="note" placeholder="press, giveaway…"></label>
      <label>Max uses<input name="max_uses" type="number" min="1" placeholder="∞" style="width:6.5em"></label>
      <label>Expires<input name="expires_at" type="date"></label>
      <button>Create</button>
    </form>"""


def dashboard(totals, apps, platforms, countries, redemptions, error: str = "") -> str:
    rows = "".join(
        "<tr>"
        f'<td><a href="/a/{escape(a["slug"])}">{escape(a["name"])}</a></td>'
        f'<td class="mono muted">{escape(a["slug"])}</td>'
        f'<td class="num">{a["code_count"]}</td>'
        f'<td class="num">{a["redemption_count"]}</td>'
        "</tr>"
        for a in apps
    )
    table = (
        "<table><tr><th>App</th><th>Slug</th><th class=num>Codes</th>"
        f"<th class=num>Redemptions</th></tr>{rows}</table>"
        if apps
        else '<p class="empty">No apps yet. Add one to start issuing codes.</p>'
    )
    return layout(
        "Overview",
        f"""<div class="page-head"><h1>Overview</h1></div>
        {_stats([("apps", totals["apps"]), ("codes", totals["codes"]),
                 ("active", totals["active_codes"]), ("redemptions", totals["redemptions"]),
                 ("devices", totals["devices"])])}
        <h2>Apps</h2>
        <div class="card">{table}</div>
        <div class="card">{_error(error)}
          <form class="row" method="post" action="/apps">
            <label>Slug<input name="slug" placeholder="my-app" class="mono" required></label>
            <label>Name<input name="name" placeholder="My App" required></label>
            <button>Add app</button>
          </form>
        </div>
        <div class="grid2">
          <div>{bars(platforms, "By platform")}</div>
          <div>{bars(countries, "By country", flags=True)}</div>
        </div>
        <h2>Latest redemptions</h2>
        <div class="card">{redemption_table(redemptions, with_app=True)}</div>""",
    )


def app_page(app, codes, redemptions, platforms, countries, error: str = "") -> str:
    slug = app["slug"] if app else None
    title = app["name"] if app else "Global codes"
    base = f"/a/{slug}" if slug else "/global"
    used = sum(c["uses"] for c in codes)
    header = (
        f"""<div class="page-head"><h1>{escape(title)}</h1>
        <form method="post" action="/a/{escape(slug)}/delete" data-confirm="Delete {escape(title)} and all its codes?">
          <button class="danger">Delete app</button></form></div>
        <p class="sub mono">{escape(slug)}</p>"""
        if slug
        else """<div class="page-head"><h1>Global codes</h1></div>
        <p class="sub">Valid in every registered app. Each app spends one use.</p>"""
    )
    stats = _stats([("codes", len(codes)),
                    ("active", sum(1 for c in codes if c["enabled"])),
                    ("redemptions", used)])
    breakdowns = (
        f'<div class="grid2"><div>{bars(platforms, "By platform")}</div>'
        f'<div>{bars(countries, "By country", flags=True)}</div></div>'
        if slug
        else ""
    )
    return layout(
        title,
        f"""{header}{stats}
        <h2>New codes</h2>
        <div class="card">{_error(error)}{code_form(base + "/codes")}</div>
        <h2>Codes <a class="muted" href="{base}/codes.csv">· export CSV</a></h2>
        <div class="card">{code_table(codes)}</div>
        {breakdowns}
        <h2>Latest redemptions</h2>
        <div class="card">{redemption_table(redemptions, with_app=not slug)}</div>""",
    )


def code_page(code, redemptions) -> str:
    scope = code["app_slug"] or "all apps"
    link = f'<a href="/a/{escape(code["app_slug"])}">{escape(code["app_slug"])}</a>' if code["app_slug"] else "all apps"
    return layout(
        code["code"],
        f"""<div class="page-head"><h1 class="mono">{escape(code["code"])}</h1>
          <form method="post" action="/c/{escape(code["code"])}/delete"
                data-confirm="Delete {escape(code["code"])}?">
            <button class="danger">Delete</button></form></div>
        <p class="sub">Scope: {link} · created {escape(code["created_at"][:10])}</p>
        {_stats([("uses", code["uses"]),
                 ("max uses", "∞" if code["max_uses"] is None else code["max_uses"]),
                 ("state", "on" if code["enabled"] else "off")])}
        <h2>Settings</h2>
        <div class="card">
          <form class="row" method="post" action="/c/{escape(code["code"])}">
            <label>Note<input name="note" value="{escape(code["note"])}"></label>
            <label>Max uses<input name="max_uses" type="number" min="1" placeholder="∞"
                   value="{code["max_uses"] if code["max_uses"] is not None else ""}" style="width:6.5em"></label>
            <label>Expires<input name="expires_at" type="date"
                   value="{escape((code["expires_at"] or "")[:10])}"></label>
            <label class="check"><input name="enabled" type="checkbox" value="1"
                   {"checked" if code["enabled"] else ""}> Enabled</label>
            <button>Save</button>
          </form>
        </div>
        <h2>Redemptions</h2>
        <div class="card">{redemption_table(redemptions, with_app=True, with_code=False)}</div>""",
    )


def not_found() -> str:
    return layout("Not found", '<div class="card"><p class="empty">Not found.</p></div>')
