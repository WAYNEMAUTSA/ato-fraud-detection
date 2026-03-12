import time
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="ATO Shield", page_icon="🛡", layout="centered")

# ── Load Data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    scores = pd.read_csv("data/processed/risk_scores.csv")
    X = pd.read_csv("data/processed/X_test.csv")
    return scores, X

scores, X = load_data()

total_txns = len(scores)
blocked    = len(scores[scores['risk_label'] == 'HIGH'])
flagged    = len(scores[scores['risk_label'] == 'MEDIUM'])
safe       = len(scores[scores['risk_label'] == 'LOW'])
high_risk  = scores[scores['risk_label'] == 'HIGH'].copy()

# ── Simulation state ──────────────────────────────────────────────────────────
if 'sim_running'   not in st.session_state: st.session_state['sim_running']   = False
if 'sim_index'     not in st.session_state: st.session_state['sim_index']     = 0
if 'sim_live'      not in st.session_state: st.session_state['sim_live']      = []
if 'sim_blocked'   not in st.session_state: st.session_state['sim_blocked']   = 0
if 'sim_flagged'   not in st.session_state: st.session_state['sim_flagged']   = 0
if 'sim_safe'      not in st.session_state: st.session_state['sim_safe']      = 0
if 'sim_alert'     not in st.session_state: st.session_state['sim_alert']     = None
if 'sim_notif'     not in st.session_state: st.session_state['sim_notif']     = None
if 'alert_dismissed' not in st.session_state: st.session_state['alert_dismissed'] = None

def fmt_time(hour):
    h = int(hour)
    suffix = "AM" if h < 12 else "PM"
    display = h % 12
    if display == 0: display = 12
    return f"{display}:00 {suffix}"

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"], .stApp {
    background: #161616 !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stHeader"] { background: transparent !important; }
header, footer { visibility: hidden; }
.block-container {
    padding: 0 !important;
    max-width: 430px !important;
    margin: 0 auto !important;
}
section[data-testid="stSidebar"] { display: none; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #161616 !important;
    border-bottom: 1px solid #2A2A2A !important;
    padding: 0 20px !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #6B7280 !important;
    padding: 14px 24px !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #C6F135 !important;
    border-bottom: 2px solid #C6F135 !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background: #161616 !important;
    padding: 0 !important;
}
.stTabs [data-baseweb="tab-highlight"] { background: transparent !important; }

