from __future__ import annotations

from html import escape

CSS = """
:root {
  color-scheme: light dark;
  --bg: #fff; --side: #fafafa; --line: #e8e9ec; --line-soft: #f1f2f4;
  --ink: #16181d; --muted: #62697a; --faint: #9aa0ad;
  --accent: #3d5afe; --accent-soft: #eef1ff;
  --ok: #15803d; --bad: #dc2626; --bar: #dfe4fd;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #0f1115; --side: #14161b; --line: #24272f; --line-soft: #1b1e24;
          --ink: #e8eaee; --muted: #9199a8; --faint: #6a7180;
          --accent: #7d94ff; --accent-soft: #1a1f38; --ok: #4ade80; --bad: #f87171;
          --bar: #232a45; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
       font: 14px/1.5 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
       -webkit-font-smoothing: antialiased; }
a { color: inherit; text-decoration: none; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.muted { color: var(--muted); }
.faint { color: var(--faint); }

/* ---- shell ---- */
.shell { display: grid; grid-template-columns: 240px 1fr; min-height: 100vh; }
.shell.collapsed { grid-template-columns: 56px 1fr; }
aside { position: sticky; top: 0; height: 100vh; display: flex; flex-direction: column;
        gap: 2px; padding: 10px; background: var(--side);
        border-right: 1px solid var(--line); }
.shell.collapsed aside { padding: 10px 8px; }
.side-head { display: flex; align-items: center; height: 40px; margin-bottom: 6px; }
.brand { flex: 1; padding-left: 10px; font-size: 15px; font-weight: 650; letter-spacing: -.01em; }
.toggle { flex: none; width: 32px; height: 32px; display: grid; place-items: center; border: 0;
          border-radius: 8px; background: transparent; color: var(--faint); cursor: pointer;
          padding: 0; }
.toggle:hover { background: var(--line); color: var(--ink); }
.shell.collapsed .brand { display: none; }
.shell.collapsed .side-head { justify-content: center; }

nav { display: flex; flex-direction: column; gap: 2px; min-height: 0;
      overflow: hidden auto; }
.item { flex: none; height: 36px; display: flex; align-items: center; gap: 10px; padding: 0 10px;
        border-radius: 8px; color: var(--muted); font-size: 14px; white-space: nowrap;
        border: 0; background: none; font-family: inherit; cursor: pointer; width: 100%; }
.item:hover { background: var(--line-soft); color: var(--ink); }
.item.on { background: var(--accent-soft); color: var(--accent); font-weight: 550; }
.item svg, .item .avatar { flex: none; }
.avatar { display: grid; place-items: center; width: 18px; height: 18px; border-radius: 5px;
          background: var(--line); color: var(--muted); font-size: 9px; font-weight: 700; }
.item.on .avatar { background: var(--accent); color: #fff; }
.item .label { overflow: hidden; text-overflow: ellipsis; }
.shell.collapsed .item { padding: 0; justify-content: center; }
.shell.collapsed .item .label, .shell.collapsed .group { display: none; }
.group { flex: none; margin: 14px 10px 4px; font-size: 11px; font-weight: 600; color: var(--faint);
         letter-spacing: .04em; }
.side-foot { flex: none; margin-top: auto; padding-top: 6px; }

/* ---- page ---- */
main { padding: 34px 36px 80px; min-width: 0; }
.wrap { max-width: 900px; margin: 0 auto; }
.head { display: flex; align-items: flex-start; gap: 16px; margin-bottom: 6px; }
.head form { margin-left: auto; }
h1 { margin: 0; font-size: 21px; font-weight: 620; letter-spacing: -.02em; }
h1.mono { font-size: 20px; letter-spacing: 0; }
.facts { margin: 0 0 26px; color: var(--muted); font-size: 13px; }
.facts b { color: var(--ink); font-weight: 600; font-variant-numeric: tabular-nums; }
section { margin-top: 30px; }
.title { display: flex; align-items: baseline; gap: 10px; margin: 0 0 10px; font-size: 13px;
         font-weight: 600; }
.title a { color: var(--accent); font-weight: 500; font-size: 12.5px; }
.box { border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }
.box.pad { padding: 14px; }
.split { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
@media (max-width: 800px) { .split { grid-template-columns: 1fr; } }

/* ---- tables ---- */
.scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; font-size: 12px; font-weight: 550; color: var(--faint); padding: 9px 14px;
     white-space: nowrap; background: var(--side); border-bottom: 1px solid var(--line); }
td { padding: 10px 14px; border-top: 1px solid var(--line-soft); white-space: nowrap; }
tbody tr:first-child td { border-top: 0; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
td.act { text-align: right; padding: 6px 8px; }
.code-link { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13.5px;
             font-weight: 550; }
.code-link:hover { color: var(--accent); }
tr.fresh td { background: var(--accent-soft); }
tr.fresh td:first-child { box-shadow: inset 2px 0 0 var(--accent); }
.fresh-note { display: flex; align-items: baseline; gap: 10px; margin: 0 0 10px;
              font-size: 13px; color: var(--accent); }
.fresh-note a { font-weight: 550; }
.empty { padding: 34px 16px; text-align: center; color: var(--faint); font-size: 13.5px; }
.dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; margin-right: 7px;
       vertical-align: 1px; background: var(--ok); }
.dot.off { background: var(--faint); }

/* ---- forms ---- */
.fields { display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-end; }
label { display: flex; flex-direction: column; gap: 5px; font-size: 12px; color: var(--muted); }
label.check { flex-direction: row; align-items: center; gap: 7px; height: 34px; }
input, select { height: 34px; padding: 0 10px; border: 1px solid var(--line); border-radius: 7px;
                background: var(--bg); color: var(--ink); font: inherit; font-size: 13.5px; }
input[type=date] { padding-right: 6px; }
input::placeholder { color: var(--faint); }
input:focus, select:focus { outline: none; border-color: var(--accent);
                            box-shadow: 0 0 0 3px var(--accent-soft); }
button { height: 34px; padding: 0 15px; border: 1px solid transparent; border-radius: 7px;
         background: var(--accent); color: #fff; font: inherit; font-size: 13.5px; font-weight: 550;
         cursor: pointer; }
button:hover { filter: brightness(1.07); }
button.quiet { height: 28px; padding: 0 9px; background: none; color: var(--muted);
               font-weight: 450; font-size: 13px; }
button.quiet:hover { background: var(--line-soft); color: var(--ink); filter: none; }
button.quiet.risk:hover { color: var(--bad); }
.warn { margin: 0 0 12px; padding: 9px 12px; border-radius: 8px; font-size: 13px;
        color: var(--bad); background: color-mix(in srgb, var(--bad) 9%, transparent); }

/* ---- bars ---- */
.bars { display: grid; gap: 6px; }
.bars .b { position: relative; display: grid; grid-template-columns: 1fr auto; gap: 10px;
           align-items: center; padding: 6px 10px; border-radius: 6px; font-size: 13.5px; }
.bars .fill { position: absolute; inset: 0 auto 0 0; background: var(--bar); border-radius: 6px; }
.bars .b > span { position: relative; }
.bars .n { color: var(--muted); font-variant-numeric: tabular-nums; font-size: 12.5px; }

/* ---- login ---- */
.login { width: 300px; margin: 16vh auto; }
.login h1 { margin-bottom: 18px; text-align: center; }
.login form { display: grid; gap: 14px; }
.login button { width: 100%; }
"""

