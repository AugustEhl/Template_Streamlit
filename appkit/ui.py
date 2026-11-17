import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import re

import streamlit as st

from . import db

# One tooltip style for every chart in the app (soft translucent green instead of trace-coloured boxes)
HOVERLABEL = dict(bgcolor="rgba(226,236,204,.86)", bordercolor="rgba(118,147,60,.35)", namelength=-1,
                  font=dict(size=13, color="#1c2a10", family="Inter, -apple-system, Segoe UI, sans-serif"))
pio.templates["app"] = go.layout.Template(layout=dict(hoverlabel=HOVERLABEL))
pio.templates.default = "plotly+app"


def _install_chart_style():
    """st.plotly_chart swaps in Streamlit's own template, which drops the default above, so the tooltip style is also applied to
    every figure as it is rendered (st.plotly_chart and container.plotly_chart both end up here). Figures that set their own keep it."""
    from streamlit.delta_generator import DeltaGenerator
    orig = DeltaGenerator.plotly_chart
    if getattr(orig, "_app_style", False):
        return

    def plotly_chart(self, figure_or_data, *a, **kw):
        try:
            if hasattr(figure_or_data, "layout") and figure_or_data.layout.hoverlabel.bgcolor is None:
                figure_or_data.update_layout(hoverlabel=HOVERLABEL)
            is_map = any(getattr(t, "type", "") in ("scattermap", "scattermapbox") for t in figure_or_data.data)
            if not is_map:        # charts are fixed: no zoom, pan or scroll-zoom
                figure_or_data.update_xaxes(fixedrange=True)
                figure_or_data.update_yaxes(fixedrange=True)
                kw["config"] = {**(kw.get("config") or {}), "scrollZoom": False}
            else:                 # maps too: no dragging, wheel zoom, double-click zoom or zoom buttons
                figure_or_data.update_layout(dragmode=False)
                kw["config"] = {**(kw.get("config") or {}), "scrollZoom": False, "doubleClick": False, "displayModeBar": False}
            tip = None if _no_overlay[0] else help_text(figure_or_data)
            if tip:                                  # charts drawn straight into a bordered box get the "?" in that box's top-right corner
                with self:
                    help_button(tip, overlay=True)
        except Exception:
            pass
        return orig(self, figure_or_data, *a, **kw)
    plotly_chart._app_style = True
    DeltaGenerator.plotly_chart = plotly_chart


_no_overlay = [False]
_install_chart_style()


def setup(title: str, icon: str = "📊"):
    """Call first on every page: makes sure the database exists and draws the page title."""
    db.init()
    st.title(f"{icon} {title}")


NO_BAR = {"displayModeBar": False, "scrollZoom": False}     # hides the zoom / pan / download icons that appear on hover; the wheel never zooms


def kpi_row(items: list[tuple[str, str, str | None]]):
    cols = st.columns(len(items))
    for c, (label, value, delta) in zip(cols, items):
        c.metric(label, value, delta)


def tidy(fig, title: str, height: int = 320, **extra):
    """Consistent chart frame: title top-left, legend directly under it (left-aligned), room for both."""
    layout = dict(
        height=height, hovermode="x unified", dragmode=False,
        title=dict(text=f"<b>{title}</b>", xref="paper", x=0, xanchor="left", yref="container", y=0.97, yanchor="top", font=dict(size=15)),
        legend=dict(orientation="h", xref="paper", x=0, xanchor="left", y=1.01, yanchor="bottom", title_text=""),
        margin=dict(l=10, r=10, t=72, b=10),
        hoverlabel=HOVERLABEL)
    layout.update(extra)
    fig.update_layout(**layout)
    return fig


LAYOUT = dict(margin=dict(l=10, r=10, t=72, b=10), legend=dict(orientation="h", x=0, xanchor="left", y=1.01, yanchor="bottom"),
              hovermode="x unified")


def week_text(dates, daily: bool = False) -> list[str]:
    """'Week 46, 2026' (daily=True: 'Week 46 · Mon') for hover labels."""
    out = []
    for d in pd.to_datetime(pd.Series(dates)):
        iso = d.isocalendar()
        out.append(f"Week {iso.week} · {d:%a}" if daily else f"Week {iso.week}, {iso.year}")
    return out


