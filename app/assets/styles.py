"""InsightFlow theme: dark violet glass UI (inspired by modern fintech dashboards).

Place at: app/assets/styles.py
Call load_custom_css() ONCE in main.py (not in every page).
"""
import streamlit as st

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
  --bg: #050907;
  --surface: rgba(255,255,255,0.04);
  --surface-2: rgba(255,255,255,0.07);
  --border: rgba(255,255,255,0.08);
  --border-strong: rgba(78,240,142,0.38);
  --primary: #22e66b;
  --primary-2: #12b85a;
  --primary-soft: #4ef08e;
  --text: #f2f7f4;
  --muted: #8fa59a;
  --ok: #34d399;
  --warn: #fbbf24;
  --bad: #fb7185;
  --radius: 18px;
}

/* ---------- App shell ---------- */
html, body, .stApp { font-family: 'Inter', sans-serif; }
.stApp {
  color: var(--text);
  background:
    radial-gradient(900px 480px at 62% -8%, rgba(34,230,107,0.32), transparent 62%),
    radial-gradient(700px 420px at 0% 100%, rgba(16,185,129,0.14), transparent 60%),
    var(--bg);
  background-attachment: fixed;
}
.block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1280px; }

/* Keep the sidebar toggle visible; hide only Streamlit chrome */
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer { display: none !important; }

h1, h2, h3 { letter-spacing: -0.02em; color: var(--text); }
h1 { font-weight: 700; }
h2, h3 { font-weight: 600; }
p, li, label, .stMarkdown { color: var(--text); }
[data-testid="stCaptionContainer"], .stCaption { color: var(--muted) !important; }
hr { border-color: var(--border) !important; margin: 1.6rem 0 !important; }