ICONS = {
    "overview": '<path d="M4 13.5 9 8.5l3.5 3.5L20 4.5"/><path d="M4 19.5h16"/>',
    "globe": '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 9.5h17M3.5 14.5h17"/>'
             '<path d="M12 3.5c2.3 2.3 3.4 5.1 3.4 8.5S14.3 18.2 12 20.5c-2.3-2.3-3.4-5.1-3.4-8.5"'
             ' /><path d="M12 3.5C9.7 5.8 8.6 8.6 8.6 12"/>',
    "plus": '<path d="M12 5.5v13M5.5 12h13"/>',
    "logout": '<path d="M14 3.5h4A2.5 2.5 0 0 1 20.5 6v12a2.5 2.5 0 0 1-2.5 2.5h-4"/>'
              '<path d="m9.5 16 4-4-4-4"/><path d="M13.5 12H3.5"/>',
    "panel": '<rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/><path d="M9.5 4.5v15"/>',
}


def icon(name: str, size: int = 17) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" '
        f'stroke-linejoin="round">{ICONS[name]}</svg>'
    )


SCRIPT = """
<script>
document.addEventListener('submit',e=>{const m=e.target.dataset.confirm;if(m&&!confirm(m))e.preventDefault()});
document.addEventListener('click',e=>{if(!e.target.closest('.toggle'))return;
  const s=document.querySelector('.shell');s.classList.toggle('collapsed');
  try{localStorage.setItem('sidebar',s.classList.contains('collapsed')?'1':'0')}catch(_){}});
</script>
"""