def week_axis(fig, lo, hi, max_ticks: int = 12, shift_days: float = 0):
    """Label a date x-axis with ISO week numbers (W46 …; the year is added at the first tick and at each new year)."""
    lo, hi = pd.Timestamp(lo), pd.Timestamp(hi)
    mondays = pd.date_range(lo - pd.Timedelta(days=lo.weekday()), hi, freq="7D")
    step = max(1, -(-len(mondays) // max_ticks))
    vals = [d for d in mondays[::step] if d >= lo - pd.Timedelta(days=3)]
    shown = [d + pd.Timedelta(days=shift_days) for d in vals]      # shift_days=3.5 centres the labels on weekly bars
    txt, prev = [], None
    for d in vals:
        iso = d.isocalendar()
        txt.append(f"W{iso.week}" + (f"<br>{iso.year}" if prev != iso.year else ""))
        prev = iso.year
    fig.update_xaxes(tickmode="array", tickvals=shown, ticktext=txt, tickangle=0)
    fig.update_layout(margin=dict(l=10, r=10, t=72, b=44))
    return fig



# ---------------------------------------------------------------- "?" help on every chart
# (title prefix in lower case, explanation). The text is looked up from a figure's title (or, for untitled figures, layout.meta).
CHART_HELP: list[tuple[str, str]] = [
    # (chart title prefix in lower case, explanation shown by the "?" on that chart)
    ("example chart", "Explain here what this chart shows. **Bold** works."),
]


def help_text(fig) -> str | None:
    """The explanation for a figure, looked up from its title (or layout.meta when it has no title)."""
    try:
        title = fig.layout.title.text or ""
        if not title and isinstance(fig.layout.meta, str):
            title = fig.layout.meta
    except Exception:
        return None
    title = re.sub(r"<[^>]+>", "", title).strip().lower()
    for prefix, text in CHART_HELP:
        if title.startswith(prefix):
            return text
    return None


_tip_seen: dict = {"run": None, "n": {}}


def _tip_key(prefix: str, text: str) -> str:
    """A key that is stable within one script run and unique per call (the same chart type can appear more than once)."""
    import hashlib
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    ctx = get_script_run_ctx()
    rid = getattr(ctx, "script_run_id", None)
    if rid != _tip_seen["run"]:
        _tip_seen.update(run=rid, n={})
    h = hashlib.md5(text.encode()).hexdigest()[:8]
    _tip_seen["n"][h] = _tip_seen["n"].get(h, 0) + 1
    return f"{prefix}_{h}_{_tip_seen['n'][h]}"


def help_button(text: str, overlay: bool = False):
    """A "?" that shows the explanation while the mouse is over it. overlay=True floats it in the top-right corner of the box it is rendered in."""
    import html as _h
    body = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", _h.escape(text))
    with st.container(key=_tip_key("chelpo" if overlay else "chelp", text)):
        st.html(f"<span class='qm'><span class='qq'>?</span><span class='qt'>{body}</span></span>")


def banner(key: str, text: str, button: str, icon: str, kind: str = "info", button_icon: str | None = None, help: str | None = None) -> bool:
    """A themed banner with its action button inside it (dark-green gradient button). Returns True when the button was clicked.
    kind 'info' = green, 'warn' = amber. `icon` is a Material icon name."""
    with st.container(key=f"nb_{kind}_{key}"):
        a, b = st.columns([6, 1.1], vertical_alignment="center")
        a.markdown(f":material/{icon}: {text}")
        return b.button(button, key=f"nbtn_{key}", type="primary", width="stretch", icon=f":material/{button_icon}:" if button_icon else None, help=help)


def chart_box(box, fig, summary: str | None = None, notes: list[str] | None = None, height: int | None = None,
              switch: tuple[str, list[str]] | None = None):
    """A chart in a bordered box: title (left, flush with the box), optional AI summary, the chart, then notes.
    Boxes in one row can share a fixed `height` so their bottom edges line up."""
    import html
    import re
    title = re.sub(r"</?b>", "", (fig.layout.title.text or "") if fig.layout.title else "")
    tip = help_text(fig)                          # looked up before the title is removed from the figure
    fig.update_layout(title=None, margin=dict(l=4, r=4, t=34, b=fig.layout.margin.b if fig.layout.margin.b is not None else 10),
                      legend=dict(x=0, xanchor="left", y=1.0, yanchor="bottom"))
    # A fixed container height makes Streamlit add an inner scrollbar when summary + notes don't fit. A minimum height keeps the rows
    # even where possible and lets a box with a lot of text grow instead of scrolling.
    ckey = f"cbox_{abs(hash(title)) % 10**8}"
    with box.container(border=True, key=ckey):
        if height:
            st.html(f"<style>.st-key-{ckey}{{min-height:{height}px}}</style>")
        if tip:
            help_button(tip, overlay=True)         # floats in the top-right corner of the box
        if switch:        # (session key, options): a small switch on the title row; the page reads st.session_state[key] to build the figure
            hc = st.columns([5, 3], vertical_alignment="center")
            hc[0].markdown(f"**{title}**")
            hc[1].radio("Unit", switch[1], key=switch[0], horizontal=True, label_visibility="collapsed")
        else:
            st.markdown(f"**{title}**")
        if summary:
            st.markdown("<div style='border-left:3px solid #76933c;background:rgba(118,147,60,.10);padding:6px 12px;border-radius:0 6px 6px 0;"
                        f"font-size:.9rem;line-height:1.45;margin:2px 0 6px'>🤖 {html.escape(summary)}</div>", unsafe_allow_html=True)
        _no_overlay[0] = True                       # the "?" is already in the box's corner
        try:
            fig.update_xaxes(fixedrange=True)       # chart boxes are fixed: no zoom, pan or scroll-zoom
            fig.update_yaxes(fixedrange=True)
            st.plotly_chart(fig, width="stretch", config=NO_BAR)
        finally:
            _no_overlay[0] = False
        if notes:                                   # explanatory text sits in an expander under the graph, so it never crowds the box
            with st.expander("Notes", icon=":material/info:"):
                for n in notes:
                    st.caption(n)


# ---------------------------------------------------------------- cockpit tiles (ring gauges)
def count_up(text: str) -> str:
    """Whole numbers like '-11', '+3', '71%' count up from 0 when they appear (CSS counter on an animated integer); anything else stays as is."""
    import html as _h
    m = re.fullmatch(r"([+-]?)(\d+)(%?)", text.strip())
    if not m:
        return _h.escape(text)
    sign, num, suf = m.groups()
    n = -int(num) if sign == "-" else int(num)
    return f"<span class='cnum' style='--n:{n}' data-pre='{'+' if sign == '+' else ''}' data-suf='{suf}' aria-label='{_h.escape(text)}'></span>"


def ring_card(pct: float | None, big: str, label: str, sub: str = "", color: str = "#4f6228", sub_color: str = "#6b7a4a") -> str:
    """A tile with a ring gauge (CSS conic gradient, no SVG): pct 0-100 fills the ring, `big` sits in its centre."""
    import html as _h
    p = 0 if pct is None else max(0.0, min(float(pct), 100.0))
    return (f"<div style='display:flex;align-items:center;gap:14px;background:#fff;border-radius:18px;padding:11px 16px;height:100px;"
            f"box-shadow:0 6px 28px rgba(79,98,40,.10);border:1px solid rgba(79,98,40,.08);box-sizing:border-box'>"
            f"<div class='cring' style='--p:{p * 3.6:.1f}deg;flex:0 0 68px;width:68px;height:68px;border-radius:50%;display:flex;align-items:center;justify-content:center;"
            f"background:conic-gradient({color} var(--p),#e9efdb 0)'>"
            f"<div style='width:52px;height:52px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;"
            f"font-weight:800;font-size:{'1.02rem' if len(big) <= 4 else '.82rem'};letter-spacing:-.03em;color:#1c2a10;text-align:center;line-height:1.1'>{count_up(big)}</div></div>"
            f"<div style='min-width:0'><div style='font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#76933c'>{_h.escape(label)}</div>"
            f"<div style='font-size:.84rem;font-weight:600;color:{sub_color};margin-top:2px;line-height:1.25'>{sub}</div></div></div>")


def info_card(label: str, big: str, sub: str, tag: str = "", color: str = "#4f6228") -> str:
    """Tile with a headline instead of a ring (e.g. the next workout)."""
    import html as _h
    return (f"<div style='background:linear-gradient(135deg,#5d7530,#3f4f1f);color:#fff;border-radius:18px;padding:12px 18px;height:100px;"
            f"box-shadow:0 8px 28px rgba(79,98,40,.35);box-sizing:border-box'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center'>"
            f"<span style='font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;opacity:.8'>{_h.escape(label)}</span>"
            f"<span style='background:rgba(255,255,255,.2);border-radius:999px;padding:1px 10px;font-size:.75rem;font-weight:700'>{_h.escape(tag)}</span></div>"
            f"<div style='font-size:.9rem;font-weight:800;letter-spacing:-.02em;margin-top:3px;line-height:1.2;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden'>{_h.escape(big)}</div>"
            f"<div style='font-size:.85rem;opacity:.85;margin-top:3px'>{_h.escape(sub)}</div></div>")


def metric_card(label: str, big: str, sub: str = "", color: str = "#4f6228", right: str = "", bottom: str = "", tag: str = "") -> str:
    """A tile without a ring: label, big number (counts up), optional visual on the right (sparkline, dots) and a strip below (zone bar)."""
    import html as _h
    return (f"<div style='display:flex;flex-direction:column;justify-content:space-between;background:#fff;border-radius:18px;padding:10px 16px;height:100px;"
            f"box-shadow:0 6px 28px rgba(79,98,40,.10);border:1px solid rgba(79,98,40,.08);box-sizing:border-box'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center'>"
            f"<span style='font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#76933c'>{_h.escape(label)}</span>"
            + (f"<span style='background:#eef3e0;border-radius:999px;padding:0 8px;font-size:.7rem;font-weight:700;color:#4f6228;white-space:nowrap'>{_h.escape(tag)}</span>" if tag else "")
            + f"</div>"
            f"<div style='display:flex;align-items:center;justify-content:space-between;gap:10px'>"
            f"<div style='font-weight:800;font-size:1.65rem;letter-spacing:-.03em;color:{color};line-height:1'>{count_up(big)}</div>{right}</div>"
            f"<div style='font-size:.76rem;font-weight:600;color:#6b7a4a;line-height:1.2;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden'>{sub}</div>"
            f"{bottom}</div>")


def sparkline(vals: list[float], color: str = "#c8453d", w: int = 76, h: int = 30, delay: float = 0.6) -> str:
    """Tiny inline line chart (SVG) with a dot on the last value."""
    v = [float(x) for x in vals if x == x]
    if len(v) < 2:
        return ""
    lo, hi = min(v), max(v)
    rng = (hi - lo) or 1.0
    pts = [(2 + i * (w - 4) / (len(v) - 1), h - 4 - (x - lo) / rng * (h - 8)) for i, x in enumerate(v)]
    path = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    import base64
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>"
           f"<style>.l{{stroke-dasharray:1;stroke-dashoffset:1;animation:d 1.2s cubic-bezier(.2,.8,.2,1) {delay}s forwards}}"
           f".c{{opacity:0;animation:f .3s ease {delay + 1.1:.2f}s forwards}}"
           f"@keyframes d{{to{{stroke-dashoffset:0}}}}@keyframes f{{to{{opacity:1}}}}"
           f"@media (prefers-reduced-motion:reduce){{.l{{animation:none;stroke-dashoffset:0}}.c{{animation:none;opacity:1}}}}</style>"
           f"<polyline class='l' pathLength='1' points='{path}' fill='none' stroke='{color}' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'/>"
           f"<circle class='c' cx='{pts[-1][0]:.1f}' cy='{pts[-1][1]:.1f}' r='3.5' fill='{color}'/></svg>")
    return f"<img width='{w}' height='{h}' style='flex:0 0 auto' src='data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}'/>"


def zone_bar(value: float, bands: list[tuple[float, str]], lo: float, hi: float) -> str:
    """Horizontal strip of coloured bands (each band = (upper limit, colour)) with a marker at `value`."""
    segs, prev = "", lo
    for up, col in bands:
        up = min(up, hi)
        segs += f"<div style='width:{max(up - prev, 0) / (hi - lo) * 100:.2f}%;background:{col}'></div>"
        prev = up
    pos = max(0.0, min((value - lo) / (hi - lo) * 100, 100.0))
    return (f"<div style='position:relative;height:8px;border-radius:99px;overflow:hidden;display:flex;opacity:.9'>{segs}</div>"
            f"<div style='position:relative;height:0'><div style='position:absolute;left:{pos:.1f}%;top:-12px;width:4px;height:16px;margin-left:-2px;border-radius:2px;"
            f"background:#1c2a10;box-shadow:0 0 0 2px #fff'></div></div>")


def dots(colors: list[str], titles: list[str] | None = None, delay: float = 0.4) -> str:
    return f"<div style='display:flex;gap:4px;--d0:{delay}s'>" + "".join(
        f"<span class='dotp' title='{(titles or [''] * len(colors))[i]}' style='--i:{i};width:9px;height:9px;border-radius:50%;background:{c}'></span>" for i, c in enumerate(colors)) + "</div>"


def ring_row(cards: list[str]):
    cols = st.columns({6: [1.15, 1.15, 1.1, 1, 1, 1]}.get(len(cards), len(cards)))
    for i, (c, h) in enumerate(zip(cols, cards)):
        c.html(f"<div style='--d:{i * 0.18:.2f}s'>{h}</div>")      # the rings fill one after another
