from __future__ import annotations

from html import escape

CSS = """
:root {
  color-scheme: light dark;
  --bg: #f4f5f7; --panel: #fff; --side: #fbfbfc; --line: #e4e6eb; --ink: #14161a;
  --muted: #6b7280; --faint: #9aa1ad; --accent: #3b5bdb; --accent-soft: #eaeeff;
  --ok: #16794a; --bad: #c0392b; --bar: #ccd6fb; --shadow: 0 1px 2px rgba(16,18,24,.05);
  --radius: 12px; --side-w: 236px;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #0e1014; --panel: #171a20; --side: #12141a; --line: #262a33; --ink: #e9ecf1;
          --muted: #98a0ac; --faint: #6c7480; --accent: #7590ff; --accent-soft: #1c2340;
          --ok: #4ade80; --bad: #f87171; --bar: #2b3557; --shadow: none; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
       font: 15px/1.5 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
       -webkit-font-smoothing: antialiased; }
a { color: inherit; text-decoration: none; }
main a:not(.item) { color: var(--accent); }
main a:not(.item):hover { text-decoration: underline; }

/* shell */
.shell { display: grid; grid-template-columns: var(--side-w) 1fr; min-height: 100vh; }
.shell.collapsed { --side-w: 68px; }
aside { position: sticky; top: 0; height: 100vh; display: flex; flex-direction: column;
        gap: 4px; padding: 14px 12px; background: var(--side);
        border-right: 1px solid var(--line); overflow: hidden; }
.side-head { display: flex; align-items: center; gap: 8px; height: 36px; padding: 0 8px 0 10px;
             margin-bottom: 10px; }
.brand { font-weight: 650; letter-spacing: -.02em; font-size: 16px; white-space: nowrap; }
.collapse { margin-left: auto; display: grid; place-items: center; width: 30px; height: 30px;
            border: 0; border-radius: 8px; background: transparent; color: var(--faint);
            cursor: pointer; flex: none; }
.collapse:hover { background: var(--line); color: var(--ink); }
.shell.collapsed .brand { display: none; }
.shell.collapsed .side-head { padding: 0; justify-content: center; }
.shell.collapsed .collapse { margin: 0; }
nav { display: flex; flex-direction: column; gap: 2px; overflow-y: auto; }
.item { flex: none; display: flex; align-items: center; gap: 10px; padding: 8px 10px; border-radius: 9px;
        color: var(--muted); font-size: 14px; white-space: nowrap; border: 0;
        background: transparent; font-family: inherit; width: 100%; cursor: pointer; }
.item svg { flex: none; }
.avatar { flex: none; display: grid; place-items: center; width: 18px; height: 18px;
          border-radius: 5px; background: var(--line); color: var(--muted); font-size: 9.5px;
          font-weight: 700; letter-spacing: .02em; }
.item.on .avatar { background: var(--accent); color: #fff; }
.item:hover { background: var(--line); color: var(--ink); }
.item.on { background: var(--accent-soft); color: var(--accent); font-weight: 550; }
.side-label { flex: none; margin: 16px 10px 6px; font-size: 11px; text-transform: uppercase;
              letter-spacing: .09em; color: var(--faint); font-weight: 600; }
.side-foot { margin-top: auto; padding-top: 8px; }
.shell.collapsed .item { justify-content: center; padding: 9px 0; }
.shell.collapsed .item .label, .shell.collapsed .side-label { display: none; }
.shell.collapsed .side-label { display: block; height: 1px; margin: 12px 12px; padding: 0;
                               background: var(--line); overflow: hidden; }

/* content */
main { padding: 30px 32px 72px; min-width: 0; }
.wrap { max-width: 940px; margin: 0 auto; }
h1 { font-size: 24px; margin: 0; letter-spacing: -.025em; }
h2 { font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: var(--faint);
     margin: 30px 0 10px; font-weight: 600; }
.page-head { display: flex; align-items: flex-start; gap: 14px; margin-bottom: 22px; }
.page-head form { margin-left: auto; }
.sub { color: var(--muted); margin: 5px 0 0; font-size: 13px; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius);
        box-shadow: var(--shadow); }
.card.pad { padding: 18px; }
.card + .card { margin-top: 12px; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; }
.stat { background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius);
        box-shadow: var(--shadow); padding: 15px 17px; }
.stat b { display: block; font-size: 25px; font-weight: 620; letter-spacing: -.03em;
          font-variant-numeric: tabular-nums; line-height: 1.2; }
.stat span { color: var(--faint); font-size: 11px; text-transform: uppercase;
             letter-spacing: .07em; font-weight: 600; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 820px) { .grid2 { grid-template-columns: 1fr; } }

/* tables */
.scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th { text-align: left; font-size: 11px; font-weight: 600; color: var(--faint);
     text-transform: uppercase; letter-spacing: .06em; padding: 13px 14px; white-space: nowrap;
     border-bottom: 1px solid var(--line); }
td { padding: 11px 14px; border-bottom: 1px solid var(--line); white-space: nowrap; }
tbody tr:last-child td { border-bottom: 0; }
tbody tr:hover { background: color-mix(in srgb, var(--line) 40%, transparent); }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px; }
.muted { color: var(--muted); }
.faint { color: var(--faint); }
.empty { color: var(--faint); padding: 26px 14px; text-align: center; font-size: 14px; }
.pill { display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: 12px;
        border: 1px solid var(--line); color: var(--muted); }
.pill.on { color: var(--ok); border-color: color-mix(in srgb, var(--ok) 40%, transparent); }
.pill.off { color: var(--bad); border-color: color-mix(in srgb, var(--bad) 40%, transparent); }
.row-actions { display: flex; gap: 4px; justify-content: flex-end; }

/* forms */
form.fields { display: flex; flex-wrap: wrap; gap: 14px; align-items: flex-end; }
label { display: flex; flex-direction: column; gap: 6px; font-size: 12px; color: var(--muted);
        font-weight: 500; }
label.check { flex-direction: row; align-items: center; gap: 8px; padding-bottom: 11px; }
input, select { padding: 9px 11px; border: 1px solid var(--line); border-radius: 9px;
                background: var(--bg); color: var(--ink); font: inherit; font-size: 14px; }
input::placeholder { color: var(--faint); }
input:focus, select:focus { outline: 2px solid var(--accent); outline-offset: -1px;
                            border-color: transparent; }
button { padding: 10px 18px; border: 1px solid transparent; border-radius: 9px;
         background: var(--accent); color: #fff; font: inherit; font-size: 14px; font-weight: 550;
         cursor: pointer; }
button:hover { filter: brightness(1.08); }
button.ghost { background: transparent; color: var(--ink); border-color: var(--line); }
button.link { background: none; border: 0; color: var(--muted); padding: 3px 6px;
              font-size: 13px; border-radius: 6px; }
button.link:hover { background: var(--line); color: var(--ink); filter: none; }
button.danger { background: transparent; color: var(--bad); border-color: var(--line); }
button.danger:hover { background: var(--bad); color: #fff; border-color: transparent;
                      filter: none; }
.note { margin: 0 0 14px; font-size: 13px; color: var(--bad);
        background: color-mix(in srgb, var(--bad) 10%, transparent); border-radius: 9px;
        padding: 10px 13px; }

/* bars */
.bars { display: grid; gap: 7px; }
.bars .b { display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 10px;
           position: relative; padding: 7px 11px; border-radius: 8px; overflow: hidden;
           font-size: 14px; }
.bars .fill { position: absolute; inset: 0 auto 0 0; background: var(--bar); border-radius: 8px; }
.bars .b > span { position: relative; }
.bars .n { font-variant-numeric: tabular-nums; color: var(--muted); font-size: 13px; }

/* login */
.login { max-width: 350px; margin: 14vh auto; }
.login h1 { text-align: center; margin-bottom: 20px; font-size: 22px; }
.login .card { padding: 22px; }
.login form { display: grid; gap: 16px; }
.login button { width: 100%; }
"""

