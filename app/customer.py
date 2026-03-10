import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Paytm", page_icon="💙", layout="centered")

@st.cache_data
def load_data():
    scores = pd.read_csv("data/processed/risk_scores.csv")
    X = pd.read_csv("data/processed/X_test.csv")
    return scores, X

scores, X = load_data()

st.markdown("""
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    .stApp {
        background: #F2F2F7;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        max-width: 430px;
        margin: 0 auto;
    }

    header { visibility: hidden; }
    footer { visibility: hidden; }
    .block-container { padding: 0 !important; }

    /* ── Header ── */
    .ptm-header {
        background: linear-gradient(180deg, #00BAF2 0%, #0099CC 100%);
        padding: 14px 20px 18px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .ptm-logo {
        font-size: 22px;
        font-weight: 900;
        color: white;
        letter-spacing: -0.5px;
    }
    .ptm-logo b { color: #002970; }
    .ptm-avatar {
        width: 36px; height: 36px;
        background: #FFB800;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 13px; font-weight: 800; color: white;
    }
    .ptm-icons { display: flex; gap: 16px; }
    .ptm-icons svg { width: 22px; height: 22px; fill: white; }

    /* ── Cards ── */
    .ptm-card {
        background: white;
        border-radius: 16px;
        padding: 18px;
        margin: 10px 12px 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    .ptm-card-title {
        font-size: 15px;
        font-weight: 700;
        color: #000000;
        margin-bottom: 14px;
    }

    /* ── Balance ── */
    .ptm-balance-label {
        font-size: 12px;
        color: #555555;
        margin-bottom: 4px;
        font-weight: 500;
    }
    .ptm-balance {
        font-size: 34px;
        font-weight: 800;
        color: #1A1F71;
        letter-spacing: -1px;
    }
    .ptm-balance span {
        font-size: 18px;
        color: #888888;
    }
    .ptm-upi {
        font-size: 12px;
        color: #555555;
        margin-top: 4px;
    }
    .ptm-shield {
        background: #F0FAF0;
        border-radius: 10px;
        padding: 10px 14px;
        text-align: center;
        border: 1px solid #C8F0D0;
    }
    .ptm-shield-label {
        font-size: 10px;
        color: #007AFF;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .ptm-shield-status {
        font-size: 12px;
        color: #1A8C3A;
        font-weight: 700;
        margin-top: 2px;
    }

    /* ── Quick actions ── */
    .ptm-actions {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 4px;
        text-align: center;
    }
    .ptm-action-icon {
        width: 52px; height: 52px;
        background: #EEF6FF;
        border-radius: 14px;
        margin: 0 auto 6px;
        display: flex; align-items: center; justify-content: center;
    }
    .ptm-action-icon svg {
        width: 24px; height: 24px;
        fill: #0088CC;
    }
    .ptm-action-label {
        font-size: 11px;
        color: #222222;
        line-height: 1.3;
        font-weight: 500;
    }

    /* ── Alert ── */
    .ptm-alert {
        background: white;
        border-radius: 16px;
        margin: 10px 12px 0;
        overflow: hidden;
        box-shadow: 0 2px 12px rgba(255,59,48,0.15);
    }
    .ptm-alert-bar {
        background: #FF3B30;
        padding: 10px 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .ptm-alert-bar-dot {
        width: 8px; height: 8px;
        background: white;
        border-radius: 50%;
        animation: blink 1s infinite;
        flex-shrink: 0;
    }
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    .ptm-alert-bar-text {
        font-size: 12px;
        font-weight: 700;
        color: white;
        letter-spacing: 0.5px;
    }
    .ptm-alert-body { padding: 16px; }
    .ptm-alert-title {
        font-size: 16px;
        font-weight: 700;
        color: #000000;
        margin-bottom: 4px;
    }
    .ptm-alert-sub {
        font-size: 13px;
        color: #444444;
        margin-bottom: 14px;
        line-height: 1.5;
    }
    .ptm-alert-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        background: #F8F8FF;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 14px;
        border: 1px solid #E8E8F0;
    }
    .ptm-alert-field-label {
        font-size: 11px;
        color: #555555;
        margin-bottom: 3px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }
    .ptm-alert-field-value {
        font-size: 15px;
        font-weight: 700;
        color: #000000;
    }
    .ptm-alert-field-value.red { color: #CC0000; }
    .ptm-alert-question {
        font-size: 13px;
        color: #333333;
        margin-bottom: 14px;
        font-weight: 500;
    }

    /* ── Buttons ── */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        padding: 12px !important;
        border: none !important;
        width: 100% !important;
    }

    /* ── Transactions ── */
    .ptm-txn {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid #EEEEEE;
    }
    .ptm-txn:last-child { border-bottom: none; }
    .ptm-txn-icon {
        width: 42px; height: 42px;
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        margin-right: 12px;
        flex-shrink: 0;
    }
    .ptm-txn-amount {
        font-size: 15px;
        font-weight: 700;
        color: #000000;
    }
    .ptm-txn-time {
        font-size: 12px;
        color: #555555;
        margin-top: 2px;
        font-weight: 500;
    }
    .ptm-badge {
        font-size: 11px;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 6px;
    }

    /* ── Bottom nav ── */
    .ptm-nav {
        position: fixed;
        bottom: 0; left: 0; right: 0;
        background: white;
        border-top: 1px solid #DDDDDD;
        display: flex;
        justify-content: space-around;
        padding: 10px 0 14px;
        z-index: 999;
    }
    .ptm-nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 3px;
    }
    .ptm-nav-item svg { width: 22px; height: 22px; }
    .ptm-nav-label {
        font-size: 10px;
        color: #555555;
        font-weight: 500;
    }
    .ptm-nav-label.active {
        color: #00BAF2;
        font-weight: 700;
    }
    .ptm-spacer { height: 80px; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ptm-header">
    <div class="ptm-avatar">WM</div>
    <div class="ptm-logo">pay<b>tm</b></div>
    <div class="ptm-icons">
        <svg viewBox="0 0 24 24">
            <path d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0 0 16 9.5 
            6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 
            4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 
            5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
        </svg>
        <svg viewBox="0 0 24 24">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
        </svg>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Balance Card ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="ptm-card">
    <div style="display:flex; justify-content:space-between; align-items:flex-start">
        <div>
            <div class="ptm-balance-label">Paytm Wallet</div>
            <div class="ptm-balance">₹47,832<span>.00</span></div>
            <div class="ptm-upi">waynemautsa@paytm</div>
        </div>
        <div class="ptm-shield">
            <div class="ptm-shield-label">AI SHIELD</div>
            <div class="ptm-shield-status">Active</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Send Money ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ptm-card">
    <div class="ptm-card-title">Send Money</div>
    <div class="ptm-actions">
        <div>
            <div class="ptm-action-icon">
                <svg viewBox="0 0 24 24">
                    <path d="M9.5 6.5v3h-3v2h3v3h2v-3h3v-2h-3v-3h-2zM11 
                    1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-8-4z"/>
                </svg>
            </div>
            <div class="ptm-action-label">Scan &amp; Pay</div>
        </div>
        <div>
            <div class="ptm-action-icon">
                <svg viewBox="0 0 24 24">
                    <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 
                    0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 
                    5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 
                    3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 
                    1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
                </svg>
            </div>
            <div class="ptm-action-label">To Mobile</div>
        </div>
        <div>
            <div class="ptm-action-icon">
                <svg viewBox="0 0 24 24">
                    <path d="M4 10v7h3v-7H4zm6 0v7h3v-7h-3zm-5 12h14v-3H5v3zm11-12v7h3v-7h-3z
                    M11.5 1L2 6v2h20V6l-10.5-5z"/>
                </svg>
            </div>
            <div class="ptm-action-label">To Bank A/c</div>
        </div>
        <div>
            <div class="ptm-action-icon">
                <svg viewBox="0 0 24 24">
                    <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 
                    2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14H7v-2h5v2zm5-4H7v-2h10v2zm0-4H7V7h10v2z"/>
                </svg>
            </div>
            <div class="ptm-action-label">Passbook</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Fraud Alert ───────────────────────────────────────────────────────────────
high_risk = scores[scores['risk_label'] == 'HIGH'].head(1)

if not high_risk.empty and 'alert_dismissed' not in st.session_state:
    txn = high_risk.iloc[0]
    txn_amount = X.iloc[high_risk.index[0]]['TransactionAmt']
    txn_hour = int(X.iloc[high_risk.index[0]]['TransactionHour'])
    time_str = f"{txn_hour:02d}:00 {'AM' if txn_hour < 12 else 'PM'}"

    st.markdown(f"""
    <div class="ptm-alert">
        <div class="ptm-alert-bar">
            <div class="ptm-alert-bar-dot"></div>
            <div class="ptm-alert-bar-text">SECURITY ALERT — Transaction Blocked</div>
        </div>
        <div class="ptm-alert-body">
            <div class="ptm-alert-title">Suspicious transaction detected</div>
            <div class="ptm-alert-sub">
                ATO Shield blocked a transaction that did not match 
                your usual activity pattern.
            </div>
            <div class="ptm-alert-grid">
                <div>
                    <div class="ptm-alert-field-label">Amount</div>
                    <div class="ptm-alert-field-value">₹{txn_amount:,.2f}</div>
                </div>
                <div>
                    <div class="ptm-alert-field-label">Time</div>
                    <div class="ptm-alert-field-value">{time_str}</div>
                </div>
                <div>
                    <div class="ptm-alert-field-label">Risk Score</div>
                    <div class="ptm-alert-field-value red">{txn['final_score']:.0%}</div>
                </div>
                <div>
                    <div class="ptm-alert-field-label">Status</div>
                    <div class="ptm-alert-field-value red">Blocked</div>
                </div>
            </div>
            <div class="ptm-alert-question">Was this transaction made by you?</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, this was me", key="confirm"):
            st.session_state['alert_dismissed'] = 'confirmed'
            st.rerun()
    with col2:
        if st.button("Block My Account", key="block"):
            st.session_state['alert_dismissed'] = 'blocked'
            st.rerun()

elif st.session_state.get('alert_dismissed') == 'confirmed':
    st.markdown("""
    <div class="ptm-card" style="text-align:center; padding:28px 18px">
        <div style="width:52px; height:52px; background:#E8FAF0; border-radius:50%;
                    display:flex; align-items:center; justify-content:center;
                    margin:0 auto 12px">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="#1A8C3A">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
            </svg>
        </div>
        <div style="font-weight:700; color:#000000; font-size:16px; margin-bottom:6px">
            Transaction Verified
        </div>
        <div style="font-size:13px; color:#444444">
            Flag cleared. Your account is secure.
        </div>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.get('alert_dismissed') == 'blocked':
    st.markdown("""
    <div class="ptm-card" style="text-align:center; padding:28px 18px">
        <div style="width:52px; height:52px; background:#FFF0EE; border-radius:50%;
                    display:flex; align-items:center; justify-content:center;
                    margin:0 auto 12px">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="#CC0000">
                <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 
                .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 
                9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 
                1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/>
            </svg>
        </div>
        <div style="font-weight:700; color:#CC0000; font-size:16px; margin-bottom:6px">
            Account Locked
        </div>
        <div style="font-size:13px; color:#444444">
            Contact Paytm support: 0120-4456-456
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Recent Transactions ───────────────────────────────────────────────────────
st.markdown("""
<div class="ptm-card">
    <div class="ptm-card-title">Recent Transactions</div>
""", unsafe_allow_html=True)

recent = scores.head(6)
for i, row in recent.iterrows():
    amount = X.iloc[i]['TransactionAmt']
    hour = int(X.iloc[i]['TransactionHour'])
    time_str = f"{hour:02d}:00 {'AM' if hour < 12 else 'PM'}"

    if row['risk_label'] == 'HIGH':
        color = "#CC0000"; bg = "#FFF0EE"
    elif row['risk_label'] == 'MEDIUM':
        color = "#CC6600"; bg = "#FFF4E8"
    else:
        color = "#1A8C3A"; bg = "#E8FAF0"

    st.markdown(f"""
    <div class="ptm-txn">
        <div style="display:flex; align-items:center">
            <div class="ptm-txn-icon" style="background:{bg}">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="{color}">
                    <path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 
                    2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16
                    c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 
                    2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2
                    c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 
                    0-2.84-2.43-3.81-4.7-4.4z"/>
                </svg>
            </div>
            <div>
                <div class="ptm-txn-amount">₹{amount:,.2f}</div>
                <div class="ptm-txn-time">{time_str}</div>
            </div>
        </div>
        <div class="ptm-badge" style="background:{bg}; color:{color}">
            {row['risk_label']}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ── Bottom Nav ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ptm-nav">
    <div class="ptm-nav-item">
        <svg viewBox="0 0 24 24" fill="#00BAF2">
            <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
        </svg>
        <div class="ptm-nav-label active">Home</div>
    </div>
    <div class="ptm-nav-item">
        <svg viewBox="0 0 24 24" fill="#555555">
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 
            2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14H7v-2h5v2zm5-4H7v-2h10v2zm0-4H7V7h10v2z"/>
        </svg>
        <div class="ptm-nav-label">Passbook</div>
    </div>
    <div class="ptm-nav-item">
        <svg viewBox="0 0 24 24" fill="#555555">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 
            10-10S17.52 2 12 2zm5 11h-4v4h-2v-4H7v-2h4V7h2v4h4v2z"/>
        </svg>
        <div class="ptm-nav-label">Pay</div>
    </div>
    <div class="ptm-nav-item">
        <svg viewBox="0 0 24 24" fill="#555555">
            <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07
            -1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 
            1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/>
        </svg>
        <div class="ptm-nav-label">Alerts</div>
    </div>
    <div class="ptm-nav-item">
        <svg viewBox="0 0 24 24" fill="#555555">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 
            4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
        </svg>
        <div class="ptm-nav-label">Profile</div>
    </div>
</div>
<div class="ptm-spacer"></div>
""", unsafe_allow_html=True)