::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: rgba(78,240,142,0.25); border-radius: 8px; }
::-webkit-scrollbar-thumb:hover { background: rgba(78,240,142,0.45); }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #08100c 0%, #040806 100%);
  border-right: 1px solid var(--border);
}
[data-testid="stSidebarNav"]::before {
  content: "◆  InsightFlow AI";
  display: block;
  padding: 1.1rem 0.9rem 0.7rem;
  font-weight: 700;
  font-size: 1.15rem;
  letter-spacing: -0.02em;
  background: linear-gradient(90deg, #ffffff, #a7f9c8);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
[data-testid="stNavSectionHeader"] {
  color: var(--muted); font-size: 0.7rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.1em;
}
[data-testid="stSidebarNavLink"] {
  border-radius: 12px; margin: 2px 0; padding: 0.55rem 0.75rem;
  color: var(--muted); border: 1px solid transparent; transition: all 0.2s ease;
}
[data-testid="stSidebarNavLink"]:hover { background: var(--surface-2); color: var(--text); }
[data-testid="stSidebarNavLink"][aria-current="page"] {
  background: linear-gradient(135deg, rgba(34,230,107,0.30), rgba(18,184,90,0.10));
  border-color: var(--border-strong); color: #fff; font-weight: 600;
  box-shadow: 0 0 24px rgba(34,230,107,0.18);
}

/* ---------- Native components ---------- */
[data-testid="stMetric"] {
  background: linear-gradient(160deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
  border: 1px solid var(--border); border-radius: var(--radius);
  padding: 1.1rem 1.25rem; box-shadow: 0 10px 30px rgba(0,0,0,0.25);
}
[data-testid="stMetricLabel"] p {
  color: var(--muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em;
}
[data-testid="stMetricValue"] { font-weight: 700; letter-spacing: -0.02em; }

/* Cards: use ui_components.card("name") -> container with key "card_name" */
[class*="st-key-card_"] {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 1.25rem 1.4rem;
  backdrop-filter: blur(14px); box-shadow: 0 12px 34px rgba(0,0,0,0.28);
  transition: border-color 0.25s ease, transform 0.25s ease;
}
[class*="st-key-card_"]:hover { border-color: var(--primary); box-shadow: 0 0 0 1px rgba(34,230,107,0.35), 0 0 30px rgba(34,230,107,0.15); }

/* Buttons */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
  border-radius: 12px; font-weight: 600; padding: 0.55rem 1.1rem;
  border: 1px solid var(--border); background: var(--surface-2); color: var(--text);
  transition: all 0.25s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color: var(--border-strong); color: #fff; transform: translateY(-1px);
}
.stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"], .stDownloadButton > button {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-2) 100%);
  border: 1px solid rgba(78,240,142,0.6); color: #04110a !important;
  box-shadow: 0 6px 22px rgba(34,230,107,0.40);
}
.stButton > button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover, .stDownloadButton > button:hover {
  box-shadow: 0 8px 30px rgba(34,230,107,0.60); filter: brightness(1.08);
}

/* Page links as pills */
[data-testid="stPageLink-NavLink"] {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 0.6rem 0.9rem; transition: all 0.2s ease;
}
[data-testid="stPageLink-NavLink"]:hover {
  border-color: var(--border-strong); background: rgba(34,230,107,0.12);
}

/* File uploader */
[data-testid="stFileUploaderDropzone"] {
  background: rgba(34,230,107,0.06); border: 1.5px dashed rgba(78,240,142,0.45);
  border-radius: var(--radius); padding: 2rem; transition: all 0.2s ease;
}
[data-testid="stFileUploaderDropzone"]:hover {
  background: rgba(34,230,107,0.12); border-color: var(--primary-soft);
}

/* Alerts, expanders, tables, tabs */
[data-testid="stAlert"] { border-radius: 14px; border: 1px solid var(--border); backdrop-filter: blur(8px); }
[data-testid="stExpander"] details {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
}
[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 14px; overflow: hidden; }
button[data-baseweb="tab"] { color: var(--muted); }
button[data-baseweb="tab"][aria-selected="true"] { color: #fff; }
[data-baseweb="tab-highlight"] { background: var(--primary) !important; }
[data-testid="stPlotlyChart"] { border-radius: 14px; overflow: hidden; }

/* ---------- Custom components (ui_components.py) ---------- */
.if-ticker { overflow: hidden; margin: 1.2rem 0 0.4rem; border-radius: 10px; background: linear-gradient(90deg, #12b85a, #22e66b); box-shadow: 0 0 28px rgba(34,230,107,0.25); }
.if-ticker__track { display: inline-flex; white-space: nowrap; animation: if-scroll 28s linear infinite; }
.if-ticker__item { padding: 0.45rem 1.6rem; font-size: 0.72rem; font-weight: 800; letter-spacing: 0.22em; color: #04110a; text-transform: uppercase; }
@keyframes if-scroll { from { transform: translateX(0); } to { transform: translateX(-50%); } }
.if-header { margin-bottom: 1.8rem; padding-bottom: 1.1rem; border-bottom: 1px solid var(--border); }
.if-header h1 {
  display: flex; align-items: center; gap: 0.7rem; margin: 0 0 0.25rem 0;
  font-size: 2.2rem; font-weight: 700; letter-spacing: -0.03em;
}
.if-header p { margin: 0; color: var(--muted); font-size: 1.05rem; }

.if-pill {
  display: inline-block; padding: 3px 10px; border-radius: 999px;
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.02em; border: 1px solid transparent;
}
.if-pill--ready  { background: rgba(34,230,107,0.15); color: #a7f9c8; border-color: rgba(34,230,107,0.35); }
.if-pill--done   { background: var(--primary); color: #04110a; border-color: var(--primary); }
.if-pill--next   { background: rgba(251,191,36,0.12); color: var(--warn); border-color: rgba(251,191,36,0.30); }
.if-pill--locked { background: rgba(255,255,255,0.04); color: var(--muted); border-color: var(--border); }

.if-hero {
  position: relative; overflow: hidden; border-radius: 24px; padding: 2.6rem 2.6rem 2.4rem;
  border: 1px solid var(--border-strong);
  background: linear-gradient(135deg, rgba(34,230,107,0.32) 0%, rgba(8,30,19,0.78) 55%, rgba(4,9,7,0.92) 100%);
  box-shadow: 0 24px 60px rgba(6,95,70,0.28);
  margin-bottom: 1rem;
}
.if-hero::after {
  content: ""; position: absolute; right: -50px; top: -70px; width: 360px; height: 360px;
  border-radius: 50%; opacity: 0.85; pointer-events: none;
  background: radial-gradient(circle at 35% 35%, rgba(255,255,255,0.55), rgba(78,240,142,0.35) 25%, rgba(18,184,90,0.15) 50%, transparent 70%);
}
.if-eyebrow {
  display: inline-block; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.14em;
  color: var(--primary-soft); text-transform: uppercase; margin-bottom: 0.8rem;
}
.if-hero h2 { position: relative; z-index: 1; font-size: 2.5rem; line-height: 1.12; font-weight: 800; letter-spacing: -0.035em; margin: 0 0 0.8rem 0; max-width: 620px; }
.if-grad { background: linear-gradient(90deg, #22e66b, #2dd4bf); -webkit-background-clip: text; background-clip: text; color: transparent; }
.if-hero p  { position: relative; z-index: 1; color: #c5d6cc; font-size: 1.05rem; max-width: 560px; margin: 0; }

.if-stat {
  background: linear-gradient(160deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
  border: 1px solid var(--border); border-radius: var(--radius);
  padding: 1.15rem 1.3rem; box-shadow: 0 10px 30px rgba(0,0,0,0.25);
  display: flex; justify-content: space-between; align-items: flex-end; gap: 1rem;
}
.if-stat__label { color: var(--muted); font-size: 0.74rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.45rem; }
.if-stat__value { font-size: 1.9rem; font-weight: 700; letter-spacing: -0.03em; line-height: 1.1; }
.if-stat__delta { font-size: 0.82rem; font-weight: 600; margin-top: 0.35rem; display: inline-block; }
.if-stat__delta--up { color: var(--ok); }
.if-stat__delta--down { color: var(--bad); }
.if-stat__delta--flat { color: var(--muted); }

.if-step {
  height: 100%; min-height: 150px; background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 1rem 1.1rem; transition: border-color 0.2s ease;
}
.if-step:hover { border-color: var(--border-strong); }
.if-step__top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.7rem; }
.if-step__num { font-size: 0.85rem; font-weight: 700; color: var(--primary-soft); letter-spacing: 0.05em; }
.if-step__title { font-weight: 600; font-size: 1rem; margin-bottom: 0.3rem; }
.if-step__desc { color: var(--muted); font-size: 0.82rem; line-height: 1.45; }

.if-empty {
  text-align: center; padding: 3rem 1.5rem 2.2rem; margin-bottom: 0.8rem;
  border: 1px dashed rgba(78,240,142,0.35); border-radius: 22px; background: rgba(34,230,107,0.05);
}
.if-empty__icon { font-size: 2.4rem; margin-bottom: 0.6rem; }
.if-empty__title { font-size: 1.25rem; font-weight: 600; margin-bottom: 0.3rem; }
.if-empty__msg { color: var(--muted); max-width: 460px; margin: 0 auto; }

.if-sidebar-status {
  margin-top: 1rem; padding: 0.9rem 1rem; border-radius: 14px;
  background: rgba(34,230,107,0.08); border: 1px solid var(--border-strong);
}
.if-sidebar-status__label { color: var(--muted); font-size: 0.68rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; }
.if-sidebar-status__name  { font-weight: 600; margin: 0.25rem 0 0.15rem; word-break: break-all; }
.if-sidebar-status__meta  { color: var(--muted); font-size: 0.8rem; }
"""


def load_custom_css() -> None:
    """Inject the global InsightFlow theme. Call once from main.py."""
    st.markdown("<style>" + _CSS + "</style>", unsafe_allow_html=True)