ICONS = {
    "overview": '<rect x="3" y="3" width="7.5" height="7.5" rx="2"/>'
                '<rect x="13.5" y="3" width="7.5" height="7.5" rx="2"/>'
                '<rect x="3" y="13.5" width="7.5" height="7.5" rx="2"/>'
                '<rect x="13.5" y="13.5" width="7.5" height="7.5" rx="2"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3.2 9h17.6M3.2 15h17.6"/>'
             '<path d="M12 3c2.4 2.4 3.6 5.4 3.6 9S14.4 18.6 12 21c-2.4-2.4-3.6-5.4-3.6-9S9.6 5.4 12 3z"/>',
    "logout": '<path d="M14 3h4.5A2.5 2.5 0 0 1 21 5.5v13a2.5 2.5 0 0 1-2.5 2.5H14"/>'
              '<path d="M9.5 16.5 14 12 9.5 7.5"/><path d="M14 12H3"/>',
    "panel": '<rect x="3" y="4" width="18" height="16" rx="2.5"/><path d="M9.5 4v16"/>',
}


def icon(name: str) -> str:
    return (
        '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>'
    )


def _initials(name: str) -> str:
    letters = [word[0] for word in name.split() if word[0].isalnum()]
    return escape("".join(letters[:2]).upper() or "?")