/* ── Header ── */
.app-header {
    background: #161616;
    padding: 18px 20px 14px;
    display: flex; align-items: center; justify-content: space-between;
}
.app-header-left { display: flex; align-items: center; gap: 12px; }
.app-avatar {
    width: 44px; height: 44px; background: #C6F135;
    border-radius: 14px; display: flex; align-items: center;
    justify-content: center; font-size: 14px; font-weight: 900; color: #161616;
}
.app-greeting { color: #6B7280; font-size: 12px; font-weight: 500; }
.app-name { color: #FFFFFF; font-size: 16px; font-weight: 800; margin-top: 2px; }
.app-header-right { display: flex; align-items: center; gap: 16px; }
.hdr-btn {
    width: 40px; height: 40px; background: #1E1E1E;
    border-radius: 12px; display: flex; align-items: center;
    justify-content: center; position: relative;
}
.hdr-btn svg { width: 20px; height: 20px; fill: #94A3B8; }
.notif-dot {
    width: 8px; height: 8px; background: #FF4444;
    border-radius: 50%; border: 2px solid #161616;
    position: absolute; top: -2px; right: -2px;
}

/* ── Balance Card ── */
.balance-card {
    margin: 6px 16px 0; background: #1E1E1E;
    border-radius: 24px; padding: 24px 22px; border: 1px solid #2A2A2A;
}
.balance-card-top {
    display: flex; justify-content: space-between;
    align-items: flex-start; margin-bottom: 6px;
}
.balance-section-label {
    font-size: 11px; color: #6B7280; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px;
}
.balance-amount {
    font-size: 40px; font-weight: 900; color: #FFFFFF;
    letter-spacing: -2px; line-height: 1; margin-bottom: 8px;
}
.balance-amount span { font-size: 24px; color: #6B7280; font-weight: 500; }
.balance-upi {
    font-size: 12px; color: #4B5563; font-weight: 500;
    display: flex; align-items: center; gap: 6px;
}
.balance-upi-dot { width: 6px; height: 6px; background: #C6F135; border-radius: 50%; }
.shield-badge {
    background: rgba(198,241,53,0.08); border: 1px solid rgba(198,241,53,0.2);
    border-radius: 14px; padding: 10px 14px; text-align: center; min-width: 72px;
}
.shield-badge-text {
    font-size: 10px; color: #C6F135; font-weight: 700;
    letter-spacing: 0.5px; line-height: 1.2;
}
.balance-divider { border: none; border-top: 1px solid #2A2A2A; margin: 20px 0 16px; }
.balance-stats { display: grid; grid-template-columns: 1fr 1fr 1fr; }
.balance-stat { text-align: center; padding: 0 8px; }
.balance-stat:not(:last-child) { border-right: 1px solid #2A2A2A; }
.balance-stat-val { font-size: 16px; font-weight: 800; color: #FFFFFF; margin-bottom: 4px; }
.balance-stat-lbl { font-size: 11px; color: #6B7280; font-weight: 500; }

/* ── Quick Actions ── */
.actions-wrap { margin: 14px 16px 0; }
.actions-label { font-size: 13px; font-weight: 700; color: #FFFFFF; margin-bottom: 12px; padding: 0 4px; }
.actions-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.action-item { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.action-icon-wrap {
    width: 58px; height: 58px; background: #1E1E1E;
    border: 1px solid #2A2A2A; border-radius: 18px;
    display: flex; align-items: center; justify-content: center;
}
.action-icon-wrap svg { width: 24px; height: 24px; fill: #C6F135; }
.action-lbl { font-size: 11px; color: #94A3B8; font-weight: 600; text-align: center; }

/* ── Simulation ── */
.sim-wrap { margin: 14px 16px 0; }
.sim-header {
    display: flex; justify-content: space-between;
    align-items: center; margin-bottom: 12px; padding: 0 4px;
}
.sim-title { font-size: 15px; font-weight: 700; color: #FFFFFF; }
.sim-status { display: flex; align-items: center; gap: 6px; }
.sim-dot { width: 8px; height: 8px; border-radius: 50%; }
.sim-status-text { font-size: 12px; font-weight: 600; }
.sim-stats-row {
    display: grid; grid-template-columns: 1fr 1fr 1fr;
    gap: 8px; margin-bottom: 12px;
}
.sim-stat {
    background: #1E1E1E; border: 1px solid #2A2A2A;
    border-radius: 14px; padding: 12px 10px; text-align: center;
}
.sim-stat-val { font-size: 20px; font-weight: 900; margin-bottom: 3px; }
.sim-stat-lbl {
    font-size: 10px; color: #6B7280; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.5px;
}
.sim-feed {
    background: #1E1E1E; border: 1px solid #2A2A2A;
    border-radius: 20px; padding: 6px 16px; margin-bottom: 0px; min-height: 60px;
}
.sim-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 11px 0; border-bottom: 1px solid #252525;
    animation: fadeIn 0.4s ease;
}
.sim-row:last-child { border-bottom: none; }
.sim-row-left { display: flex; align-items: center; gap: 12px; }
.sim-row-icon {
    width: 38px; height: 38px; border-radius: 11px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0;
}
.sim-row-amount { font-size: 14px; font-weight: 700; color: #FFFFFF; }
.sim-row-time { font-size: 11px; color: #6B7280; margin-top: 2px; }
.sim-badge { font-size: 10px; font-weight: 700; padding: 4px 10px; border-radius: 6px; }
.notif-bar {
    border-radius: 14px; padding: 12px 16px; margin: 0 16px 10px;
    display: flex; align-items: center; gap: 10px;
    animation: slideDown 0.3s ease;
}
.notif-text { font-size: 13px; font-weight: 600; }

@keyframes fadeIn { from{opacity:0;transform:translateY(-6px)} to{opacity:1;transform:translateY(0)} }
@keyframes slideDown { from{opacity:0;transform:translateY(-10px)} to{opacity:1;transform:translateY(0)} }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.2} }

/* ── Alert ── */
.alert-wrap {
    margin: 14px 16px 0; background: #1E1E1E;
    border: 1px solid #3A1A1A; border-radius: 20px; overflow: hidden;
}
.alert-bar {
    background: #E63946; padding: 11px 16px;
    display: flex; align-items: center; gap: 10px;
}
.alert-dot {
    width: 8px; height: 8px; background: white; border-radius: 50%;
    flex-shrink: 0; animation: pulse 1.2s infinite;
}
.alert-bar-text { font-size: 12px; font-weight: 700; color: white; letter-spacing: 0.5px; }
.alert-body { padding: 18px; }
.alert-title { font-size: 17px; font-weight: 800; color: #FFFFFF; margin-bottom: 6px; }
.alert-sub { font-size: 13px; color: #94A3B8; line-height: 1.6; margin-bottom: 16px; }
.alert-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 1px; background: #2A2A2A; border-radius: 14px;
    overflow: hidden; margin-bottom: 18px;
}
.alert-cell { background: #252525; padding: 13px 14px; }
.alert-cell-lbl {
    font-size: 10px; color: #6B7280; font-weight: 700;
    letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;
}
.alert-cell-val { font-size: 16px; font-weight: 800; color: #FFFFFF; }
.alert-cell-val.red { color: #E63946; }
.alert-question { font-size: 14px; color: #FFFFFF; font-weight: 600; margin-bottom: 14px; }

/* ── Buttons ── */
div[data-testid="stButton"] > button,
div[data-testid="stButton"] > button:hover,
div[data-testid="stButton"] > button:focus {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    height: 50px !important;
    width: 100% !important;
    border: none !important;
    border-radius: 14px !important;
    transition: all 0.15s !important;
    background: #C6F135 !important;
    color: #161616 !important;
}

/* ── State Cards ── */
.state-card {
    margin: 14px 16px 0; background: #1E1E1E;
    border: 1px solid #2A2A2A; border-radius: 20px;
    padding: 32px 20px; text-align: center;
}
.state-icon {
    width: 60px; height: 60px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 14px; font-size: 28px;
}
.state-title { font-size: 18px; font-weight: 800; color: #FFFFFF; margin-bottom: 8px; }
.state-sub { font-size: 13px; color: #6B7280; line-height: 1.5; }

/* ── Transactions ── */
.txns-wrap { margin: 14px 16px 0; }
.txns-header {
    display: flex; justify-content: space-between;
    align-items: center; margin-bottom: 12px; padding: 0 4px;
}
.txns-title { font-size: 15px; font-weight: 700; color: #FFFFFF; }
.txns-viewall { font-size: 12px; font-weight: 600; color: #C6F135; }
.txns-card {
    background: #1E1E1E; border: 1px solid #2A2A2A;
    border-radius: 20px; padding: 6px 16px;
}
.txn-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 0; border-bottom: 1px solid #252525;
}
.txn-row:last-child { border-bottom: none; }
.txn-left { display: flex; align-items: center; gap: 14px; }
.txn-icon {
    width: 46px; height: 46px; border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; font-size: 18px;
}
.txn-name { font-size: 14px; font-weight: 700; color: #FFFFFF; }
.txn-time { font-size: 12px; color: #6B7280; font-weight: 500; margin-top: 3px; }
.txn-right { text-align: right; }
.txn-amount { font-size: 15px; font-weight: 800; color: #FFFFFF; }
.txn-badge {
    font-size: 10px; font-weight: 700; padding: 3px 9px;
    border-radius: 6px; margin-top: 4px; display: inline-block;
}

/* ── Security Tab ── */
.sec-wrap { padding: 16px 16px 0; }
.sec-stats { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 14px; }
.sec-stat-card {
    background: #1E1E1E; border: 1px solid #2A2A2A;
    border-radius: 16px; padding: 16px 12px; text-align: center;
}
.sec-stat-val { font-size: 22px; font-weight: 900; margin-bottom: 4px; letter-spacing: -0.5px; }
.sec-stat-lbl {
    font-size: 10px; color: #6B7280; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1px;
}
.sec-section-title { font-size: 15px; font-weight: 700; color: #FFFFFF; margin-bottom: 12px; }
.sec-card {
    background: #1E1E1E; border: 1px solid #2A2A2A;
    border-radius: 20px; padding: 18px; margin-bottom: 14px;
}
.reason-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.reason-pill {
    background: #2A1A1A; border: 1px solid #3A2A2A; color: #E63946;
    border-radius: 10px; padding: 7px 13px; font-size: 12px; font-weight: 600;
}
.blocked-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 13px 0; border-bottom: 1px solid #252525;
}
.blocked-row:last-child { border-bottom: none; }
.blocked-left { display: flex; align-items: center; gap: 12px; }
.blocked-icon {
    width: 44px; height: 44px; background: #2A1A1A; border-radius: 13px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0;
}
.blocked-amount { font-size: 14px; font-weight: 700; color: #FFFFFF; }
.blocked-sub { font-size: 12px; color: #6B7280; margin-top: 3px; font-weight: 500; }
.blocked-right { text-align: right; }
.blocked-badge {
    font-size: 10px; font-weight: 700; background: #2A1A1A;
    color: #E63946; padding: 4px 10px; border-radius: 6px;
}
.blocked-score { font-size: 11px; color: #6B7280; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="app-header-left">
        <div class="app-avatar">WM</div>
        <div>
            <div class="app-greeting">Good morning 👋</div>
            <div class="app-name">Wayne Mautsa</div>
        </div>
    </div>
    <div class="app-header-right">
        <div class="hdr-btn">
            <svg viewBox="0 0 24 24">
                <path d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0 0 16 9.5
                6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79
                l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01
                5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
            </svg>
        </div>
        <div class="hdr-btn" style="position:relative">
            <svg viewBox="0 0 24 24">
                <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5
                c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5
                .67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/>
            </svg>
            <div class="notif-dot"></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Home", "My Security"])

# ═══════════════════════════════════════════════════════════════════
# TAB 1 — HOME
# ═══════════════════════════════════════════════════════════════════
# Initialize the key if it doesn't exist
if "sim_balance" not in st.session_state:
    st.session_state.sim_balance = 43079.76  

with tab1:

    # ── Balance Card ─────────────────────────────────────────────
    s_safe    = st.session_state['sim_safe']
    s_flagged = st.session_state['sim_flagged']
    s_blocked = st.session_state['sim_blocked']
    s_total   = s_safe + s_flagged + s_blocked

    display_total   = s_total   if s_total > 0 else total_txns
    display_safe    = s_safe    if s_total > 0 else safe
    display_blocked = s_blocked if s_total > 0 else blocked

    st.markdown(
        '<div class="balance-card">'
        '<div class="balance-card-top">'
        '<div>'
        '<div class="balance-section-label">Total Balance</div>'
        
        f'<div class="balance-amount">₹{st.session_state["sim_balance"]:,.2f}</div>'
        '<div class="balance-upi">'
        '<div class="balance-upi-dot"></div>'
        'waynemautsa@shield'
        '</div>'
        '</div>'
        '<div class="shield-badge">'
        '<div class="shield-badge-text" style="font-size:22px;margin-bottom:4px">🛡</div>'
        '<div class="shield-badge-text">AI Protected</div>'
        '</div>'
        '</div>'
        '<hr class="balance-divider">'
        '<div class="balance-stats">'
        f'<div class="balance-stat"><div class="balance-stat-val">{display_total:,}</div><div class="balance-stat-lbl">Total</div></div>'
        f'<div class="balance-stat"><div class="balance-stat-val" style="color:#C6F135">{display_safe:,}</div><div class="balance-stat-lbl">Safe</div></div>'
        f'<div class="balance-stat"><div class="balance-stat-val" style="color:#FF4444">{display_blocked:,}</div><div class="balance-stat-lbl">Blocked</div></div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # ── Quick Actions ─────────────────────────────────────────────
    st.markdown("""
    <div class="actions-wrap">
        <div class="actions-label">Quick Actions</div>
        <div class="actions-grid">
            <div class="action-item">
                <div class="action-icon-wrap">
                    <svg viewBox="0 0 24 24"><path d="M4 10v7h3v-7H4zm6 0v7h3v-7h-3zm-5 12h14v-3H5v3zm11-12v7h3v-7h-3zM11.5 1L2 6v2h20V6l-10.5-5z"/></svg>
                </div>
                <div class="action-lbl">Deposit</div>
            </div>
            <div class="action-item">
                <div class="action-icon-wrap">
                    <svg viewBox="0 0 24 24"><path d="M20 10H4v4h16v-4zM4 18h16v-2H4v2zM4 8h16V6H4v2z"/></svg>
                </div>
                <div class="action-lbl">Withdraw</div>
            </div>
            <div class="action-item">
                <div class="action-icon-wrap">
                    <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
                </div>
                <div class="action-lbl">Send</div>
            </div>
            <div class="action-item">
                <div class="action-icon-wrap">
                    <svg viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14H7v-2h5v2zm5-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
                </div>
                <div class="action-lbl">History</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Live Simulation ───────────────────────────────────────────
    st.markdown('<div class="sim-wrap">', unsafe_allow_html=True)

    st.markdown(
        '<div class="sim-header">'
        '<div class="sim-title">Live Transaction Monitor</div>'
        '<div class="sim-status">'
        + (
            '<div class="sim-dot" style="background:#C6F135;animation:pulse 1.2s infinite"></div>'
            '<div class="sim-status-text" style="color:#C6F135">LIVE</div>'
            if st.session_state['sim_running'] else
            '<div class="sim-dot" style="background:#6B7280"></div>'
            '<div class="sim-status-text" style="color:#6B7280">PAUSED</div>'
        ) +
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Sim stats
    st.markdown(
        '<div class="sim-stats-row">'
        f'<div class="sim-stat"><div class="sim-stat-val" style="color:#FFFFFF">{s_total}</div><div class="sim-stat-lbl">Processed</div></div>'
        f'<div class="sim-stat"><div class="sim-stat-val" style="color:#C6F135">{s_safe}</div><div class="sim-stat-lbl">Safe</div></div>'
        f'<div class="sim-stat"><div class="sim-stat-val" style="color:#E63946">{s_blocked}</div><div class="sim-stat-lbl">Blocked</div></div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Start / Stop
    if st.session_state['sim_running']:
        if st.button("⏹  Stop Simulation", key="sim_stop"):
            st.session_state['sim_running'] = False
            st.rerun()
    else:
        if st.button("▶  Start Live Simulation", key="sim_start"):
            st.session_state['sim_running'] = True
            st.rerun()

    # Notification toast for MEDIUM and LOW
    if st.session_state['sim_notif']:
        notif = st.session_state['sim_notif']
        if notif['type'] == 'MEDIUM':
            bar_color = "#2A2210"; text_color = "#F4A261"; icon = "⚠️"
            msg = f"Transaction ₹{notif['amount']:,.2f} flagged for review"
        else:
            bar_color = "#1A2A1A"; text_color = "#C6F135"; icon = "✓"
            msg = f"Transaction ₹{notif['amount']:,.2f} cleared as safe"

        st.markdown(
            f'<div class="notif-bar" style="background:{bar_color};border:1px solid {text_color}55">'
            f'<span style="font-size:18px">{icon}</span>'
            f'<span class="notif-text" style="color:{text_color}">{msg}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    # Live feed
    feed = st.session_state['sim_live']
    if feed:
        feed_html = ""
        for txn in reversed(feed[-5:]):
            if txn['label'] == 'HIGH':
                bg="#2A1A1A"; fg="#E63946"; icon="⛔"; label="Blocked"
            elif txn['label'] == 'MEDIUM':
                bg="#2A2210"; fg="#F4A261"; icon="⚠️"; label="Flagged"
            else:
                bg="#1A2A1A"; fg="#C6F135"; icon="✓"; label="Safe"
            feed_html += (
                '<div class="sim-row">'
                '<div class="sim-row-left">'
                f'<div class="sim-row-icon" style="background:{bg};color:{fg}">{icon}</div>'
                '<div>'
                f'<div class="sim-row-amount">₹{txn["amount"]:,.2f}</div>'
                f'<div class="sim-row-time">{txn["time"]}</div>'
                '</div></div>'
                f'<div class="sim-badge" style="background:{bg};color:{fg}">{label}</div>'
                '</div>'
            )
        st.markdown('<div class="sim-feed">' + feed_html + '</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="sim-feed" style="display:flex;align-items:center;'
            'justify-content:center;padding:20px">'
            '<div style="color:#6B7280;font-size:13px;font-weight:500">'
            'Press Start to begin live monitoring</div></div>',
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # ── HIGH risk sim alert ───────────────────────────────────────
    if st.session_state['sim_alert'] and st.session_state['alert_dismissed'] != 'sim_confirmed':
        alert_txn = st.session_state['sim_alert']
        st.markdown(
            '<div class="alert-wrap">'
            '<div class="alert-bar">'
            '<div class="alert-dot"></div>'
            '<div class="alert-bar-text">LIVE ALERT — Transaction Blocked by AI</div>'
            '</div>'
            '<div class="alert-body">'
            '<div class="alert-title">Suspicious transaction detected</div>'
            '<div class="alert-sub">ATO Shield blocked this transaction in real time.</div>'
            '<div class="alert-grid">'
            f'<div class="alert-cell"><div class="alert-cell-lbl">Amount</div><div class="alert-cell-val">₹{alert_txn["amount"]:,.2f}</div></div>'
            f'<div class="alert-cell"><div class="alert-cell-lbl">Time</div><div class="alert-cell-val">{alert_txn["time"]}</div></div>'
            f'<div class="alert-cell"><div class="alert-cell-lbl">Risk Score</div><div class="alert-cell-val red">{alert_txn["score"]:.0%}</div></div>'
            '<div class="alert-cell"><div class="alert-cell-lbl">Status</div><div class="alert-cell-val red">Blocked</div></div>'
            '</div>'
            '<div class="alert-question">Was this transaction made by you?</div>'
            '</div></div>',
            unsafe_allow_html=True
        )
        ca1, ca2 = st.columns(2)
        with ca1:
            if st.button("Yes, this was me", key="sim_confirm"):
                st.session_state['sim_alert'] = None
                st.session_state['alert_dismissed'] = 'sim_confirmed'
                st.session_state['sim_running'] = True
                st.rerun()
        with ca2:
            if st.button("Block Account", key="sim_block"):
                st.session_state['sim_alert'] = None
                st.session_state['sim_running'] = False
                st.session_state['alert_dismissed'] = 'blocked'
                st.rerun()

    # ── Static alert (before simulation starts) ───────────────────
    elif st.session_state['alert_dismissed'] == 'blocked':
        st.markdown("""
        <div class="state-card">
            <div class="state-icon" style="background:#2A1A1A">🔒</div>
            <div class="state-title" style="color:#E63946">Account Locked</div>
            <div class="state-sub">Your account has been secured.<br>Contact support: 0120-4456-456</div>
        </div>
        """, unsafe_allow_html=True)

    elif st.session_state['alert_dismissed'] == 'sim_confirmed':
        st.markdown("""
        <div class="state-card">
            <div class="state-icon" style="background:#1A2A1A">✅</div>
            <div class="state-title">Transaction Verified</div>
            <div class="state-sub">Flag cleared. Your account is secure and fully protected by ATO Shield.</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Recent Transactions ───────────────────────────────────────
    # If simulation has run, show live feed as transactions
    if st.session_state['sim_live']:
        recent = list(reversed(st.session_state['sim_live'][-6:]))
    else:
        high_s = scores[scores['risk_label'] == 'HIGH'].sample(2, random_state=42)
        med_s  = scores[scores['risk_label'] == 'MEDIUM'].sample(2, random_state=42)
        low_s  = scores[scores['risk_label'] == 'LOW'].sample(2, random_state=42)
        sample = pd.concat([high_s, med_s, low_s]).sample(frac=1, random_state=42)
        recent = []
        for i, row in sample.iterrows():
            recent.append({
                'amount': X['TransactionAmt'].iloc[i],
                'time': fmt_time(X['TransactionHour'].iloc[i]),
                'label': row['risk_label'],
                'score': row['final_score']
            })

    txn_rows = ""
    for txn in recent:
        if txn['label'] == 'HIGH':
            bg="#2A1A1A"; fg="#E63946"; icon="⛔"; label="Blocked"; sign="-"
        elif txn['label'] == 'MEDIUM':
            bg="#2A2210"; fg="#F4A261"; icon="⚠️"; label="Flagged"; sign="-"
        else:
            bg="#1A2A1A"; fg="#C6F135"; icon="✓"; label="Safe"; sign="+"

        txn_rows += (
            '<div class="txn-row">'
            '<div class="txn-left">'
            f'<div class="txn-icon" style="background:{bg};color:{fg}">{icon}</div>'
            '<div>'
            f'<div class="txn-name">₹{txn["amount"]:,.2f}</div>'
            f'<div class="txn-time">{txn["time"]}</div>'
            '</div></div>'
            '<div class="txn-right">'
            f'<div class="txn-amount" style="color:{fg}">{sign}₹{txn["amount"]:,.2f}</div>'
            f'<div class="txn-badge" style="background:{bg};color:{fg}">{label}</div>'
            '</div></div>'
        )

    st.markdown(
        '<div class="txns-wrap">'
        '<div class="txns-header">'
        '<div class="txns-title">Recent Transactions</div>'
        '<div class="txns-viewall">View All</div>'
        '</div>'
        '<div class="txns-card">' + txn_rows + '</div>'
        '</div>'
        '<div style="height:24px"></div>',
        unsafe_allow_html=True
    )

    # ── Simulation Engine ─────────────────────────────────────────
    if st.session_state['sim_running']:
        # Initialize sim balance
        if 'sim_balance' not in st.session_state: st.session_state['sim_balance'] = 47832.00
        # Pick a random transaction each time for variety
        import random
        cycle = st.session_state['sim_index'] % 6

        if cycle == 5:
            # Every 6th transaction is HIGH risk (fraud)
            high_idx = random.choice(high_risk.index.tolist())
            row    = scores.loc[high_idx]
            amount = X['TransactionAmt'].iloc[high_idx]
            hour   = X['TransactionHour'].iloc[high_idx]
        elif cycle in [1, 3]:
            # 2 out of 6 are MEDIUM
            med     = scores[scores['risk_label'] == 'MEDIUM']
            med_idx = random.choice(med.index.tolist())
            row    = scores.loc[med_idx]
            amount = X['TransactionAmt'].iloc[med_idx]
            hour   = X['TransactionHour'].iloc[med_idx]
        else:
            # Rest are LOW (safe)
            low     = scores[scores['risk_label'] == 'LOW']
            low_idx = random.choice(low.index.tolist())
            row    = scores.loc[low_idx]
            amount = X['TransactionAmt'].iloc[low_idx]
            hour   = X['TransactionHour'].iloc[low_idx]

        label  = row['risk_label']
        score  = row['final_score']
        tstr   = fmt_time(hour)

        if label == 'HIGH':
            st.session_state['sim_blocked'] += 1
            st.session_state['sim_alert']   = {'amount': amount, 'time': tstr, 'score': score, 'label': label}
            st.session_state['sim_notif']   = None
            # Balance unchanged — transaction blocked
        elif label == 'MEDIUM':
            st.session_state['sim_flagged'] += 1
            st.session_state['sim_alert']   = None
            st.session_state['sim_notif']   = {'type': 'MEDIUM', 'amount': amount}
            # MEDIUM still goes through — deducted
            st.session_state['sim_balance'] -= amount
        else:
            st.session_state['sim_safe']    += 1
            st.session_state['sim_alert']   = None
            st.session_state['sim_notif']   = {'type': 'LOW', 'amount': amount}
            # Safe transaction — deducted from balance
            st.session_state['sim_balance'] -= amount
        st.session_state['sim_live'].append({'amount': amount, 'time': tstr, 'label': label, 'score': score})
        if len(st.session_state['sim_live']) > 20:
            st.session_state['sim_live'].pop(0)

        st.session_state['sim_index'] += 1

        if label == 'HIGH':
            # Pause simulation — wait for human to respond
            st.session_state['sim_running'] = False
        else:
            time.sleep(3)
            st.rerun()

# ═══════════════════════════════════════════════════════════════════
# TAB 2 — MY SECURITY
# ═══════════════════════════════════════════════════════════════════
with tab2:

    # Use sim counts if simulation has run, else use CSV counts
    disp_total   = s_total   if s_total > 0 else total_txns
    disp_safe    = s_safe    if s_total > 0 else safe
    disp_blocked = s_blocked if s_total > 0 else blocked
    disp_flagged = s_flagged if s_total > 0 else flagged

    st.markdown("<div class='sec-wrap'>", unsafe_allow_html=True)

    # Stats
    st.markdown(
        '<div class="sec-stats">'
        f'<div class="sec-stat-card"><div class="sec-stat-val" style="color:#FFFFFF">{disp_total:,}</div><div class="sec-stat-lbl">Total</div></div>'
        f'<div class="sec-stat-card"><div class="sec-stat-val" style="color:#C6F135">{disp_safe:,}</div><div class="sec-stat-lbl">Safe</div></div>'
        f'<div class="sec-stat-card"><div class="sec-stat-val" style="color:#E63946">{disp_blocked:,}</div><div class="sec-stat-lbl">Blocked</div></div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Donut chart
    st.markdown('<div class="sec-card"><div class="sec-section-title">Risk Breakdown</div></div>', unsafe_allow_html=True)

    fig = go.Figure(data=[go.Pie(
        labels=['Safe', 'Flagged', 'Blocked'],
        values=[disp_safe, disp_flagged, disp_blocked],
        hole=0.65,
        marker_colors=['#C6F135', '#F4A261', '#E63946'],
        textinfo='percent',
        textfont=dict(size=12, color='white', family='Inter'),
        hovertemplate='%{label}: %{value:,}<extra></extra>',
        showlegend=True
    )])
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5,
                    font=dict(size=12, color='#94A3B8', family='Inter')),
        margin=dict(t=0, b=40, l=0, r=0), height=220,
        paper_bgcolor='#1E1E1E', plot_bgcolor='#1E1E1E',
        annotations=[dict(text=f'<b>{disp_total:,}</b>', x=0.5, y=0.5,
                          font=dict(size=14, color='#FFFFFF', family='Inter'), showarrow=False)]
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # Why blocked
    st.markdown(
        '<div class="sec-card">'
        '<div class="sec-section-title">Why Transactions Were Blocked</div>'
        '<div class="reason-grid">'
        '<div class="reason-pill">Night activity</div>'
        '<div class="reason-pill">Unusual amount</div>'
        '<div class="reason-pill">New device</div>'
        '<div class="reason-pill">High velocity</div>'
        '<div class="reason-pill">New location</div>'
        '<div class="reason-pill">New email</div>'
        '</div></div>',
        unsafe_allow_html=True
    )

    # Blocked transactions — use sim feed if available else CSV
    if st.session_state['sim_live']:
        sim_blocked_txns = [t for t in st.session_state['sim_live'] if t['label'] == 'HIGH'][-6:]
        blocked_rows = ""
        for txn in reversed(sim_blocked_txns):
            reason = "Night activity" if any(h in txn['time'] for h in ['12:00 AM','1:00 AM','2:00 AM','3:00 AM','4:00 AM','5:00 AM','11:00 PM','10:00 PM']) else "Unusual pattern"
            blocked_rows += (
                '<div class="blocked-row"><div class="blocked-left">'
                '<div class="blocked-icon">⛔</div><div>'
                f'<div class="blocked-amount">₹{txn["amount"]:,.2f}</div>'
                f'<div class="blocked-sub">{txn["time"]} · {reason}</div>'
                '</div></div><div class="blocked-right">'
                '<div class="blocked-badge">BLOCKED</div>'
                f'<div class="blocked-score">{txn["score"]:.0%} risk</div>'
                '</div></div>'
            )
        if not blocked_rows:
            blocked_rows = '<div style="padding:16px 0;color:#6B7280;font-size:13px;text-align:center">No blocked transactions yet</div>'
    else:
        blocked_sample = high_risk.sample(min(6, len(high_risk)), random_state=42)
        blocked_rows = ""
        for i, row in blocked_sample.iterrows():
            amount = X['TransactionAmt'].iloc[i]
            hour   = X['TransactionHour'].iloc[i]
            tstr   = fmt_time(hour)
            reason = "Night activity" if int(hour) < 6 or int(hour) > 22 else "Unusual pattern"
            blocked_rows += (
                '<div class="blocked-row"><div class="blocked-left">'
                '<div class="blocked-icon">⛔</div><div>'
                f'<div class="blocked-amount">₹{amount:,.2f}</div>'
                f'<div class="blocked-sub">{tstr} · {reason}</div>'
                '</div></div><div class="blocked-right">'
                '<div class="blocked-badge">BLOCKED</div>'
                f'<div class="blocked-score">{row["final_score"]:.0%} risk</div>'
                '</div></div>'
            )

    st.markdown('<div class="sec-card"><div class="sec-section-title">Blocked Transactions</div>' + blocked_rows + '</div>', unsafe_allow_html=True)

    # Bar chart
    st.markdown('<div class="sec-card"><div class="sec-section-title">Suspicious Activity by Hour</div></div>', unsafe_allow_html=True)

    high_hours = X.iloc[high_risk.index]['TransactionHour'].value_counts().sort_index()
    fig2 = go.Figure(data=[go.Bar(
        x=high_hours.index, y=high_hours.values,
        marker_color='#E63946', marker_opacity=0.85,
        hovertemplate='%{x}:00 — %{y} blocked<extra></extra>'
    )])
    fig2.update_layout(
        margin=dict(t=0, b=0, l=0, r=0), height=200,
        paper_bgcolor='#1E1E1E', plot_bgcolor='#1E1E1E',
        xaxis=dict(title='Hour', tickfont=dict(size=11, color='#6B7280'), gridcolor='#2A2A2A', title_font=dict(size=12, color='#6B7280')),
        yaxis=dict(title='Blocked', tickfont=dict(size=11, color='#6B7280'), gridcolor='#2A2A2A', title_font=dict(size=12, color='#6B7280')),
        bargap=0.3
    )
    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)