EARLY = ("<script>try{if(localStorage.getItem('sidebar')==='1')"
         "document.currentScript.parentNode.classList.add('collapsed')}catch(_){}</script>")


def _initials(name: str) -> str:
    letters = [word[0] for word in name.split() if word[0].isalnum()]
    return escape("".join(letters[:2]).upper() or "?")


def sidebar(apps, active: str) -> str:
    def item(href: str, mark: str, label: str, key: str) -> str:
        on = " on" if key == active else ""
        return (f'<a class="item{on}" href="{href}" title="{escape(label)}">{mark}'
                f'<span class="label">{escape(label)}</span></a>')

    entries = "".join(
        item(f'/a/{escape(a["slug"])}', f'<span class="avatar">{_initials(a["name"])}</span>',
             a["name"], f'app:{a["slug"]}')
        for a in apps
    )
    group = '<p class="group">Apps</p>' if apps else ""
    return f"""<aside>
      <div class="side-head"><span class="brand">Redeemer</span>
        <button class="toggle" aria-label="Toggle sidebar">{icon("panel", 18)}</button></div>
      <nav>
        {item("/", icon("overview"), "Overview", "overview")}
        {item("/global", icon("globe"), "Global codes", "global")}
        {group}{entries}
        {item("/apps/new", icon("plus"), "New app", "new")}
      </nav>
      <form class="side-foot" method="post" action="/logout">
        <button class="item" title="Sign out">{icon("logout")}
          <span class="label">Sign out</span></button>
      </form>
    </aside>"""


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
        f'<div class="login"><h1>Redeemer</h1>{warn(error)}'
        '<form method="post" action="/login">'
        '<label>Password<input type="password" name="password" autofocus></label>'
        "<button>Sign in</button></form></div></html>"
    )


def not_found(apps=()) -> str:
    return page("Not found", apps, "", '<div class="box"><p class="empty">Not found.</p></div>')


# --- pieces ------------------------------------------------------------------


def warn(message: str) -> str:
    return f'<p class="warn">{escape(message)}</p>' if message else ""


def facts(*parts: str) -> str:
    return f'<p class="facts">{" · ".join(p for p in parts if p)}</p>'


def section(title: str, body: str, *, link: tuple[str, str] | None = None) -> str:
    extra = f'<a href="{link[0]}">{escape(link[1])}</a>' if link else ""
    return f'<section><p class="title">{escape(title)}{extra}</p>{body}</section>'