def sidebar(apps, active: str) -> str:
    def item(href: str, mark: str, label: str, key: str) -> str:
        on = " on" if key == active else ""
        return (f'<a class="item{on}" href="{href}" title="{escape(label)}">'
                f'{mark}<span class="label">{escape(label)}</span></a>')

    entries = "".join(
        item(f'/a/{escape(a["slug"])}', f'<span class="avatar">{_initials(a["name"])}</span>',
             a["name"], f'app:{a["slug"]}')
        for a in apps
    )
    return f"""<aside>
      <div class="side-head"><span class="brand">Redeemer</span>
        <button class="collapse" aria-label="Toggle sidebar">{icon("panel")}</button></div>
      <nav>
        {item("/", icon("overview"), "Overview", "overview")}
        {item("/global", icon("globe"), "Global codes", "global")}
        <p class="side-label">Apps</p>
        {entries or '<span class="side-label faint" style="text-transform:none;letter-spacing:0">None yet</span>'}
      </nav>
      <form class="side-foot" method="post" action="/logout">
        <button class="item" title="Sign out">{icon("logout")}<span class="label">Sign out</span></button>
      </form>
    </aside>"""


SCRIPT = """
<script>
document.addEventListener('submit',e=>{const m=e.target.dataset.confirm;if(m&&!confirm(m))e.preventDefault()});
document.addEventListener('click',e=>{const b=e.target.closest('.collapse');if(!b)return;
  const s=document.querySelector('.shell');s.classList.toggle('collapsed');
  try{localStorage.setItem('sidebar',s.classList.contains('collapsed')?'1':'0')}catch(_){}});
</script>
"""

EARLY = ("<script>try{if(localStorage.getItem('sidebar')==='1')"
         "document.currentScript.parentNode.classList.add('collapsed')}catch(_){}</script>")


def page(title: str, apps, active: str, body: str) -> str:
    return (
        "<!doctype html><html lang=en><meta charset=utf-8>"
        '<meta name=viewport content="width=device-width,initial-scale=1">'
        f"<title>{escape(title)} · Redeemer</title><link rel=stylesheet href=/style.css>"
        f'<div class="shell">{EARLY}{sidebar(apps, active)}'
        f'<main><div class="wrap">{body}</div></main></div>{SCRIPT}</html>'
    )


def login_page(error: str = "") -> str:
    return (
        "<!doctype html><html lang=en><meta charset=utf-8>"
        '<meta name=viewport content="width=device-width,initial-scale=1">'
        "<title>Sign in · Redeemer</title><link rel=stylesheet href=/style.css>"
        f'<div class="login"><h1>Redeemer</h1><div class="card">{_note(error)}'
        '<form method="post" action="/login">'
        '<label>Password<input type="password" name="password" autofocus></label>'
        "<button>Sign in</button></form></div></div></html>"
    )


def not_found(apps=()) -> str:
    return page("Not found", apps, "", '<div class="card"><p class="empty">Not found.</p></div>')


# --- pieces ------------------------------------------------------------------


def _note(message: str) -> str:
    return f'<p class="note">{escape(message)}</p>' if message else ""


def _stats(items) -> str:
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
    return f'<h2>{escape(title)}</h2><div class="card pad"><div class="bars">{items}</div></div>'


def _table(head: str, rows: str, empty: str) -> str:
    if not rows:
        return f'<div class="card"><p class="empty">{escape(empty)}</p></div>'
    return (f'<div class="card scroll"><table><thead>{head}</thead>'
            f"<tbody>{rows}</tbody></table></div>")


PLATFORM_LABELS = {"": "Any", "ios": "iOS", "android": "Android", "ios,android": "iOS + Android"}


def _platform(value) -> str:
    label = PLATFORM_LABELS.get(value or "", value or "Any")
    return f'<span class="faint">{escape(label)}</span>' if not value else escape(label)


def _uses(row) -> str:
    return f'{row["uses"]} / {"∞" if row["max_uses"] is None else row["max_uses"]}'


def _state(row) -> str:
    return ('<span class="pill on">on</span>' if row["enabled"]
            else '<span class="pill off">off</span>')


