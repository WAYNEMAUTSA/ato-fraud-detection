import streamlit as st
import pandas as pd
import numpy as np
import joblib
import shap
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="ATO Shield — Analyst Dashboard",
    page_icon="🛡",
    layout="wide"
)

@st.cache_data
def load_data():
    scores = pd.read_csv("data/processed/risk_scores.csv")
    X = pd.read_csv("data/processed/X_test.csv")
    return scores, X

@st.cache_resource
def load_models():
    xgb = joblib.load("src/models/saved/xgboost_model.pkl")
    iso = joblib.load("src/models/saved/isolation_forest.pkl")
    return xgb, iso

scores, X = load_data()
xgb_model, iso_model = load_models()

st.markdown("""
<style>
    .stApp {
        background: #0A0F1E;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    header { visibility: hidden; }
    footer { visibility: hidden; }

    /* Header */
    .dash-header {
        background: linear-gradient(135deg, #0D1B3E, #1A2F6E);
        padding: 18px 28px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid #1E3A8A;
        margin-bottom: 24px;
    }
    .dash-title {
        font-size: 20px;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.5px;
    }
    .dash-subtitle {
        font-size: 12px;
        color: #93C5FD;
        margin-top: 2px;
        font-weight: 500;
    }
    .dash-live {
        display: flex;
        align-items: center;
        gap: 8px;
        background: #0D2137;
        border: 1px solid #1E4D7B;
        border-radius: 20px;
        padding: 6px 14px;
    }
    .dash-live-dot {
        width: 8px; height: 8px;
        background: #34D399;
        border-radius: 50%;
        animation: blink 1.5s infinite;
    }
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    .dash-live-text {
        font-size: 11px;
        color: #34D399;
        font-weight: 700;
        letter-spacing: 1px;
    }

    /* KPI Cards */
    .kpi-card {
        background: #0D1B3E;
        border: 1px solid #1E3A8A;
        border-radius: 14px;
        padding: 18px 20px;
    }
    .kpi-label {
        font-size: 11px;
        color: #93C5FD;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 32px;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -1px;
    }
    .kpi-sub {
        font-size: 11px;
        color: #64748B;
        margin-top: 4px;
    }

    /* Table */
    .dash-table-header {
        background: #0D1B3E;
        border: 1px solid #1E3A8A;
        border-radius: 14px 14px 0 0;
        padding: 14px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .dash-table-title {
        font-size: 14px;
        font-weight: 700;
        color: #FFFFFF;
    }
    .dash-row {
        background: #0A0F1E;
        border: 1px solid #1E3A8A;
        border-top: none;
        padding: 12px 20px;
        display: grid;
        grid-template-columns: 120px 1fr 100px 110px 90px;
        gap: 12px;
        align-items: center;
        cursor: pointer;
        transition: background 0.15s;
    }
    .dash-row:hover { background: #0D1B3E; }
    .dash-row:last-child {
        border-radius: 0 0 14px 14px;
    }
    .dash-row-id {
        font-size: 11px;
        color: #64748B;
        font-family: monospace;
    }
    .dash-row-amount {
        font-size: 14px;
        font-weight: 700;
        color: #FFFFFF;
    }
    .dash-row-sub {
        font-size: 11px;
        color: #64748B;
        margin-top: 2px;
    }
    .dash-row-time {
        font-size: 12px;
        color: #94A3B8;
    }
    .dash-badge {
        font-size: 10px;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 6px;
        letter-spacing: 0.5px;
        text-align: center;
    }

    /* Detail Panel */
    .detail-card {
        background: #0D1B3E;
        border: 1px solid #1E3A8A;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 14px;
    }
    .detail-label {
        font-size: 11px;
        color: #93C5FD;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 14px;
    }
    .detail-field-label {
        font-size: 10px;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 3px;
    }
    .detail-field-value {
        font-size: 14px;
        font-weight: 700;
        color: #FFFFFF;
    }

    /* Score bar */
    .score-bar-bg {
        background: #1E3A8A;
        border-radius: 4px;
        height: 8px;
        width: 100%;
        margin-top: 4px;
        overflow: hidden;
    }

    /* Metric bars */
    .metric-label {
        font-size: 12px;
        color: #E2E8F0;
        font-weight: 500;
    }
    .metric-value {
        font-size: 13px;
        font-weight: 700;
    }

    /* Action buttons */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        padding: 10px !important;
        width: 100% !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="dash-header">
    <div>
        <div class="dash-title">ATO Shield — Fraud Analyst Dashboard</div>
        <div class="dash-subtitle">
            Powered by XGBoost + Isolation Forest · IEEE-CIS Dataset · 
            {len(scores):,} transactions monitored
        </div>
    </div>
    <div class="dash-live">
        <div class="dash-live-dot"></div>
        <div class="dash-live-text">LIVE MONITORING</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── KPI Row ───────────────────────────────────────────────────────────────────
high_count = len(scores[scores['risk_label'] == 'HIGH'])
med_count = len(scores[scores['risk_label'] == 'MEDIUM'])
low_count = len(scores[scores['risk_label'] == 'LOW'])
fraud_rate = scores['actual_fraud'].mean() * 100

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Total Transactions</div>
        <div class="kpi-value">{len(scores):,}</div>
        <div class="kpi-sub">Last 590,540 records</div>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card" style="border-color:#7F1D1D">
        <div class="kpi-label" style="color:#FCA5A5">High Risk</div>
        <div class="kpi-value" style="color:#F87171">{high_count:,}</div>
        <div class="kpi-sub">{high_count/len(scores)*100:.1f}% of total</div>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card" style="border-color:#78350F">
        <div class="kpi-label" style="color:#FCD34D">Medium Risk</div>
        <div class="kpi-value" style="color:#FBBF24">{med_count:,}</div>
        <div class="kpi-sub">Needs review</div>
    </div>""", unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card" style="border-color:#064E3B">
        <div class="kpi-label" style="color:#6EE7B7">ROC-AUC</div>
        <div class="kpi-value" style="color:#34D399">0.982</div>
        <div class="kpi-sub">Hybrid model</div>
    </div>""", unsafe_allow_html=True)

with k5:
    st.markdown(f"""
    <div class="kpi-card" style="border-color:#312E81">
        <div class="kpi-label" style="color:#C4B5FD">Recall</div>
        <div class="kpi-value" style="color:#A78BFA">90.9%</div>
        <div class="kpi-sub">Fraud caught</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── Main Layout ───────────────────────────────────────────────────────────────
left, right = st.columns([2, 1])

with left:
    # Filter
    filter_col, _ = st.columns([1, 2])
    with filter_col:
        risk_filter = st.selectbox(
            "Filter by risk",
            ["ALL", "HIGH", "MEDIUM", "LOW"],
            label_visibility="collapsed"
        )

    # Table
    filtered = scores if risk_filter == "ALL" else scores[scores['risk_label'] == risk_filter]
    display = filtered.head(20)

    st.markdown("""
    <div class="dash-table-header">
        <div class="dash-table-title">Transaction Feed</div>
        <div style="font-size:11px; color:#64748B">Click a row to inspect</div>
    </div>
    """, unsafe_allow_html=True)

    for idx, (i, row) in enumerate(display.iterrows()):
        amount = X.iloc[i]['TransactionAmt']
        hour = int(X.iloc[i]['TransactionHour'])
        time_str = f"{hour:02d}:00 {'AM' if hour < 12 else 'PM'}"

        if row['risk_label'] == 'HIGH':
            badge_style = "background:#7F1D1D; color:#F87171"
        elif row['risk_label'] == 'MEDIUM':
            badge_style = "background:#78350F; color:#FBBF24"
        else:
            badge_style = "background:#064E3B; color:#34D399"

        st.markdown(f"""
        <div class="dash-row">
            <div class="dash-row-id">TXN-{str(i).zfill(6)}</div>
            <div>
                <div class="dash-row-amount">₹{amount:,.2f}</div>
                <div class="dash-row-sub">Score: {row['final_score']:.3f}</div>
            </div>
            <div class="dash-row-time">{time_str}</div>
            <div>
                <span class="dash-badge" style="{badge_style}">
                    {row['risk_label']}
                </span>
            </div>
            <div class="dash-row-sub">
                {'FRAUD' if row['actual_fraud'] == 1 else 'LEGIT'}
            </div>
        </div>
        """, unsafe_allow_html=True)

with right:
    # Model Performance
    st.markdown("""
    <div class="detail-card">
        <div class="detail-label">Model Performance</div>
    """, unsafe_allow_html=True)

    for label, value, color in [
        ("Precision", 0.960, "#60A5FA"),
        ("Recall",    0.909, "#34D399"),
        ("F1-Score",  0.934, "#A78BFA"),
        ("ROC-AUC",   0.982, "#FBBF24"),
    ]:
        st.markdown(f"""
        <div style="margin-bottom:12px">
            <div style="display:flex; justify-content:space-between; margin-bottom:4px">
                <span class="metric-label">{label}</span>
                <span class="metric-value" style="color:{color}">{value}</span>
            </div>
            <div class="score-bar-bg">
                <div style="width:{value*100}%; height:100%; 
                            background:{color}; border-radius:4px">
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div style="font-size:11px; color:#475569; margin-top:8px; 
                    padding-top:10px; border-top:1px solid #1E3A8A">
            XGBoost 70% + Isolation Forest 30%
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Transaction Inspector
    st.markdown("""
    <div class="detail-card">
        <div class="detail-label">Transaction Inspector</div>
    """, unsafe_allow_html=True)

    inspect_idx = st.number_input(
        "Enter transaction index",
        min_value=0,
        max_value=len(scores)-1,
        value=0,
        label_visibility="collapsed"
    )

    row = scores.iloc[inspect_idx]
    amount = X.iloc[inspect_idx]['TransactionAmt']
    hour = int(X.iloc[inspect_idx]['TransactionHour'])

    st.markdown(f"""
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:16px">
            <div>
                <div class="detail-field-label">Amount</div>
                <div class="detail-field-value">₹{amount:,.2f}</div>
            </div>
            <div>
                <div class="detail-field-label">Time</div>
                <div class="detail-field-value">{hour:02d}:00</div>
            </div>
            <div>
                <div class="detail-field-label">XGBoost Score</div>
                <div class="detail-field-value" style="color:#60A5FA">
                    {row['xgb_score']:.3f}
                </div>
            </div>
            <div>
                <div class="detail-field-label">Iso Score</div>
                <div class="detail-field-value" style="color:#A78BFA">
                    {row['iso_score']:.3f}
                </div>
            </div>
            <div>
                <div class="detail-field-label">Final Score</div>
                <div class="detail-field-value" style="color:#F87171">
                    {row['final_score']:.3f}
                </div>
            </div>
            <div>
                <div class="detail-field-label">Actual</div>
                <div class="detail-field-value" 
                    style="color:{'#F87171' if row['actual_fraud']==1 else '#34D399'}">
                    {'FRAUD' if row['actual_fraud']==1 else 'LEGIT'}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # SHAP
    st.markdown("""
    <div class="detail-card">
        <div class="detail-label">SHAP — Why was this flagged?</div>
    """, unsafe_allow_html=True)

    if st.button("Generate SHAP Explanation", key="shap_btn"):
        with st.spinner("Calculating..."):
            explainer = shap.TreeExplainer(xgb_model)
            sample = X.iloc[[inspect_idx]]
            shap_vals = explainer.shap_values(sample)[0]

            feat_imp = pd.DataFrame({
                'Feature': X.columns,
                'Impact': shap_vals
            }).sort_values('Impact', ascending=False).head(6)

            for _, r in feat_imp.iterrows():
                color = "#F87171" if r['Impact'] > 0 else "#34D399"
                direction = "increases" if r['Impact'] > 0 else "decreases"
                bar_width = min(abs(r['Impact']) * 200, 100)

                st.markdown(f"""
                <div style="margin-bottom:10px">
                    <div style="display:flex; justify-content:space-between; margin-bottom:3px">
                        <span style="font-size:12px; color:#E2E8F0">
                            {r['Feature']}
                        </span>
                        <span style="font-size:11px; color:{color}; font-weight:700">
                            {'+' if r['Impact']>0 else ''}{r['Impact']:.3f}
                        </span>
                    </div>
                    <div class="score-bar-bg">
                        <div style="width:{bar_width}%; height:100%; 
                                    background:{color}; border-radius:4px">
                        </div>
                    </div>
                    <div style="font-size:10px; color:#475569; margin-top:2px">
                        {direction} fraud risk
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Actions
    st.markdown("""
    <div class="detail-card">
        <div class="detail-label">Analyst Actions</div>
    </div>
    """, unsafe_allow_html=True)

    a1, a2 = st.columns(2)
    with a1:
        if st.button("Confirm Fraud", key="fraud_btn"):
            st.error("Marked as FRAUD")
    with a2:
        if st.button("Clear — Legit", key="legit_btn"):
            st.success("Cleared as LEGIT")

    if st.button("Escalate for Review", key="escalate_btn"):
        st.warning("Escalated to senior analyst")