def table(head: str, rows: list[str], empty: str) -> str:
    if not rows:
        return f'<div class="box"><p class="empty">{escape(empty)}</p></div>'
    return (f'<div class="box scroll"><table><thead>{head}</thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def _flag(country: str) -> str:
    if len(country) != 2 or not country.isalpha():
        return ""
    return "".join(chr(0x1F1E6 + ord(c) - 65) for c in country.upper()) + " "


def bars(rows, title: str, *, flags: bool = False) -> str:
    if not rows:
        return section(title, '<div class="box"><p class="empty">Nothing yet</p></div>')
    top = max(row["count"] for row in rows) or 1
    items = "".join(
        f'<div class="b"><div class="fill" style="width:{row["count"] * 100 // top}%"></div>'
        f'<span>{_flag(row["value"]) if flags else ""}{escape(row["value"])}</span>'
        f'<span class="n">{row["count"]}</span></div>'
        for row in rows
    )
    return section(title, f'<div class="box pad"><div class="bars">{items}</div></div>')


PLATFORMS = {"": "Any", "ios": "iOS", "android": "Android", "ios,android": "iOS + Android"}


def _select(name: str, options: dict, chosen: str) -> str:
    items = "".join(
        f'<option value="{escape(v)}"{" selected" if v == chosen else ""}>{escape(t)}</option>'
        for v, t in options.items()
    )
    return f'<select name="{name}">{items}</select>'


def _uses(row) -> str:
    return f'{row["uses"]} / {"∞" if row["max_uses"] is None else row["max_uses"]}'


def code_rows(codes, fresh: str = "") -> list[str]:
    rows = []
    for c in codes:
        code = escape(c["code"])
        new = ' class="fresh"' if fresh and c["batch"] == fresh else ""
        platform = PLATFORMS.get(c["platforms"] or "", c["platforms"] or "Any")
        expires = (c["expires_at"] or "")[:10]
        rows.append(
            f"<tr{new}>"
            f'<td><a class="code-link" href="/c/{code}">{code}</a></td>'
            f'<td class="muted">{escape(c["note"]) or ""}</td>'
            f'<td class="num">{_uses(c)}</td>'
            f'<td class="muted">{escape(platform)}</td>'
            f'<td class="muted">{escape(expires)}</td>'
            f'<td><span class="dot{"" if c["enabled"] else " off"}"></span>'
            f'{"Active" if c["enabled"] else "Off"}</td>'
            f'<td class="act"><form method="post" action="/c/{code}/toggle">'
            f'<button class="quiet">{"Disable" if c["enabled"] else "Enable"}</button></form></td>'
            "</tr>"
        )
    return rows


def code_table(codes, fresh: str = "") -> str:
    head = ("<tr><th>Code</th><th>Note</th><th class=num>Uses</th><th>Platform</th>"
            "<th>Expires</th><th>Status</th><th></th></tr>")
    return table(head, code_rows(codes, fresh), "No codes yet")


def redemption_table(redemptions, *, with_app: bool = False, with_code: bool = True) -> str:
    columns = (["When"] + (["App"] if with_app else []) + (["Code"] if with_code else [])
               + ["Platform", "Version", "Country", "Device"])
    head = "<tr>" + "".join(f"<th>{c}</th>" for c in columns) + "</tr>"
    rows = []
    for r in redemptions:
        country = r["country"] or ""
        device = (f'<td class="mono faint">{escape(r["device_id"][:8])}…</td>'
                  if r["device_id"] else '<td class="faint">anonymous</td>')
        rows.append(
            "<tr>"
            f'<td class="muted">{escape(r["redeemed_at"][:16].replace("T", " "))}</td>'
            + (f'<td>{escape(r["app_slug"])}</td>' if with_app else "")
            + (f'<td><a class="code-link" href="/c/{escape(r["code"])}">'
               f'{escape(r["code"])}</a></td>' if with_code else "")
            + f'<td class="muted">{escape(r["platform"] or "—")}</td>'
            + f'<td class="muted">{escape(r["app_version"] or "—")}</td>'
            + f'<td class="muted">{_flag(country)}{escape(country or "—")}</td>'
            + device
            + "</tr>"
        )
    return table(head, rows, "No redemptions yet")


def code_form(action: str, values: dict) -> str:
    def field(name: str, fallback: str = "") -> str:
        return escape(values.get(name, "") or fallback)

    return f"""<div class="box pad">
      <form class="fields" method="post" action="{action}">
        <label>Code<input name="code" class="mono" placeholder="auto" style="width:8.5em"
               value="{field("code")}"></label>
        <label>How many<input name="quantity" type="number" min="1" max="500" style="width:5em"
               value="{field("quantity", "1")}"></label>
        <label>Note<input name="note" placeholder="optional" style="width:10em"
               value="{field("note")}"></label>
        <label>Max uses<input name="max_uses" type="number" min="1" placeholder="∞"
               style="width:5.5em" value="{field("max_uses")}"></label>
        <label>Platform{_select("platforms", PLATFORMS, values.get("platforms", ""))}</label>
        <label>Expires<input name="expires_at" type="date" value="{field("expires_at")}"></label>
        <button>Create</button>
      </form>
    </div>"""


def _plural(count: int, one: str, many: str) -> str:
    return f"<b>{count}</b> {one if count == 1 else many}"


# --- pages -------------------------------------------------------------------


def dashboard(totals, apps, platforms, countries, redemptions) -> str:
    if not apps:
        return page(
            "Overview", apps, "overview",
            '<div class="head"><h1>Overview</h1></div>'
            '<div class="box"><p class="empty">No apps yet. '
            '<a href="/apps/new" style="color:var(--accent)">Add the first one</a> '
            "to start issuing codes.</p></div>",
        )
    return page(
        "Overview", apps, "overview",
        f"""<div class="head"><h1>Overview</h1></div>
        {facts(_plural(totals["apps"], "app", "apps"),
               _plural(totals["active_codes"], "active code", "active codes"),
               _plural(totals["redemptions"], "redemption", "redemptions"))}
        <div class="split">{bars(platforms, "Platforms")}
          {bars(countries, "Countries", flags=True)}</div>
        {section("Latest redemptions", redemption_table(redemptions, with_app=True))}""",
    )


def new_app(apps, values=None, error="") -> str:
    values = values or {}
    return page(
        "New app", apps, "new",
        f"""<div class="head"><h1>New app</h1></div>
        {facts("The slug is what your app sends in every request. Pick it once; it cannot change.")}
        <div class="box pad">{warn(error)}
          <form class="fields" method="post" action="/apps">
            <label>Slug<input name="slug" class="mono" placeholder="my-app" required
                   style="width:14em" value="{escape(values.get("slug", ""))}"></label>
            <label>Name<input name="name" placeholder="My App" required style="width:14em"
                   value="{escape(values.get("name", ""))}"></label>
            <button>Create</button>
          </form>
        </div>""",
    )


def app_page(app, apps, codes, redemptions, platforms, countries,
             values=None, error="", fresh="", fresh_count=0) -> str:
    values = values or {}
    slug = app["slug"] if app else None
    title = app["name"] if app else "Global codes"
    base = f"/a/{slug}" if slug else "/global"
    used = sum(c["uses"] for c in codes)
    if slug:
        head = f"""<div class="head"><h1>{escape(title)}</h1>
          <form method="post" action="/a/{escape(slug)}/delete"
                data-confirm="Delete {escape(title)} and all its codes?">
            <button class="quiet risk">Delete app</button></form></div>
        {facts(f'<span class="mono">{escape(slug)}</span>',
               _plural(len(codes), "code", "codes"),
               _plural(used, "redemption", "redemptions"))}"""
    else:
        head = ('<div class="head"><h1>Global codes</h1></div>'
                + facts("Valid in every app. Each app spends one use.",
                        _plural(len(codes), "code", "codes"),
                        _plural(used, "redemption", "redemptions")))
    banner = ""
    if fresh_count:
        banner = (f'<p class="fresh-note">{fresh_count} '
                  f'{"code" if fresh_count == 1 else "codes"} just created'
                  f'<a href="{base}/codes.csv?batch={escape(fresh)}">Export just these</a></p>')
    return page(
        title, apps, f"app:{slug}" if slug else "global",
        f"""{head}
        {section("New codes", warn(error) + code_form(base + "/codes", values))}
        {section("Codes", banner + code_table(codes, fresh),
                 link=(base + "/codes.csv", "Export CSV"))}
        <div class="split">{bars(platforms, "Platforms")}
          {bars(countries, "Countries", flags=True)}</div>
        {section("Latest redemptions", redemption_table(redemptions, with_app=not slug))}""",
    )


def code_page(code, apps, redemptions, platforms, countries) -> str:
    name = escape(code["code"])
    scope = (f'<a href="/a/{escape(code["app_slug"])}" style="color:var(--accent)">'
             f'{escape(code["app_slug"])}</a>' if code["app_slug"] else "every app")
    limits = [
        f'<b>{code["uses"]}</b> of {"∞" if code["max_uses"] is None else code["max_uses"]} uses',
        PLATFORMS.get(code["platforms"], "any platform") if code["platforms"] else "any platform",
        f'expires {escape(code["expires_at"][:10])}' if code["expires_at"] else "",
        "active" if code["enabled"] else "disabled",
    ]
    return page(
        code["code"], apps, f'app:{code["app_slug"]}' if code["app_slug"] else "global",
        f"""<div class="head"><h1 class="mono">{name}</h1>
          <form method="post" action="/c/{name}/delete" data-confirm="Delete {name}?">
            <button class="quiet risk">Delete code</button></form></div>
        {facts(f"valid in {scope}", *limits)}
        {section("Settings", f'''<div class="box pad">
          <form class="fields" method="post" action="/c/{name}">
            <label>Note<input name="note" style="width:14em"
                   value="{escape(code["note"])}"></label>
            <label>Max uses<input name="max_uses" type="number" min="1" placeholder="∞"
                   style="width:6em"
                   value="{code["max_uses"] if code["max_uses"] is not None else ""}"></label>
            <label>Platform{_select("platforms", PLATFORMS, code["platforms"] or "")}</label>
            <label>Expires<input name="expires_at" type="date"
                   value="{escape((code["expires_at"] or "")[:10])}"></label>
            <label class="check"><input name="enabled" type="checkbox" value="1"
                   {"checked" if code["enabled"] else ""}> Enabled</label>
            <button>Save</button>
          </form></div>''')}
        <div class="split">{bars(platforms, "Platforms")}
          {bars(countries, "Countries", flags=True)}</div>
        {section("Redemptions",
                 redemption_table(redemptions, with_app=True, with_code=False))}""",
    )