def _device(device_id) -> str:
    if not device_id:
        return '<td class="faint">anonymous</td>'
    return f'<td class="mono faint">{escape(device_id[:8])}…</td>'


def _select(name: str, options: dict, chosen: str) -> str:
    items = "".join(
        f'<option value="{escape(value)}"{" selected" if value == chosen else ""}>'
        f"{escape(label)}</option>"
        for value, label in options.items()
    )
    return f'<select name="{name}">{items}</select>'


def code_table(codes) -> str:
    head = ("<tr><th>Code</th><th>Note</th><th class=num>Uses</th><th>Platform</th>"
            "<th>Expires</th><th>State</th><th></th></tr>")
    rows = []
    for c in codes:
        code = escape(c["code"])
        rows.append(
            "<tr>"
            f'<td class="mono"><a href="/c/{code}">{code}</a></td>'
            f'<td>{escape(c["note"]) or "<span class=faint>—</span>"}</td>'
            f'<td class="num">{_uses(c)}</td>'
            f"<td>{_platform(c['platforms'])}</td>"
            f'<td class="faint">{escape((c["expires_at"] or "—")[:10])}</td>'
            f"<td>{_state(c)}</td>"
            '<td><div class="row-actions">'
            f'<form method="post" action="/c/{code}/toggle">'
            f'<button class="link">{"Disable" if c["enabled"] else "Enable"}</button></form>'
            f'<form method="post" action="/c/{code}/delete" data-confirm="Delete {code}?">'
            '<button class="link">Delete</button></form>'
            "</div></td></tr>"
        )
    return _table(head, "".join(rows), "No codes yet")


def redemption_table(redemptions, *, with_app: bool = False, with_code: bool = True) -> str:
    columns = (["When"] + (["App"] if with_app else []) + (["Code"] if with_code else [])
               + ["Platform", "Version", "Country", "Device"])
    head = "<tr>" + "".join(f"<th>{c}</th>" for c in columns) + "</tr>"
    rows = []
    for r in redemptions:
        country = r["country"] or ""
        rows.append(
            "<tr>"
            f'<td class="mono faint">{escape(r["redeemed_at"][:16].replace("T", " "))}</td>'
            + (f'<td class="mono">{escape(r["app_slug"])}</td>' if with_app else "")
            + (f'<td class="mono"><a href="/c/{escape(r["code"])}">{escape(r["code"])}</a></td>'
               if with_code else "")
            + f'<td>{escape(r["platform"] or "—")}</td>'
            + f'<td class="mono faint">{escape(r["app_version"] or "—")}</td>'
            + f'<td>{_flag(country)}{escape(country or "—")}</td>'
            + _device(r["device_id"])
            + "</tr>"
        )
    return _table(head, "".join(rows), "No redemptions yet")


def code_form(action: str, values: dict) -> str:
    def field(name: str) -> str:
        return escape(values.get(name, ""))

    return f"""
    <form class="fields" method="post" action="{action}">
      <label>Code<input name="code" placeholder="auto-generated" class="mono"
             value="{field("code")}"></label>
      <label>How many<input name="quantity" type="number" min="1" max="500" style="width:6.5em"
             value="{field("quantity") or "1"}"></label>
      <label>Note<input name="note" placeholder="press, giveaway…" value="{field("note")}"></label>
      <label>Max uses<input name="max_uses" type="number" min="1" placeholder="∞"
             style="width:6.5em" value="{field("max_uses")}"></label>
      <label>Platform{_select("platforms", PLATFORM_LABELS, values.get("platforms", ""))}</label>
      <label>Expires<input name="expires_at" type="date" value="{field("expires_at")}"></label>
      <button>Create</button>
    </form>"""


# --- pages -------------------------------------------------------------------


