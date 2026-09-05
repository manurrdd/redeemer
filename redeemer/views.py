from __future__ import annotations

from html import escape

from .export import DATASETS, FORMATS, STATUS
from .export import SCOPES as EXPORT_SCOPES

CSS = """
:root {
  color-scheme: light;
  --canvas: #f7f6f3; --side: #f2f0ec; --surface: #fff; --raised: #faf9f6;
  --line: #e5e1d9; --line-soft: #efece6;
  --ink: #1b1a17; --muted: #6b665c; --faint: #9c968a;
  --accent: #0f7a55; --accent-ink: #0b6046; --accent-soft: #e4f0ea;
  --bad: #b3261e; --bad-soft: #fbecea;
  --btn: #23211d; --btn-ink: #faf9f6;
  --shadow: 0 1px 2px rgba(28, 25, 20, .05), 0 4px 14px rgba(28, 25, 20, .03);
  --ring: 0 0 0 3px rgba(15, 122, 85, .16);
}
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --canvas: #0d0e10; --side: #101215; --surface: #16181c; --raised: #1b1e22;
    --line: #272a30; --line-soft: #202328;
    --ink: #eceae5; --muted: #9b978f; --faint: #6e6b66;
    --accent: #4ecb96; --accent-ink: #7bdcb1; --accent-soft: #16261f;
    --bad: #f5796b; --bad-soft: #2a1614;
    --btn: #eceae5; --btn-ink: #16181c;
    --shadow: none;
    --ring: 0 0 0 3px rgba(78, 203, 150, .18);
  }
}
* { box-sizing: border-box; }
[hidden] { display: none !important; }
body { margin: 0; background: var(--canvas); color: var(--ink);
       font: 14px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, ui-sans-serif,
             system-ui, sans-serif;
       -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility; }
a { color: inherit; text-decoration: none; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.muted { color: var(--muted); }
.faint { color: var(--faint); }

/* ---- shell ---- */
.shell { display: grid; grid-template-columns: 246px 1fr; min-height: 100vh; }
.shell.collapsed { grid-template-columns: 60px 1fr; }
aside { position: sticky; top: 0; height: 100vh; display: flex; flex-direction: column; gap: 2px;
        padding: 14px 12px; background: var(--side); border-right: 1px solid var(--line); }
.shell.collapsed aside { padding: 14px 10px; }
.side-head { display: flex; align-items: center; gap: 10px; height: 38px; margin-bottom: 12px;
             padding-left: 4px; }
.mark { flex: none; display: grid; place-items: center; width: 26px; height: 26px; border-radius: 8px;
        background: var(--accent); color: #fff; font-size: 13px; font-weight: 700; letter-spacing: -.02em; }
.brand { flex: 1; font-size: 15px; font-weight: 640; letter-spacing: -.015em; }
.toggle { flex: none; width: 30px; height: 30px; display: grid; place-items: center; padding: 0;
          border: 0; border-radius: 8px; background: transparent; color: var(--faint); cursor: pointer; }
.toggle:hover { background: var(--line-soft); color: var(--ink); }
.shell.collapsed .brand { display: none; }
.shell.collapsed .side-head { position: relative; justify-content: center; padding: 0; }
.shell.collapsed .toggle { position: absolute; inset: 0; width: 100%; height: 100%; opacity: 0;
                           background: var(--side); }
.shell.collapsed .toggle:hover { opacity: 1; background: var(--line-soft); }
@media (hover: none) { .shell.collapsed .toggle { opacity: 1; } }

nav { display: flex; flex-direction: column; gap: 1px; min-height: 0; overflow: hidden auto; }
.item { flex: none; height: 36px; width: 100%; display: flex; align-items: center; gap: 10px;
        padding: 0 10px; border: 1px solid transparent; border-radius: 9px; background: none;
        color: var(--muted); font: inherit; font-size: 13.5px; white-space: nowrap; cursor: pointer; }
.item:hover { background: var(--line-soft); color: var(--ink); }
.item.on { background: var(--surface); border-color: var(--line); color: var(--ink); font-weight: 560;
           box-shadow: var(--shadow); }
.item.on svg { color: var(--accent); }
.item svg, .item .avatar { flex: none; }
.avatar { display: grid; place-items: center; width: 19px; height: 19px; border-radius: 6px;
          background: var(--line); color: var(--muted); font-size: 9px; font-weight: 700; }
.item.on .avatar { background: var(--accent); color: #fff; }
.item .label { overflow: hidden; text-overflow: ellipsis; }
.shell.collapsed .item { padding: 0; justify-content: center; }
.shell.collapsed .item .label, .shell.collapsed .group { display: none; }
.group { flex: none; margin: 18px 10px 6px; font-size: 10.5px; font-weight: 650; color: var(--faint);
         letter-spacing: .08em; text-transform: uppercase; }
.side-foot { flex: none; margin-top: auto; padding-top: 8px; }

/* ---- page ---- */
main { padding: 40px 44px 96px; min-width: 0; }
.wrap { max-width: 1000px; margin: 0 auto; }
.head { display: flex; align-items: flex-start; gap: 20px; margin-bottom: 22px; }
.head form { margin-left: auto; }
h1 { margin: 0; font-size: 25px; font-weight: 620; letter-spacing: -.025em; }
h1.mono { font-size: 22px; letter-spacing: -.01em; }
.sub { margin: 5px 0 0; color: var(--muted); font-size: 13px; }
.lead { margin: -8px 0 24px; max-width: 62ch; color: var(--muted); font-size: 13.5px; }
section { margin-top: 34px; }
.title { display: flex; align-items: center; gap: 12px; margin: 0 0 12px; font-size: 11px;
         font-weight: 650; letter-spacing: .08em; text-transform: uppercase; color: var(--faint); }
.title a { margin-left: auto; color: var(--accent-ink); font-size: 12px; font-weight: 550;
           letter-spacing: 0; text-transform: none; }
.title a:hover { text-decoration: underline; }
.box { background: var(--surface); border: 1px solid var(--line); border-radius: 14px;
       box-shadow: var(--shadow); overflow: hidden; }
.box.pad { padding: 18px; }
.split { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.split section { display: flex; flex-direction: column; margin-top: 0; }
.split .box { flex: 1; }
@media (max-width: 860px) { .split { grid-template-columns: 1fr; } }

/* ---- stats ---- */
.stats { display: flex; flex-wrap: wrap; margin: -4px 0 4px; }
.stat { padding: 0 26px; border-right: 1px solid var(--line); }
.stat:first-child { padding-left: 0; }
.stat:last-child { padding-right: 0; border-right: 0; }
.stat b { display: block; font-size: 22px; font-weight: 600; letter-spacing: -.03em;
          font-variant-numeric: tabular-nums; }
.stat span { display: block; color: var(--muted); font-size: 12.5px; }

/* ---- chips ---- */
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 4px; }
.chip { display: inline-flex; align-items: center; gap: 7px; height: 27px; padding: 0 12px;
        border: 1px solid var(--line); border-radius: 999px; background: var(--surface);
        color: var(--muted); font-size: 12.5px; }
.chip a { color: var(--accent-ink); font-weight: 550; }
.chip a:hover { text-decoration: underline; }
.chip.on, .chip.off { padding-left: 11px; }
.chip.on::before, .chip.off::before { content: ""; width: 5px; height: 5px; border-radius: 50%;
                                      background: var(--faint); }
.chip.on { border-color: transparent; background: var(--accent-soft); color: var(--accent-ink); }
.chip.on::before { background: var(--accent); }

/* ---- tables ---- */
.scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: 10px 16px; background: var(--raised); color: var(--faint);
     border-bottom: 1px solid var(--line); font-size: 10.5px; font-weight: 650;
     letter-spacing: .07em; text-transform: uppercase; white-space: nowrap; }
td { padding: 11px 16px; border-top: 1px solid var(--line-soft); white-space: nowrap; }
tbody tr:first-child td { border-top: 0; }
tbody tr:hover td { background: var(--raised); }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
td.act { text-align: right; padding: 5px 8px; }
.code-link { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px;
             font-weight: 560; letter-spacing: -.01em; }
.code-link:hover { color: var(--accent-ink); text-decoration: underline; }
tr.fresh td { background: var(--accent-soft); }
tr.fresh td:first-child { box-shadow: inset 2px 0 0 var(--accent); }
tr.fresh:hover td { background: var(--accent-soft); }
.fresh-note { display: flex; align-items: center; gap: 12px; margin: 0 0 12px; padding: 10px 14px;
              border: 1px solid var(--line); border-radius: 11px; background: var(--accent-soft);
              color: var(--accent-ink); font-size: 13px; }
.fresh-note a { margin-left: auto; font-weight: 560; }
.fresh-note a:hover { text-decoration: underline; }
.empty { padding: 32px 18px; text-align: center; color: var(--faint); font-size: 13.5px; }
.empty a { color: var(--accent-ink); font-weight: 550; }
.pill { display: inline-flex; align-items: center; gap: 6px; height: 23px; padding: 0 10px;
        border-radius: 999px; background: var(--line-soft); color: var(--muted); font-size: 12px; }
.pill::before { content: ""; width: 5px; height: 5px; border-radius: 50%; background: var(--faint); }
.pill.on { background: var(--accent-soft); color: var(--accent-ink); }
.pill.on::before { background: var(--accent); }

/* ---- rows ---- */
.bar { display: flex; align-items: center; gap: 12px; padding: 13px 18px; }
.bar + .bar { border-top: 1px solid var(--line-soft); }
.bar b { font-size: 16px; font-weight: 600; font-variant-numeric: tabular-nums; }
.bar form { display: flex; flex: 1; align-items: center; gap: 12px; margin: 0; }
.bar form button { margin-left: auto; }

/* ---- forms ---- */
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(158px, 1fr)); gap: 16px; }
.grid > .wide { grid-column: span 2; }
@media (max-width: 560px) { .grid > .wide { grid-column: auto; } }
label { display: flex; flex-direction: column; gap: 6px; min-width: 0; color: var(--muted);
        font-size: 12px; font-weight: 550; }
fieldset { grid-column: 1 / -1; display: flex; flex-wrap: wrap; gap: 10px 22px; margin: 0;
           padding: 12px 14px; border: 1px solid var(--line); border-radius: 11px;
           background: var(--raised); }
legend { padding: 0 5px; color: var(--muted); font-size: 12px; font-weight: 550; }
.hint { color: var(--faint); font-size: 11.5px; font-weight: 450; }
label.check { flex-direction: row; align-items: center; gap: 8px; color: var(--ink); font-size: 13px;
              font-weight: 450; }
.grid > label.check { align-self: end; height: 36px; }
input, select { width: 100%; height: 36px; padding: 0 11px; border: 1px solid var(--line);
                border-radius: 9px; background: var(--surface); color: var(--ink); font: inherit;
                font-size: 13.5px; }
select { appearance: none; padding-right: 30px; background-image:
  url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' \
viewBox='0 0 24 24' fill='none' stroke='%238a857a' stroke-width='2.4' stroke-linecap='round' \
stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 11px center; }
input[type=file] { max-width: 400px; height: auto; padding: 8px 10px; }
input[type=checkbox] { width: auto; height: auto; accent-color: var(--accent); }
input::placeholder { color: var(--faint); }
input:focus, select:focus { outline: none; border-color: var(--accent); box-shadow: var(--ring); }
button { height: 36px; padding: 0 17px; border: 1px solid transparent; border-radius: 9px;
         background: var(--btn); color: var(--btn-ink); font: inherit; font-size: 13.5px;
         font-weight: 560; cursor: pointer; transition: opacity .14s ease, background .14s ease; }
button:hover { opacity: .86; }
button.quiet { height: 30px; padding: 0 11px; background: none; color: var(--muted);
               font-weight: 450; font-size: 13px; }
button.quiet:hover { background: var(--line-soft); color: var(--ink); opacity: 1; }
button.quiet.risk:hover { background: var(--bad-soft); color: var(--bad); }
.form-foot { display: flex; justify-content: flex-end; margin-top: 18px; padding-top: 16px;
             border-top: 1px solid var(--line-soft); }
.warn { margin: 0 0 14px; padding: 10px 13px; border-radius: 10px; font-size: 13px;
        color: var(--bad); background: var(--bad-soft);
        border: 1px solid color-mix(in srgb, var(--bad) 24%, transparent); }

/* ---- bars ---- */
.bars { display: grid; gap: 4px; }
.bars .b { position: relative; display: grid; grid-template-columns: 1fr auto; gap: 12px;
           align-items: center; padding: 8px 12px; border-radius: 8px; font-size: 13px; }
.bars .fill { position: absolute; inset: 0 auto 0 0; border-radius: 8px;
              background: var(--accent-soft); }
.bars .b > span { position: relative; }
.bars .n { color: var(--muted); font-size: 12.5px; font-variant-numeric: tabular-nums; }

/* ---- login ---- */
.login { width: 336px; margin: 15vh auto; }
.login .mark { width: 34px; height: 34px; margin: 0 auto 16px; font-size: 16px; border-radius: 10px; }
.login h1 { margin-bottom: 20px; font-size: 20px; text-align: center; }
.login .box { padding: 24px; }
.login form { display: grid; gap: 16px; }

@media (max-width: 760px) {
  .shell, .shell.collapsed { grid-template-columns: 1fr; }
  aside, .shell.collapsed aside { position: static; height: auto; flex-direction: row;
    align-items: center; gap: 6px; padding: 8px 12px; overflow-x: auto;
    border-right: 0; border-bottom: 1px solid var(--line); }
  .side-head { margin: 0; padding: 0; }
  .brand, .toggle, .group { display: none; }
  nav { flex-direction: row; gap: 4px; overflow: visible; }
  .item, .shell.collapsed .item { width: auto; padding: 0 12px; }
  .item .label, .shell.collapsed .item .label { display: inline; }
  .side-foot { margin: 0 0 0 auto; padding: 0; }
  main { padding: 26px 18px 72px; }
  .head { flex-wrap: wrap; }
}
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
    "data": '<rect x="2.5" y="3.5" width="19" height="5" rx="1.5"/>'
              '<path d="M4.5 8.5v10a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-10"/>'
              '<path d="M10 12.5h4"/>',
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
document.addEventListener('change',e=>{if(e.target.name!=='scope')return;
  e.target.closest('form').querySelector('.apps').hidden=e.target.value!=='selected'});
document.addEventListener('change',e=>{const f=e.target.form;if(!f||!f.format)return;
  const txt=f.format.value==='txt',on=n=>txt?n==='codes':[...f.include].some(c=>c.checked&&c.value===n);
  f.querySelector('.include').hidden=txt;
  f.querySelectorAll('.codes').forEach(x=>x.hidden=!on('codes'));
  f.querySelectorAll('.uses').forEach(x=>x.hidden=!on('redemptions'))});
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
      <div class="side-head"><span class="mark">R</span><span class="brand">Redeemer</span>
        <button class="toggle" aria-label="Toggle sidebar">{icon("panel", 18)}</button></div>
      <nav>
        {item("/", icon("overview"), "Overview", "overview")}
        {item("/global", icon("globe"), "Global codes", "global")}
        {item("/data", icon("data"), "Data", "data")}
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
        '<div class="login"><div class="mark">R</div><h1>Redeemer</h1>'
        f'<div class="box pad">{warn(error)}'
        '<form method="post" action="/login">'
        '<label>Password<input type="password" name="password" autofocus></label>'
        "<button>Sign in</button></form></div></div></html>"
    )


def not_found(apps=()) -> str:
    return page("Not found", apps, "", '<div class="box"><p class="empty">Not found.</p></div>')


# --- pieces ------------------------------------------------------------------


def warn(message: str) -> str:
    return f'<p class="warn">{escape(message)}</p>' if message else ""


def head(title: str, action: str = "", *, mono: bool = False, sub: str = "") -> str:
    klass = ' class="mono"' if mono else ""
    line = f'<p class="sub mono">{escape(sub)}</p>' if sub else ""
    return f'<div class="head"><div><h1{klass}>{escape(title)}</h1>{line}</div>{action}</div>'


def stats(*items: tuple[int, str, str]) -> str:
    tiles = "".join(
        f'<div class="stat"><b>{count}</b><span>{escape(one if count == 1 else many)}</span></div>'
        for count, one, many in items
    )
    return f'<div class="stats">{tiles}</div>'


def chips(*parts) -> str:
    """Each part is HTML, or (HTML, modifier class)."""
    items = "".join(
        f'<span class="chip {p[1] if isinstance(p, tuple) else ""}">'
        f'{p[0] if isinstance(p, tuple) else p}</span>'
        for p in parts if p
    )
    return f'<div class="chips">{items}</div>'


def lead(text: str) -> str:
    return f'<p class="lead">{escape(text)}</p>'


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


def _spans_apps(row) -> bool:
    """Quota only means something for a code more than one app can spend."""
    return bool(row["is_global"]) or "," in (row["app_names"] or "")


def _uses(row) -> str:
    limit = "∞" if row["max_uses"] is None else row["max_uses"]
    if not _spans_apps(row):
        return f'{row["uses"]} / {limit}'
    if row["quota_mode"] == "per_app":
        return f'{row["uses"]} total · {limit}/app'
    return f'{row["uses"]} / {limit} shared'


def code_rows(codes, fresh: str = "") -> list[str]:
    rows = []
    for c in codes:
        code = escape(c["code"])
        new = ' class="fresh"' if fresh and c["batch"] == fresh else ""
        platform = PLATFORMS.get(c["platforms"] or "", c["platforms"] or "Any")
        expires = (c["expires_at"] or "")[:10]
        rows.append(
            f"<tr{new}>"
            f'<td><a class="code-link" href="/c/{c['id']}">{code}</a></td>'
            f'<td class="muted">{escape(c["note"]) or ""}</td>'
            f'<td>{"All apps" if c["is_global"] else escape(c["app_names"] or "")}</td>'
            f'<td class="num">{_uses(c)}</td>'
            f'<td class="muted">{escape(platform)}</td>'
            f'<td class="muted">{escape(expires)}</td>'
            f'<td><span class="pill{" on" if c["enabled"] else ""}">'
            f'{"Active" if c["enabled"] else "Off"}</span></td>'
            f'<td class="act"><form method="post" action="/c/{c['id']}/toggle">'
            f'<button class="quiet">{"Disable" if c["enabled"] else "Enable"}</button></form></td>'
            "</tr>"
        )
    return rows


def code_table(codes, fresh: str = "") -> str:
    head = ("<tr><th>Code</th><th>Note</th><th>Apps</th><th class=num>Uses</th><th>Platform</th>"
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
            + (f'<td><a class="code-link" href="/c/{r["code_id"]}">'
               f'{escape(r["code"])}</a></td>' if with_code else "")
            + f'<td class="muted">{escape(r["platform"] or "—")}</td>'
            + f'<td class="muted">{escape(r["app_version"] or "—")}</td>'
            + f'<td class="muted">{_flag(country)}{escape(country or "—")}</td>'
            + device
            + "</tr>"
        )
    return table(head, rows, "No redemptions yet")


QUOTAS = {"shared": "Shared across apps", "per_app": "Per app"}
SCOPES = {"selected": "Selected apps", "global": "All apps (including future apps)"}


def code_form(action: str, values: dict, apps, default_slug=None) -> str:
    def field(name: str, fallback: str = "") -> str:
        return escape(values.get(name, "") or fallback)

    scope = ""
    if default_slug is None:
        chosen = values.get("scope", "global")
        choices = "".join(
            f'<label class="check"><input type="checkbox" name="app:{escape(a["slug"])}" value="1"'
            f'{" checked" if values.get("app:" + a["slug"]) == "1" else ""}>'
            f'{escape(a["name"])}</label>' for a in apps
        )
        scope = (
            f'<label class="wide">Valid in{_select("scope", SCOPES, chosen)}</label>'
            f'<fieldset class="apps"{"" if chosen == "selected" else " hidden"}>'
            f'<legend>Apps</legend>{choices or "Register an app first."}</fieldset>'
            f'<label>Quota{_select("quota_mode", QUOTAS, values.get("quota_mode", "shared"))}</label>'
        )
    return f"""<div class="box pad">
      <form method="post" action="{action}">
        <div class="grid">
          {scope}
          <label>Code<input name="code" class="mono" placeholder="auto"
                 value="{field("code")}"></label>
          <label>How many<input name="quantity" type="number" min="1" max="500"
                 value="{field("quantity", "1")}"></label>
          <label>Note<input name="note" placeholder="optional" value="{field("note")}"></label>
          <label>Max uses<input name="max_uses" type="number" min="1" placeholder="∞"
                 value="{field("max_uses")}"></label>
          <label>Platform{_select("platforms", PLATFORMS, values.get("platforms", ""))}</label>
          <label>Expires<input name="expires_at" type="date" value="{field("expires_at")}"></label>
        </div>
        <div class="form-foot"><button>Create</button></div>
      </form>
    </div>"""


# --- pages -------------------------------------------------------------------


def dashboard(totals, apps, platforms, countries, redemptions) -> str:
    if not apps:
        return page(
            "Overview", apps, "overview",
            head("Overview")
            + '<div class="box"><p class="empty">No apps yet. '
              '<a href="/apps/new">Add the first one</a> to start issuing codes.</p></div>',
        )
    return page(
        "Overview", apps, "overview",
        f"""{head("Overview")}
        {stats((totals["apps"], "app", "apps"),
               (totals["active_codes"], "active code", "active codes"),
               (totals["redemptions"], "redemption", "redemptions"))}
        <section><div class="split">{bars(platforms, "Platforms")}
          {bars(countries, "Countries", flags=True)}</div></section>
        {section("Latest redemptions", redemption_table(redemptions, with_app=True))}""",
    )


def export_form(apps, values) -> str:
    def one(name: str, fallback: str = "") -> str:
        chosen = values.get(name) or []
        return chosen[0] if chosen else fallback

    def checks(name: str, options, marked) -> str:
        return "".join(
            f'<label class="check"><input type="checkbox" name="{name}" value="{escape(value)}"'
            f'{" checked" if value in marked else ""}>{escape(label)}</label>'
            for value, label in options
        )

    def shown(on: bool) -> str:
        return "" if on else " hidden"

    fmt = one("format", "csv")
    scope = one("scope", "all")
    included = set(values.get("include") or ["codes"])
    codes = shown(fmt == "txt" or "codes" in included)
    uses = shown(fmt != "txt" and "redemptions" in included)
    picked = checks("app", [(a["slug"], a["name"]) for a in apps], set(values.get("app") or []))
    return f"""<div class="box pad">
      <form method="get" action="/data/export">
        <div class="grid">
          <label>Format{_select("format", FORMATS, fmt)}</label>
          <label class="codes"{codes}>Code status{_select("status", STATUS, one("status", "all"))}</label>
          <label class="uses"{uses}>Redeemed from
            <input type="date" name="from" value="{escape(one("from"))}"></label>
          <label class="uses"{uses}>Redeemed to
            <input type="date" name="to" value="{escape(one("to"))}"></label>
          <label class="check uses"{uses}><input type="checkbox" name="devices" value="1"
                 {"checked" if not values or one("devices") == "1" else ""}> Device ids</label>
          <fieldset class="include"{shown(fmt != "txt")}><legend>Include</legend>
            {checks("include", DATASETS.items(), included)}</fieldset>
          <label class="wide">Apps{_select("scope", EXPORT_SCOPES, scope)}</label>
          <fieldset class="apps"{shown(scope == "selected")}><legend>Apps</legend>
            {picked or "Register an app first."}</fieldset>
        </div>
        <div class="form-foot"><button>Export</button></div>
      </form>
    </div>"""


def data_page(apps, snapshots: int, latest: str, values=None, error="", restore_error="") -> str:
    backup = f"""<div class="box">
      <div class="bar"><b>{snapshots}</b>
        <span class="muted">{"snapshot" if snapshots == 1 else "snapshots"}</span>
        {f'<span class="faint">{escape(latest)}</span>' if latest else ""}
        <form method="get" action="/backup.db.gz"><button>Download</button></form></div>
      <div class="bar">
        <form method="post" action="/restore" enctype="multipart/form-data"
              data-confirm="Replace every app, code and redemption with this file?">
          <input type="file" name="file" accept=".gz,.db" required>
          <button>Restore</button></form></div>
    </div>"""
    return page(
        "Data", apps, "data",
        head("Data")
        + section("Export", warn(error) + export_form(apps, values or {}))
        + section("Backup", warn(restore_error) + backup),
    )


def new_app(apps, values=None, error="") -> str:
    values = values or {}
    return page(
        "New app", apps, "new",
        f"""{head("New app")}
        {lead("The slug is what your app sends in every request. Pick it once; it cannot change.")}
        <div class="box pad">{warn(error)}
          <form method="post" action="/apps">
            <div class="grid">
              <label>Slug<input name="slug" class="mono" placeholder="my-app" required
                     value="{escape(values.get("slug", ""))}"></label>
              <label>Name<input name="name" placeholder="My App" required
                     value="{escape(values.get("name", ""))}"></label>
            </div>
            <div class="form-foot"><button>Create</button></div>
          </form>
        </div>""",
    )


def app_page(app, apps, codes, redemptions, platforms, countries,
             values=None, error="", fresh="", fresh_count=0) -> str:
    values = values or {}
    slug = app["slug"] if app else None
    title = app["name"] if app else "Global codes"
    base = f"/a/{slug}" if slug else "/global"
    used = app["redemption_count"] if app else sum(c["uses"] for c in codes)
    if slug:
        top = head(
            title,
            f'''<form method="post" action="/a/{escape(slug)}/delete"
                data-confirm="Delete {escape(title)}? Codes shared with other apps will remain.">
              <button class="quiet risk">Delete app</button></form>''',
            sub=slug,
        )
    else:
        top = head("Global codes") + lead(
            "Valid in every registered app, including future apps. Quota is shared or per app.")
    banner = ""
    if fresh_count:
        banner = (f'<p class="fresh-note">{fresh_count} '
                  f'{"code" if fresh_count == 1 else "codes"} just created'
                  f'<a href="{base}/codes.csv?batch={escape(fresh)}">Export just these</a></p>')
    return page(
        title, apps, f"app:{slug}" if slug else "global",
        f"""{top}
        {stats((len(codes), "code", "codes"), (used, "redemption", "redemptions"))}
        {section("New codes", warn(error) + code_form(base + "/codes", values, apps, slug))}
        {section("Codes", banner + code_table(codes, fresh),
                 link=(base + "/codes.csv", "Export CSV"))}
        <section><div class="split">{bars(platforms, "Platforms")}
          {bars(countries, "Countries", flags=True)}</div></section>
        {section("Latest redemptions", redemption_table(redemptions, with_app=not slug))}""",
    )


def code_page(code, apps, redemptions, platforms, countries, app_slugs, app_uses) -> str:
    name = escape(code["code"])
    scope = "every app (including future apps)" if code["is_global"] else ", ".join(
        f'<a href="/a/{escape(slug)}">{escape(slug)}</a>' for slug in app_slugs
    )
    quota = (f'<label>Quota{_select("quota_mode", QUOTAS, code["quota_mode"])}'
             '<small class="hint">Changing it keeps all previous uses.</small></label>'
             ) if _spans_apps(code) else ""
    return page(
        code["code"], apps, f"app:{app_slugs[0]}" if app_slugs else "global",
        f"""{head(code["code"], f'''<form method="post" action="/c/{code['id']}/delete"
              data-confirm="Delete {name}?">
            <button class="quiet risk">Delete code</button></form>''', mono=True)}
        {chips(f"valid in {scope}", _uses(code),
               escape(PLATFORMS.get(code["platforms"], "any platform")
                      if code["platforms"] else "any platform"),
               f'expires {escape(code["expires_at"][:10])}' if code["expires_at"] else "",
               ("Active", "on") if code["enabled"] else ("Off", "off"))}
        {section("Settings", f'''<div class="box pad">
          <form method="post" action="/c/{code['id']}">
            <div class="grid">
              <label>Note<input name="note" value="{escape(code["note"])}"></label>
              <label>Max uses<input name="max_uses" type="number" min="1" placeholder="∞"
                     value="{code["max_uses"] if code["max_uses"] is not None else ""}"></label>
              {quota}
              <label>Platform{_select("platforms", PLATFORMS, code["platforms"] or "")}</label>
              <label>Expires<input name="expires_at" type="date"
                     value="{escape((code["expires_at"] or "")[:10])}"></label>
              <label class="check"><input name="enabled" type="checkbox" value="1"
                     {"checked" if code["enabled"] else ""}> Enabled</label>
            </div>
            <div class="form-foot"><button>Save</button></div>
          </form></div>''')}
        <section><div class="split">{bars(platforms, "Platforms")}
          {bars(countries, "Countries", flags=True)}</div></section>
        {bars(app_uses, "Uses by app")}
        {section("Redemptions",
                 redemption_table(redemptions, with_app=True, with_code=False))}""",
    )
