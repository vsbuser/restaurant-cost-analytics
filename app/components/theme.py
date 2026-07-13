import streamlit as st

ACCENT = "#1e8f5e"
STATUS_GOOD = "#159073"
STATUS_WARNING = "#d98b2b"
STATUS_CRITICAL = "#d14343"
INK_MUTED = "#839084"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&display=swap');

h1, h2, h3, [data-testid="stMetricValue"] {
    font-family: 'Poppins', sans-serif !important;
}

[data-testid="stSidebar"] {
    background: #10241a;
}
[data-testid="stSidebar"] * {
    color: #e6f1ea !important;
}
[data-testid="stSidebarNav"] a {
    border-radius: 10px;
}
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: rgba(255,255,255,.10);
}

.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
    border-radius: 12px !important;
    font-weight: 600 !important;
}

.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] { border-radius: 10px 10px 0 0; }

[data-testid="stExpander"] {
    border-radius: 14px;
    border: 1px solid #e1e8dc;
}

[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e1e8dc;
    border-radius: 14px;
    padding: 14px 16px;
}

.kpi-card {
    background: #ffffff;
    border: 1px solid #e1e8dc;
    border-radius: 14px;
    padding: 14px 16px 12px;
    position: relative;
    overflow: hidden;
    margin-bottom: 4px;
}
.kpi-card::before {
    content: "";
    position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
    background: var(--kpi-accent, #1e8f5e);
}
.kpi-card .kpi-label {
    font-size: 11.5px; color: #839084; font-weight: 600;
    text-transform: uppercase; letter-spacing: .04em; margin-bottom: 8px;
}
.kpi-card .kpi-value {
    font-family: 'Poppins', sans-serif; font-size: 24px; font-weight: 700; color: #16211a;
    line-height: 1.1;
}
.kpi-card .kpi-delta {
    font-size: 11.5px; margin-top: 6px; font-weight: 600; color: #4b5d50;
}

.rc-pill {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 11.5px; font-weight: 700; padding: 3px 10px; border-radius: 100px;
}
.rc-pill .rc-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.rc-pill.good { background: rgba(21,144,115,.14); color: #159073; }
.rc-pill.warning { background: rgba(217,139,43,.14); color: #d98b2b; }
.rc-pill.critical { background: rgba(209,67,67,.14); color: #d14343; }
</style>
"""


def aplicar_tema():
    st.markdown(_CSS, unsafe_allow_html=True)


def kpi_card(label, value, delta=None, accent=None):
    accent_attr = f' style="--kpi-accent:{accent}"' if accent else ""
    delta_html = f'<div class="kpi-delta">{delta}</div>' if delta else ""
    st.markdown(
        f'<div class="kpi-card"{accent_attr}>'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f"{delta_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


def status_pill(texto, status):
    return f'<span class="rc-pill {status}"><span class="rc-dot"></span>{texto}</span>'