def dashboard(totals, apps, platforms, countries, redemptions, values=None, error="") -> str:
    values = values or {}
    rows = "".join(
        "<tr>"
        f'<td><a href="/a/{escape(a["slug"])}">{escape(a["name"])}</a></td>'
        f'<td class="mono faint">{escape(a["slug"])}</td>'
        f'<td class="num">{a["code_count"]}</td>'
        f'<td class="num">{a["redemption_count"]}</td>'
        "</tr>"
        for a in apps
    )
    table = _table(
        "<tr><th>App</th><th>Slug</th><th class=num>Codes</th><th class=num>Redemptions</th></tr>",
        rows,
        "No apps yet. Add one below to start issuing codes.",
    )
    return page(
        "Overview", apps, "overview",
        f"""<div class="page-head"><div><h1>Overview</h1>
          <p class="sub">Every app, code and redemption on this server.</p></div></div>
        {_stats([("apps", totals["apps"]), ("codes", totals["codes"]),
                 ("active", totals["active_codes"]), ("redemptions", totals["redemptions"]),
                 ("devices", totals["devices"])])}
        <h2>Apps</h2>
        {table}
        <div class="card pad">{_note(error)}
          <form class="fields" method="post" action="/apps">
            <label>Slug<input name="slug" placeholder="my-app" class="mono" required
                   value="{escape(values.get("slug", ""))}"></label>
            <label>Name<input name="name" placeholder="My App" required
                   value="{escape(values.get("name", ""))}"></label>
            <button>Add app</button>
          </form>
        </div>
        <div class="grid2">
          <div>{bars(platforms, "By platform")}</div>
          <div>{bars(countries, "By country", flags=True)}</div>
        </div>
        <h2>Latest redemptions</h2>
        {redemption_table(redemptions, with_app=True)}""",
    )


def app_page(app, apps, codes, redemptions, platforms, countries, values=None, error="") -> str:
    values = values or {}
    slug = app["slug"] if app else None
    title = app["name"] if app else "Global codes"
    base = f"/a/{slug}" if slug else "/global"
    if slug:
        head = f"""<div class="page-head">
          <div><h1>{escape(title)}</h1><p class="sub mono">{escape(slug)}</p></div>
          <form method="post" action="/a/{escape(slug)}/delete"
                data-confirm="Delete {escape(title)} and all its codes?">
            <button class="danger">Delete app</button></form></div>"""
    else:
        head = """<div class="page-head"><div><h1>Global codes</h1>
          <p class="sub">Valid in every registered app. Each app spends one use.</p></div></div>"""
    stats = _stats([("codes", len(codes)),
                    ("active", sum(1 for c in codes if c["enabled"])),
                    ("redemptions", sum(c["uses"] for c in codes))])
    breakdowns = (
        f'<div class="grid2"><div>{bars(platforms, "By platform")}</div>'
        f'<div>{bars(countries, "By country", flags=True)}</div></div>'
        if slug
        else ""
    )
    return page(
        title, apps, f"app:{slug}" if slug else "global",
        f"""{head}{stats}
        <h2>New codes</h2>
        <div class="card pad">{_note(error)}{code_form(base + "/codes", values)}</div>
        <h2>Codes <a class="faint" href="{base}/codes.csv">· export CSV</a></h2>
        {code_table(codes)}
        {breakdowns}
        <h2>Latest redemptions</h2>
        {redemption_table(redemptions, with_app=not slug)}""",
    )


def code_page(code, apps, redemptions) -> str:
    scope = (f'<a href="/a/{escape(code["app_slug"])}">{escape(code["app_slug"])}</a>'
             if code["app_slug"] else "all apps")
    return page(
        code["code"], apps, f'app:{code["app_slug"]}' if code["app_slug"] else "global",
        f"""<div class="page-head">
          <div><h1 class="mono">{escape(code["code"])}</h1>
          <p class="sub">Scope: {scope} · created {escape(code["created_at"][:10])}</p></div>
          <form method="post" action="/c/{escape(code["code"])}/delete"
                data-confirm="Delete {escape(code["code"])}?">
            <button class="danger">Delete</button></form></div>
        {_stats([("uses", code["uses"]),
                 ("max uses", "∞" if code["max_uses"] is None else code["max_uses"]),
                 ("platform", PLATFORM_LABELS.get(code["platforms"] or "", "Any")),
                 ("state", "on" if code["enabled"] else "off")])}
        <h2>Settings</h2>
        <div class="card pad">
          <form class="fields" method="post" action="/c/{escape(code["code"])}">
            <label>Note<input name="note" value="{escape(code["note"])}"></label>
            <label>Max uses<input name="max_uses" type="number" min="1" placeholder="∞"
                   value="{code["max_uses"] if code["max_uses"] is not None else ""}"
                   style="width:6.5em"></label>
            <label>Platform{_select("platforms", PLATFORM_LABELS, code["platforms"] or "")}</label>
            <label>Expires<input name="expires_at" type="date"
                   value="{escape((code["expires_at"] or "")[:10])}"></label>
            <label class="check"><input name="enabled" type="checkbox" value="1"
                   {"checked" if code["enabled"] else ""}> Enabled</label>
            <button>Save</button>
          </form>
        </div>
        <h2>Redemptions</h2>
        {redemption_table(redemptions, with_app=True, with_code=False)}""",
    )
