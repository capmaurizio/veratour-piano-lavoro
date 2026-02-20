#!/usr/bin/env python3
"""UI Styles — CSS + componenti visivi per Piano Lavoro Streamlit"""

import streamlit as st


def inject_styles():
    """Inject Inter font + professional CSS."""
    st.markdown(
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">',
        unsafe_allow_html=True,
    )
    st.markdown(_CSS, unsafe_allow_html=True)


def render_top_bar(username: str = ""):
    """Render branded top bar."""
    user_html = f'<div class="top-bar-user">{username}</div>' if username else ""
    st.markdown(f"""
    <div class="top-bar">
        <div class="top-bar-brand">
            <div class="top-bar-logo">S</div>
            <div>
                <div class="top-bar-title">Piano Lavoro</div>
                <div class="top-bar-subtitle">Multi-Tour Operator</div>
            </div>
        </div>
        {user_html}
    </div>
    """, unsafe_allow_html=True)


def render_stepper(current_step: int):
    """
    Render a horizontal progress stepper.
    Steps: 0=Upload, 1=Rilevamento, 2=Elaborazione, 3=Completato
    """
    labels = ["Caricamento", "Rilevamento", "Elaborazione", "Completato"]
    parts = []
    for i, label in enumerate(labels):
        if i < current_step:
            dot = '<div class="step-dot step-dot-done">&#10003;</div>'
            cls = "step-done"
        elif i == current_step:
            dot = f'<div class="step-dot step-dot-active">{i + 1}</div>'
            cls = "step-active"
        else:
            dot = f'<div class="step-dot step-dot-pending">{i + 1}</div>'
            cls = "step-pending"
        parts.append(f'<div class="step {cls}">{dot}<div class="step-label">{label}</div></div>')
        if i < len(labels) - 1:
            conn_cls = "step-conn-done" if i < current_step else ""
            parts.append(f'<div class="step-connector {conn_cls}"></div>')
    st.markdown(f'<div class="stepper">{"".join(parts)}</div>', unsafe_allow_html=True)


def render_footer():
    """Render branded footer."""
    st.markdown("""
    <div class="app-footer">
        <span>SCAY Group S.n.c.</span> · Piano Lavoro · Bergamo
    </div>
    """, unsafe_allow_html=True)


def render_stat_card(value, label: str, accent: str = ""):
    """Render a stat card for results dashboard."""
    accent_class = f" stat-{accent}" if accent else ""
    st.markdown(
        f'<div class="stat-card{accent_class}">'
        f'<div class="stat-value">{value}</div>'
        f'<div class="stat-label">{label}</div></div>',
        unsafe_allow_html=True,
    )


def render_status_line(icon: str, text: str, kind: str = "info"):
    """Render an inline status line (kind: info/success/warn/error)."""
    st.markdown(
        f'<div class="status-line status-{kind}">'
        f'<span class="status-icon">{icon}</span>{text}</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
_CSS = """
<style>
/* ═══════════════════════════════════════════
   DESIGN TOKENS
   ═══════════════════════════════════════════ */
:root {
    --ink:       #1a1a2e;
    --ink-2:     #2d2d44;
    --ink-3:     #5a5a72;
    --ink-4:     #8b8ba0;
    --border:    #e6e6ef;
    --bg:        #fafafc;
    --card:      #ffffff;
    --hover:     #f2f2f8;
    --blue:      #3366ff;
    --blue-d:    #2952cc;
    --blue-bg:   #eef3ff;
    --green:     #0d9f6e;
    --green-bg:  #edfcf5;
    --amber:     #d97706;
    --amber-bg:  #fffbeb;
    --red:       #dc2626;
    --red-bg:    #fef2f2;
    --r: 6px;
}

/* ═══════════════════════════════════════════
   GLOBAL
   ═══════════════════════════════════════════ */
html, body, [data-testid="stAppViewContainer"], .main, .block-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: var(--ink) !important;
}
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 0.5rem !important;
    max-width: 960px !important;
}

/* ═══════════════════════════════════════════
   TOP BAR
   ═══════════════════════════════════════════ */
.top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 0;
    margin-bottom: 8px;
    border-bottom: 1px solid var(--border);
}
.top-bar-brand { display: flex; align-items: center; gap: 10px; }
.top-bar-logo {
    width: 28px; height: 28px;
    border-radius: 6px;
    background: var(--ink);
    color: white;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 800;
}
.top-bar-title { font-size: 0.88rem; font-weight: 700; color: var(--ink); }
.top-bar-subtitle { font-size: 0.6rem; color: var(--ink-4); letter-spacing: 0.3px; }
.top-bar-user { font-size: 0.78rem; color: var(--ink-3); font-weight: 500; }

/* ═══════════════════════════════════════════
   STEPPER
   ═══════════════════════════════════════════ */
.stepper {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px 0 12px;
    margin-bottom: 16px;
    gap: 0;
}
.step {
    display: flex;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
}
.step-dot {
    width: 24px; height: 24px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.65rem; font-weight: 700;
    flex-shrink: 0;
    transition: all 0.3s ease;
}
.step-dot-done {
    background: var(--green);
    color: white;
    font-size: 0.7rem;
}
.step-dot-active {
    background: var(--blue);
    color: white;
    box-shadow: 0 0 0 3px var(--blue-bg);
}
.step-dot-pending {
    background: var(--hover);
    color: var(--ink-4);
    border: 1px solid var(--border);
}
.step-label {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--ink-3);
}
.step-active .step-label { color: var(--blue); font-weight: 700; }
.step-done .step-label { color: var(--green); }

.step-connector {
    width: 40px;
    height: 1px;
    background: var(--border);
    margin: 0 8px;
    flex-shrink: 0;
}
.step-conn-done {
    background: var(--green);
}

/* ═══════════════════════════════════════════
   STATUS LINES
   ═══════════════════════════════════════════ */
.status-line {
    display: flex;
    align-items: baseline;
    gap: 8px;
    padding: 8px 14px;
    border-radius: var(--r);
    font-size: 0.82rem;
    font-weight: 500;
    margin: 4px 0;
    line-height: 1.5;
}
.status-icon { flex-shrink: 0; font-size: 0.75rem; }
.status-info    { background: var(--blue-bg); color: var(--blue-d); }
.status-success { background: var(--green-bg); color: #065f46; }
.status-warn    { background: var(--amber-bg); color: #92400e; }
.status-error   { background: var(--red-bg); color: var(--red); }

/* ═══════════════════════════════════════════
   LOGIN
   ═══════════════════════════════════════════ */
.login-card {
    max-width: 340px;
    margin: 0 auto;
    padding: 28px 24px 20px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--r);
}
.login-brand {
    display: flex; align-items: center; justify-content: center;
    gap: 8px; margin-bottom: 2px;
}
.login-logo {
    width: 28px; height: 28px; border-radius: 5px;
    background: var(--ink); color: white;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 800;
}
.login-brand-text { font-size: 1rem; font-weight: 700; color: var(--ink); }
.login-subtitle {
    font-size: 0.76rem; color: var(--ink-4);
    text-align: center; margin-bottom: 16px;
}
.login-footer {
    text-align: center; margin-top: 14px; padding-top: 12px;
    border-top: 1px solid var(--border);
    font-size: 0.68rem; color: var(--ink-4);
}
.login-wrapper [data-testid="stForm"] {
    max-width: 340px; margin: 0 auto;
    border: none !important; padding: 0 !important;
}
.login-wrapper [data-testid="stForm"] input {
    font-size: 0.82rem !important; padding: 9px 12px !important;
    border-radius: var(--r) !important; border: 1px solid var(--border) !important;
}
.login-wrapper [data-testid="stForm"] label {
    font-size: 0.78rem !important; font-weight: 500 !important; color: var(--ink-2) !important;
}
.login-wrapper [data-testid="stForm"] button {
    border-radius: var(--r) !important; padding: 9px 20px !important;
    font-size: 0.82rem !important; font-weight: 600 !important;
    min-height: auto !important;
    background: var(--blue) !important; color: white !important;
    border: none !important; margin-top: 6px !important;
}
.login-wrapper [data-testid="stForm"] button:hover {
    background: var(--blue-d) !important;
}
.login-wrapper .stMarkdown { max-width: 340px; margin: 0 auto; }

/* ═══════════════════════════════════════════
   BUTTONS
   ═══════════════════════════════════════════ */
.stButton > button {
    border-radius: var(--r) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    border: 1px solid var(--border) !important;
    padding: 9px 18px !important;
    min-height: auto !important;
    background: var(--card) !important;
    color: var(--ink-3) !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    border-color: var(--ink-4) !important;
    color: var(--ink) !important;
    background: var(--hover) !important;
}
button[kind="primary"],
button[kind="primary"][data-testid="stBaseButton-primary"] {
    background: var(--blue) !important;
    color: white !important;
    border: none !important;
    font-size: 0.85rem !important;
    padding: 11px 24px !important;
    letter-spacing: 0.2px !important;
}
button[kind="primary"]:hover,
button[kind="primary"][data-testid="stBaseButton-primary"]:hover {
    background: var(--blue-d) !important;
}
button[kind="secondary"] {
    font-size: 0.76rem !important; min-height: auto !important;
    padding: 7px 14px !important;
}
.stDownloadButton > button {
    background: var(--green) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--r) !important;
    padding: 11px 24px !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
    font-family: 'Inter', sans-serif !important;
    min-height: auto !important;
    transition: all 0.15s ease !important;
}
.stDownloadButton > button:hover { background: #0b8a5e !important; }

/* ═══════════════════════════════════════════
   STAT CARDS
   ═══════════════════════════════════════════ */
.stat-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 16px 12px;
    text-align: center;
}
.stat-value {
    font-size: 1.5rem; font-weight: 800; color: var(--ink);
    letter-spacing: -0.5px; line-height: 1.2;
}
.stat-label {
    font-size: 0.65rem; font-weight: 600; color: var(--ink-4);
    text-transform: uppercase; letter-spacing: 0.5px; margin-top: 3px;
}
.stat-green .stat-value { color: var(--green); }
.stat-amber .stat-value { color: var(--amber); }
.stat-red   .stat-value { color: var(--red); }

/* ═══════════════════════════════════════════
   FILE UPLOAD & EXPANDERS
   ═══════════════════════════════════════════ */
[data-testid="stFileUploader"] {
    border: 1px dashed var(--border) !important;
    border-radius: var(--r) !important;
    padding: 16px !important;
    background: var(--bg) !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--blue) !important; }
[data-testid="stFileUploader"] label {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important; color: var(--ink-2) !important;
}
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    background: var(--card) !important;
}
[data-testid="stExpander"] summary {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important; font-size: 0.82rem !important;
    color: var(--ink) !important;
}

/* ═══════════════════════════════════════════
   MISC
   ═══════════════════════════════════════════ */
hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 16px 0 !important; }
.app-footer {
    text-align: center; padding: 12px 0 6px; margin-top: 24px;
    border-top: 1px solid var(--border);
    font-size: 0.65rem; color: var(--ink-4);
}
.stAlert { border-radius: var(--r) !important; font-family: 'Inter', sans-serif !important; font-size: 0.82rem !important; }
</style>
"""
