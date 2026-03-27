"""
FraudOps — Institutional Fraud Operations Centre
A realistic, analyst-grade fraud detection dashboard.
"""

import random
import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from collections import Counter, deque

st.set_page_config(
    page_title="FraudOps · Institutional Fraud Operations",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    s = pd.read_csv("data/processed/risk_scores.csv")
    X = pd.read_csv("data/processed/X_test.csv")
    return s, X

@st.cache_data
def build_pools(scores):
    return {
        "HIGH":   scores[scores["risk_label"] == "HIGH"].index.tolist(),
        "MEDIUM": scores[scores["risk_label"] == "MEDIUM"].index.tolist(),
        "LOW":    scores[scores["risk_label"] == "LOW"].index.tolist(),
    }

scores, X = load_data()
POOLS = build_pools(scores)

# ─────────────────────────────────────────────
# CONSTANTS & LOOKUPS
# ─────────────────────────────────────────────
FRAUD_TYPES = {
    "ATO": "Account Takeover",
    "VEL": "Velocity Fraud",
    "AMT": "Large Amount",
    "NGT": "Off-Hours Fraud",
    "ANO": "Anomalous Pattern",
}

FRAUD_COLORS = {
    "ATO": ("#991B1B", "#FEE2E2"),
    "VEL": ("#C2410C", "#FFF7ED"),
    "AMT": ("#92400E", "#FFFBEB"),
    "NGT": ("#6D28D9", "#F5F3FF"),
    "ANO": ("#1D4ED8", "#EFF6FF"),
}

ACTION_META = {
    "BLOCK":    ("Block Transaction",    "Halt this transaction immediately. Funds will not be released."),
    "FREEZE":   ("Freeze Account",       "Lock the account. Customer cannot transact until unfrozen."),
    "ALERT":    ("Send Customer Alert",  "Notify the customer via SMS and in-app to verify this activity."),
    "ESCALATE": ("Escalate to L2",       "Assign to a Level 2 senior analyst for deeper investigation."),
    "CLEAR":    ("Clear — False Positive","Mark as legitimate. Remove from open cases."),
}

HIGH_W  = [0.35, 0.22, 0.20, 0.13, 0.10]
MED_W   = [0.12, 0.13, 0.18, 0.27, 0.30]
CODES   = list(FRAUD_TYPES.keys())

NAMES    = ["Priya Sharma","Rahul Mehta","Anita Patel","Vikram Singh","Deepa Nair",
            "Arjun Kapoor","Sunita Reddy","Kiran Joshi","Amit Verma","Pooja Iyer",
            "Ravi Kumar","Meena Gupta","Suresh Pillai","Kavitha Rao","Nitin Desai",
            "Sanjay Tiwari","Lakshmi Venkat","Rohit Sinha","Neha Bose","Arun Nambiar"]
ACCT_T   = ["Savings","Current","Salary","NRI","Business"]
DEVICES  = ["iPhone 15 Pro","Samsung Galaxy S24","Redmi Note 13","OnePlus 12",
            "Unknown Device","Google Pixel 8","Vivo V29","OPPO Reno 11"]
CITIES   = ["Mumbai","Delhi","Bangalore","Chennai","Hyderabad","Pune",
            "Kolkata","Ahmedabad","Jaipur","Lucknow","Surat","Kochi"]
BANKS    = ["HDFC Bank","ICICI Bank","SBI","Axis Bank","Kotak Mahindra",
            "IndusInd Bank","Yes Bank","PNB","Bank of Baroda","Canara Bank"]

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def fmt_inr(v):
    v = float(v)
    if v >= 100000:
        return f"₹{v/100000:.2f}L"
    if v >= 1000:
        return f"₹{v:,.0f}"
    return f"₹{v:.0f}"

def fmt_time(h):
    h = int(h) % 24
    return f"{h%12 or 12:02d}:00 {'AM' if h < 12 else 'PM'}"

def ts_now():
    return datetime.datetime.now().strftime("%H:%M:%S")

def pick_code(label):
    return random.choices(CODES, weights=HIGH_W if label == "HIGH" else MED_W, k=1)[0]

def make_customer():
    name = random.choice(NAMES)
    avg  = round(random.uniform(400, 15000), 0)
    return {
        "name":         name,
        "initials":     "".join(p[0] for p in name.split()),
        "account_no":   f"{''.join([str(random.randint(0,9)) for _ in range(4)])} {''.join([str(random.randint(0,9)) for _ in range(4)])} {''.join([str(random.randint(0,9)) for _ in range(4)])}",
        "account_type": random.choice(ACCT_T),
        "bank":         random.choice(BANKS),
        "city":         random.choice(CITIES),
        "device":       random.choice(DEVICES),
        "avg_txn":      avg,
        "txn_30d":      random.randint(5, 80),
        "balance":      round(random.uniform(2000, 500000), 0),
        "last_login":   f"{random.randint(1,12):02d}:{random.randint(0,5)}{random.randint(0,9)} {'AM' if random.random() > 0.5 else 'PM'}",
        "member_since": f"{random.randint(2015, 2023)}",
        "risk_history": random.choice([
            "Clean — no prior flags",
            "Clean — no prior flags",
            "Clean — no prior flags",
            "1 flag in last 90 days",
            "2 flags in last 90 days",
            "New account < 30 days",
        ]),
    }

def build_reasons(code, amt, hour, score, customer):
    ts  = fmt_time(hour)
    mul = round(amt / max(customer["avg_txn"], 1), 1)
    vel = random.randint(4, 22)
    amt_s = fmt_inr(amt)
    avg_s = fmt_inr(customer["avg_txn"])

    reasons = {
        "ATO": [
            ("New device fingerprint",     f"Transaction originated from '{customer['device']}' — this device has no prior transaction history on this account."),
            ("Unusual hour",               f"Account accessed at {ts}, outside this customer's established activity window (typically 9 AM–9 PM)."),
            ("Amount anomaly",             f"{amt_s} is {mul}x above this customer's 30-day average of {avg_s}. Large transfers immediately after device change are a primary ATO signal."),
            ("Rapid post-login action",    "Transaction initiated within seconds of authentication — attackers execute transfers immediately before victims receive SMS alerts."),
        ],
        "VEL": [
            ("Transaction burst detected", f"{vel} transactions attempted within 90 seconds from the same card — consistent with automated card-testing scripts."),
            ("Uniform amount pattern",     f"Each transaction is exactly {amt_s}. Fraudsters use identical amounts to test card validity before executing a large withdrawal."),
            ("Off-peak timing",            f"Burst initiated at {ts}. Automated fraud systems target off-peak hours to reduce real-time monitoring friction."),
            ("Cumulative exposure",        f"If all {vel} transactions clear, total exposure is {fmt_inr(amt * vel)}. Velocity block is the fastest intervention."),
        ],
        "AMT": [
            ("Abnormal transaction size",  f"{amt_s} is {mul}x this customer's 30-day average ({avg_s}). No prior transaction of this magnitude exists in 6 months of data."),
            ("No historical precedent",    "This amount exceeds the 99th percentile of all transactions on this account — statistically a 1-in-100 event requiring verification."),
            ("Time-of-day risk",           f"High-value transaction at {ts}. Night-time large transfers have a 3.2x higher fraud rate than daytime transactions."),
            ("Irreversible if fraud",      f"Instant transfers cannot be recalled. If fraudulent, the customer permanently loses {amt_s} — immediate hold recommended."),
        ],
        "NGT": [
            ("Outside activity window",    f"No transaction history between 11 PM and 5 AM across 6 months. This customer has never transacted at {ts} before."),
            ("High-value off-hours",       f"{amt_s} at {ts}. Off-hours high-value transactions have a fraud rate 4.1x higher than normal operating hours."),
            ("No prior night behaviour",   f"Customer's transaction history shows {customer['txn_30d']} transactions in the last 30 days, all during daytime hours."),
            ("Detection window",           "Night fraud is rarely discovered until the following morning. Early detection and block is the only effective intervention."),
        ],
        "ANO": [
            ("Behavioural outlier",        f"The Isolation Forest model assigns this transaction an anomaly score in the top 2% of all {len(scores):,} transactions analysed."),
            ("No matching fraud template", "This pattern does not match any known attack signature (ATO, velocity, card testing). Unsupervised model flagged it as novel."),
            ("Amount deviation",           f"{amt_s} is {mul}x this customer's average ({avg_s}) — statistically abnormal even without a known fraud pattern."),
            ("Composite risk score",       f"Combined XGBoost + Isolation Forest score: {score:.3f}/1.000. Threshold for review is 0.30 — this exceeds it by {score-0.30:.3f}."),
        ],
    }
    return reasons.get(code, reasons["ANO"])

def generate_transaction(label):
    pidx  = random.choice(POOLS[label])
    score = float(scores.loc[pidx, "final_score"])
    amt   = float(X["TransactionAmt"].iloc[pidx])
    if amt < 200:
        amt = round(random.uniform(1200, 180000), 2)
    hour  = random.randint(0, 23)
    code  = pick_code(label)
    cust  = make_customer()
    hl_map = {
        "ATO": "Login from unrecognised device",
        "VEL": f"{random.randint(4,22)} transactions in rapid succession",
        "AMT": f"{fmt_inr(amt)} — {round(amt/max(cust['avg_txn'],1),1)}x customer average",
        "NGT": f"Transaction at {fmt_time(hour)} — outside normal window",
        "ANO": "Significant deviation from customer profile",
    }
    return {
        "cid":      f"FR-{st.session_state.ctr:05d}",
        "code":     code,
        "ft":       FRAUD_TYPES[code],
        "hl":       hl_map[code],
        "reasons":  build_reasons(code, amt, hour, score, cust),
        "amt":      amt,
        "amt_s":    fmt_inr(amt),
        "hour":     hour,
        "det":      ts_now(),
        "label":    label,
        "score":    score,
        "customer": cust,
        "status":   "OPEN",
        "note":     "",
        "assigned": "W. Mautsa",
    }

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
def init_state():
    defaults = dict(
        tab="feed", running=False, idx=0,
        feed=[], cases=[], rlog=[], act_case=None,
        ctr=10000, processed=0, blocked=0, flagged=0, safe=0,
        resolved=0, frozen=0, escalated=0, alerted=0, fp=0,
        tps=0, fslots=[], note_draft="",
    )
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
S = st.session_state

# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  --bg:       #F5F6F8;
  --surface:  #FFFFFF;
  --border:   #E4E7ED;
  --border2:  #CDD2DA;
  --text1:    #0F1923;
  --text2:    #4A5568;
  --text3:    #8A95A3;
  --green:    #1B5E3B;
  --green2:   #E8F5EE;
  --red:      #C0392B;
  --red2:     #FDEDEC;
  --amber:    #B7770D;
  --amber2:   #FEF9EC;
  --blue:     #1A4A8A;
  --blue2:    #EBF2FB;
  --mono:     'IBM Plex Mono', monospace;
  --sans:     'IBM Plex Sans', sans-serif;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"], .stApp {
  background: var(--bg) !important;
  font-family: var(--sans) !important;
  font-size: 13px;
  color: var(--text1);
}

[data-testid="stHeader"] { background: transparent !important; }
header, footer { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none !important; }
div[data-testid="stVerticalBlock"] { gap: 0 !important; }
div[data-testid="column"] { padding: 0 !important; }
[data-testid="stHorizontalBlock"] { gap: 0 !important; }

/* ── HIDE NAV TRIGGER BUTTONS (FIX: duplicate tab bar) ── */
/* Target the specific column row containing our nav buttons */
[data-testid="stHorizontalBlock"]:has([data-testid="column"]:first-child [data-testid="stButton"] button[kind="secondary"]) {
  position: absolute !important;
  width: 0 !important;
  height: 0 !important;
  overflow: hidden !important;
  opacity: 0 !important;
  pointer-events: none !important;
  margin: 0 !important;
  padding: 0 !important;
  top: -9999px !important;
  left: -9999px !important;
}

/* ── TOP BAR ── */
.topbar {
  height: 52px;
  background: var(--green);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 2px solid rgba(0,0,0,.15);
}
.tb-left  { display: flex; align-items: center; gap: 20px; }
.tb-right { display: flex; align-items: center; gap: 16px; }
.tb-logo  {
  font-family: var(--mono);
  font-size: 15px;
  font-weight: 500;
  color: #fff;
  letter-spacing: 2px;
}
.tb-divider { width: 1px; height: 20px; background: rgba(255,255,255,.25); }
.tb-env {
  font-size: 10px;
  font-weight: 600;
  color: rgba(255,255,255,.7);
  text-transform: uppercase;
  letter-spacing: 1.5px;
  border: 1px solid rgba(255,255,255,.3);
  border-radius: 3px;
  padding: 2px 8px;
}
.tb-stat { display: flex; flex-direction: column; align-items: center; }
.tb-stat-v { font-family: var(--mono); font-size: 14px; font-weight: 500; color: #fff; line-height: 1; }
.tb-stat-l { font-size: 9px; color: rgba(255,255,255,.6); text-transform: uppercase; letter-spacing: .8px; margin-top: 2px; }
.tb-status {
  display: flex; align-items: center; gap: 6px;
  background: rgba(255,255,255,.12);
  border: 1px solid rgba(255,255,255,.2);
  border-radius: 4px;
  padding: 5px 12px;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  font-family: var(--mono);
}
.tb-dot-live { width: 7px; height: 7px; background: #4ADE80; border-radius: 50%; animation: pulse 1.5s infinite; }
.tb-dot-off  { width: 7px; height: 7px; background: rgba(255,255,255,.4); border-radius: 50%; }
@keyframes pulse { 0%,100%{opacity:1; transform:scale(1)} 50%{opacity:.6; transform:scale(.85)} }
.tb-analyst {
  display: flex; align-items: center; gap: 8px;
  background: rgba(255,255,255,.1);
  border: 1px solid rgba(255,255,255,.2);
  border-radius: 4px;
  padding: 5px 10px;
}
.tb-av {
  width: 26px; height: 26px;
  background: rgba(255,255,255,.25);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700; color: #fff;
}
.tb-aname { font-size: 12px; font-weight: 600; color: #fff; }
.tb-arole { font-size: 10px; color: rgba(255,255,255,.6); }

/* ── METRICS BAR ── */
.metbar {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0 24px;
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 0;
}
.met {
  padding: 10px 14px;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.met:last-child { border-right: none; }
.met-l { font-size: 10px; font-weight: 600; color: var(--text3); text-transform: uppercase; letter-spacing: .8px; }
.met-v { font-family: var(--mono); font-size: 18px; font-weight: 500; color: var(--text1); line-height: 1; }
.met-v.red    { color: var(--red); }
.met-v.amber  { color: var(--amber); }
.met-v.green  { color: var(--green); }
.met-v.blue   { color: var(--blue); }
.met-sub { font-size: 10px; color: var(--text3); }

/* ── TICKER ── */
.ticker {
  background: #0F1923;
  padding: 6px 24px;
  display: flex;
  align-items: center;
  gap: 0;
  overflow: hidden;
  font-family: var(--mono);
  font-size: 11px;
  color: rgba(255,255,255,.5);
  white-space: nowrap;
}
.tick-item { display: flex; align-items: center; gap: 6px; padding: 0 16px; border-right: 1px solid rgba(255,255,255,.08); }
.tick-item:first-child { padding-left: 0; }
.tick-lbl { color: rgba(255,255,255,.35); text-transform: uppercase; letter-spacing: .8px; font-size: 9px; }
.tick-val { color: #fff; font-weight: 500; }
.tick-val.r { color: #FC8181; }
.tick-val.a { color: #F6C90E; }
.tick-val.g { color: #48BB78; }

/* ── NAV TABS ── */
.navtabs {
  background: var(--surface);
  border-bottom: 2px solid var(--border);
  padding: 0 24px;
  display: flex;
  align-items: flex-end;
  gap: 0;
}
.navtab {
  padding: 12px 20px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text3);
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  cursor: pointer;
  white-space: nowrap;
  transition: color .15s;
  text-decoration: none;
}
.navtab.active { color: var(--green); border-bottom-color: var(--green); font-weight: 600; }
.navtab:hover  { color: var(--text2); }
.nbadge {
  display: inline-block;
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 500;
  padding: 1px 6px;
  border-radius: 3px;
  margin-left: 6px;
  background: var(--bg);
  color: var(--text3);
}
.nbadge.alert { background: var(--red2); color: var(--red); }

/* ── PAGE CONTENT ── */
.page { padding: 20px 24px; }

/* ── FEED TABLE ── */
.feed-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}
.feed-toolbar {
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg);
}
.feed-toolbar-left { display: flex; align-items: center; gap: 10px; }
.feed-title { font-size: 13px; font-weight: 600; color: var(--text1); }
.feed-sub   { font-size: 11px; color: var(--text3); }
.feed-stat  {
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 3px;
}
.feed-stat.r { background: var(--red2);   color: var(--red);   }
.feed-stat.a { background: var(--amber2); color: var(--amber); }

.feed-thead {
  display: grid;
  grid-template-columns: 90px 90px 170px 200px 120px 160px 80px 95px;
  padding: 8px 16px;
  background: #F8F9FB;
  border-bottom: 1px solid var(--border);
}
.fth {
  font-size: 10px;
  font-weight: 700;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: .7px;
}
.frow {
  display: grid;
  grid-template-columns: 90px 90px 170px 200px 120px 160px 80px 95px;
  padding: 10px 16px;
  border-bottom: 1px solid #F3F5F8;
  align-items: center;
  transition: background .1s;
}
.frow:last-child { border-bottom: none; }
.frow:hover { background: #F8F9FB; }
.frow.H { background: #FEF8F8; }
.frow.H:hover { background: #FDEEED; }
.frow.M { background: #FEFDF6; }
.frow.M:hover { background: #FEFAEB; }

.fc     { font-size: 12px; color: var(--text2); }
.fc.mo  { font-family: var(--mono); font-size: 11px; color: var(--text2); }
.fc.bold{ font-weight: 600; color: var(--text1); font-size: 13px; }
.fc.sm  { font-size: 11px; color: var(--text3); margin-top: 2px; }

.ftag {
  display: inline-block;
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 3px;
}
.ftag.ATO { background: #FEE2E2; color: #991B1B; }
.ftag.VEL { background: #FFF4E5; color: #9C3700; }
.ftag.AMT { background: #FFF9E5; color: #7A4200; }
.ftag.NGT { background: #F3F0FF; color: #5B21B6; }
.ftag.ANO { background: #EBF3FF; color: #1E40AF; }

.rtag {
  display: inline-block;
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 10px;
}
.rtag.HIGH   { background: #FEE2E2; color: #9B1C1C; }
.rtag.MEDIUM { background: #FEF3C7; color: #92400E; }

.stag {
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 600;
}
.stag.BLOCKED { color: var(--red);   }
.stag.FLAGGED { color: var(--amber); }

.feed-empty {
  padding: 64px 20px;
  text-align: center;
}
.feed-empty-title { font-size: 14px; font-weight: 600; color: var(--text2); margin-bottom: 6px; }
.feed-empty-sub   { font-size: 12px; color: var(--text3); line-height: 1.8; }

/* ── CASE MANAGER LAYOUT ── */
.cm-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 16px;
  align-items: start;
}

/* case list */
.clist {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}
.clist-hdr {
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.clist-title { font-size: 12px; font-weight: 600; color: var(--text1); text-transform: uppercase; letter-spacing: .5px; }
.clist-counts { display: flex; gap: 6px; }
.clist-badge {
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 3px;
}
.clist-badge.r { background: var(--red2);   color: var(--red);   }
.clist-badge.a { background: var(--amber2); color: var(--amber); }

.citem {
  padding: 12px 14px;
  border-bottom: 1px solid #F3F5F8;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: background .1s;
}
.citem:last-child { border-bottom: none; }
.citem:hover { background: #F8F9FB; }
.citem.sel { background: #F0F7F3; border-left-color: var(--green); }
.citem.HIGH   { border-left-color: var(--red); }
.citem.MEDIUM { border-left-color: var(--amber); }
.citem.sel    { border-left-color: var(--green) !important; background: #F0F7F3; }

.ci-top  { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.ci-id   { font-family: var(--mono); font-size: 10px; color: var(--text3); font-weight: 500; }
.ci-ft   { font-size: 13px; font-weight: 600; color: var(--text1); margin-bottom: 3px; }
.ci-hl   { font-size: 11px; color: var(--text3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 6px; }
.ci-foot { display: flex; align-items: center; justify-content: space-between; }
.ci-amt  { font-family: var(--mono); font-size: 12px; font-weight: 600; color: var(--text1); }
.ci-time { font-family: var(--mono); font-size: 10px; color: var(--text3); }
.ci-cust { font-size: 10px; color: var(--text3); margin-top: 5px; }

/* ── CASE DETAIL ── */
.cdetail { display: flex; flex-direction: column; gap: 12px; }

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}
.card-hdr {
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-hdr.HIGH   { background: #FDF0EF; border-bottom-color: #F5C6C2; }
.card-hdr.MEDIUM { background: #FEF9EC; border-bottom-color: #F2D78A; }
.card-title { font-size: 12px; font-weight: 600; color: var(--text1); text-transform: uppercase; letter-spacing: .5px; }
.card-body  { padding: 14px 16px; }

/* alert header */
.alert-hdr {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
}
.alert-hdr.HIGH   { background: var(--red2);   border-bottom-color: #F5C6C2; }
.alert-hdr.MEDIUM { background: var(--amber2); border-bottom-color: #F2D78A; }
.alert-case-id { font-family: var(--mono); font-size: 10px; font-weight: 600; color: var(--text3); margin-bottom: 4px; }
.alert-case-id.HIGH   { color: var(--red); }
.alert-case-id.MEDIUM { color: var(--amber); }
.alert-hl { font-size: 16px; font-weight: 700; color: var(--text1); line-height: 1.3; margin-bottom: 4px; }
.alert-det { font-family: var(--mono); font-size: 11px; color: var(--text3); }

/* meta grid */
.meta4 { display: grid; grid-template-columns: repeat(4,1fr); }
.meta3 { display: grid; grid-template-columns: repeat(3,1fr); }
.meta2 { display: grid; grid-template-columns: repeat(2,1fr); }
.mf {
  padding: 12px 16px;
  border-right: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}
.mf:last-child,
.mf:nth-child(4n) { border-right: none; }
.mf:nth-last-child(-n+4) { border-bottom: none; }
.mf3:nth-child(3n)  { border-right: none; }
.mf3:nth-last-child(-n+3) { border-bottom: none; }
.mf2:nth-child(2n)  { border-right: none; }
.mf2:nth-last-child(-n+2) { border-bottom: none; }
.ml { font-size: 10px; font-weight: 600; color: var(--text3); text-transform: uppercase; letter-spacing: .8px; margin-bottom: 4px; }
.mv { font-family: var(--mono); font-size: 14px; font-weight: 500; color: var(--text1); }
.mv.red   { color: var(--red);   }
.mv.amber { color: var(--amber); }
.mv.green { color: var(--green); }
.mv.sm    { font-size: 12px; }

/* customer profile */
.cust-banner {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--bg);
}
.cust-av {
  width: 44px; height: 44px;
  border-radius: 50%;
  background: var(--green);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 700; color: #fff;
  flex-shrink: 0;
}
.cust-name { font-size: 15px; font-weight: 700; color: var(--text1); }
.cust-sub  { font-family: var(--mono); font-size: 11px; color: var(--text3); margin-top: 2px; }
.cust-bal  { margin-left: auto; text-align: right; }
.cust-bal-v { font-family: var(--mono); font-size: 15px; font-weight: 600; color: var(--text1); }
.cust-bal-l { font-size: 10px; color: var(--text3); text-transform: uppercase; letter-spacing: .5px; margin-top: 2px; }

/* risk pill */
.risk-hist {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 3px;
}
.risk-hist.ok   { background: #E8F5EE; color: var(--green); }
.risk-hist.warn { background: var(--amber2); color: var(--amber); }
.risk-hist.bad  { background: var(--red2);   color: var(--red); }

/* SHAP */
.shap-item { padding: 10px 0; border-bottom: 1px solid #F3F5F8; }
.shap-item:last-child { border-bottom: none; padding-bottom: 0; }
.shap-row  { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.shap-name { font-size: 12px; font-weight: 600; color: var(--text1); }
.shap-val  { font-family: var(--mono); font-size: 11px; font-weight: 600; color: var(--red); }
.shap-bar  { height: 3px; background: #EEF0F3; border-radius: 2px; margin-bottom: 5px; }
.shap-fill { height: 3px; background: var(--red); border-radius: 2px; }
.shap-desc { font-size: 11px; color: var(--text3); line-height: 1.6; }

/* action panel */
.action-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.action-btn {
  padding: 10px 14px;
  border: 1px solid var(--border2);
  border-radius: 5px;
  background: var(--surface);
  cursor: pointer;
  text-align: left;
  transition: all .15s;
}
.action-btn:hover { border-color: var(--green); background: var(--green2); }
.action-btn.danger:hover { border-color: var(--red); background: var(--red2); }
.action-btn.wide { grid-column: 1 / -1; }
.action-btn.wide:hover { border-color: var(--text3); background: var(--bg); }
.ab-title { font-size: 12px; font-weight: 600; color: var(--text1); margin-bottom: 2px; }
.ab-desc  { font-size: 10px; color: var(--text3); line-height: 1.4; }

/* note textarea */
.note-area {
  width: 100%;
  min-height: 70px;
  border: 1px solid var(--border2);
  border-radius: 5px;
  padding: 8px 10px;
  font-family: var(--sans);
  font-size: 12px;
  color: var(--text1);
  resize: vertical;
  background: var(--surface);
}
.note-area:focus { outline: none; border-color: var(--green); }

/* resolved log */
.rlog-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 16px;
  border-bottom: 1px solid #F3F5F8;
}
.rlog-item:last-child { border-bottom: none; }
.rlog-icon {
  width: 28px; height: 28px;
  border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.rlog-main { font-size: 12px; font-weight: 600; color: var(--text1); }
.rlog-sub  { font-size: 10px; color: var(--text3); margin-top: 2px; }
.rlog-act  { margin-left: auto; font-family: var(--mono); font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 3px; flex-shrink: 0; }
.rlog-note { font-size: 10px; color: var(--text3); font-style: italic; margin-top: 2px; }

/* summary tiles */
.summary-tiles { display: grid; grid-template-columns: repeat(4,1fr); gap: 10px; margin-top: 14px; }
.stile {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px 14px;
  text-align: center;
}
.stile-v { font-family: var(--mono); font-size: 22px; font-weight: 500; margin-bottom: 3px; }
.stile-l { font-size: 10px; color: var(--text3); font-weight: 600; text-transform: uppercase; letter-spacing: .5px; }

/* chart cards */
.ccrd {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 14px 16px;
  margin-bottom: 10px;
}
.ccrd-title { font-size: 11px; font-weight: 600; color: var(--text3); text-transform: uppercase; letter-spacing: .8px; margin-bottom: 12px; }

/* empty state */
.empty {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 72px 20px;
  text-align: center;
}
.empty-t { font-size: 14px; font-weight: 600; color: var(--text2); margin-bottom: 8px; }
.empty-s { font-size: 12px; color: var(--text3); line-height: 1.8; }

/* streamlit buttons */
div[data-testid="stButton"] > button {
  font-family: var(--sans) !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  border-radius: 5px !important;
  height: 34px !important;
  border: 1px solid var(--border2) !important;
  background: var(--surface) !important;
  color: var(--text1) !important;
  transition: all .15s !important;
}
div[data-testid="stButton"] > button:hover {
  border-color: var(--green) !important;
  background: var(--green2) !important;
  color: var(--green) !important;
}

/* streamlit download button — match regular button style */
div[data-testid="stDownloadButton"] > button {
  font-family: var(--sans) !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  border-radius: 5px !important;
  height: 34px !important;
  border: 1px solid var(--border2) !important;
  background: var(--surface) !important;
  color: var(--text1) !important;
  transition: all .15s !important;
  width: 100% !important;
}
div[data-testid="stDownloadButton"] > button:hover {
  border-color: var(--green) !important;
  background: var(--green2) !important;
  color: var(--green) !important;
}

/* streamlit text area */
div[data-testid="stTextArea"] textarea {
  font-family: var(--sans) !important;
  font-size: 12px !important;
  border-radius: 5px !important;
  border-color: var(--border2) !important;
  color: var(--text1) !important;
}
div[data-testid="stTextArea"] textarea:focus {
  border-color: var(--green) !important;
  box-shadow: none !important;
}
div[data-testid="stTextArea"] label { font-size: 11px !important; color: var(--text3) !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FRAGMENT: TOPBAR + METRICS (auto-refresh)
# ─────────────────────────────────────────────
@st.fragment(run_every=2)
def topbar():
    S  = st.session_state
    tp = S["processed"]; tb = S["blocked"]
    tf = S["flagged"];   ts = S["safe"]
    fr = tb / max(tp, 1) * 100
    avg_s = sum(t["score"] for t in S["feed"]) / max(len(S["feed"]), 1)
    oc    = len(S["cases"])
    tps   = S["tps"]

    pill = (
        '<div class="tb-status"><div class="tb-dot-live"></div>LIVE MONITORING</div>'
        if S["running"] else
        '<div class="tb-status"><div class="tb-dot-off"></div>MONITORING PAUSED</div>'
    )

    st.markdown(f"""
<div class="topbar">
  <div class="tb-left">
    <div class="tb-logo">FRAUDOPS</div>
    <div class="tb-divider"></div>
    <div class="tb-env">PRODUCTION</div>
    <div class="tb-divider"></div>
    <div class="tb-stat"><div class="tb-stat-v">{tps}</div><div class="tb-stat-l">txn/min</div></div>
    <div class="tb-stat"><div class="tb-stat-v">{tp:,}</div><div class="tb-stat-l">processed</div></div>
  </div>
  <div class="tb-right">
    {pill}
    <div class="tb-analyst">
      <div class="tb-av">WM</div>
      <div>
        <div class="tb-aname">W. Mautsa</div>
        <div class="tb-arole">Senior Fraud Analyst · Desk 4</div>
      </div>
    </div>
  </div>
</div>
<div class="metbar">
  <div class="met"><div class="met-l">Processed</div><div class="met-v">{tp:,}</div><div class="met-sub">today</div></div>
  <div class="met"><div class="met-l">Passed</div><div class="met-v green">{ts:,}</div><div class="met-sub">silently cleared</div></div>
  <div class="met"><div class="met-l">Blocked</div><div class="met-v red">{tb:,}</div><div class="met-sub">{fr:.2f}% rate</div></div>
  <div class="met"><div class="met-l">Flagged</div><div class="met-v amber">{tf:,}</div><div class="met-sub">under review</div></div>
  <div class="met"><div class="met-l">Open Cases</div><div class="met-v blue">{oc}</div><div class="met-sub">awaiting action</div></div>
  <div class="met"><div class="met-l">Resolved</div><div class="met-v">{S["resolved"]}</div><div class="met-sub">{S["fp"]} false +ve</div></div>
  <div class="met"><div class="met-l">Avg Score</div><div class="met-v">{avg_s:.3f}</div><div class="met-sub">fraud events</div></div>
  <div class="met"><div class="met-l">Fraud Alerts</div><div class="met-v">{len(S["feed"])}</div><div class="met-sub">in feed</div></div>
</div>
<div class="ticker">
  <div class="tick-item"><span class="tick-lbl">Rate</span><span class="tick-val r">{fr:.2f}%</span></div>
  <div class="tick-item"><span class="tick-lbl">Blocked</span><span class="tick-val r">{tb}</span></div>
  <div class="tick-item"><span class="tick-lbl">Flagged</span><span class="tick-val a">{tf}</span></div>
  <div class="tick-item"><span class="tick-lbl">Passed</span><span class="tick-val g">{ts:,}</span></div>
  <div class="tick-item"><span class="tick-lbl">Open Cases</span><span class="tick-val">{oc}</span></div>
  <div class="tick-item"><span class="tick-lbl">Resolved</span><span class="tick-val">{S["resolved"]}</span></div>
  <div class="tick-item"><span class="tick-lbl">Frozen</span><span class="tick-val">{S["frozen"]}</span></div>
  <div class="tick-item"><span class="tick-lbl">Escalated</span><span class="tick-val">{S["escalated"]}</span></div>
  <div class="tick-item"><span class="tick-lbl">Alerted</span><span class="tick-val">{S["alerted"]}</span></div>
  <div class="tick-item"><span class="tick-lbl">False +ve</span><span class="tick-val">{S["fp"]}</span></div>
</div>
""", unsafe_allow_html=True)

topbar()

# ─────────────────────────────────────────────
# NAV TABS
# ─────────────────────────────────────────────
fc  = len(S["feed"])
oc  = len(S["cases"])
nbf = f'<span class="nbadge alert">{fc}</span>'  if fc else f'<span class="nbadge">{fc}</span>'
nbc = f'<span class="nbadge alert">{oc}</span>'  if oc else f'<span class="nbadge">{oc}</span>'
t   = S["tab"]

st.markdown(f"""
<div class="navtabs">
  <a class="navtab {'active' if t=='feed' else ''}" href="?tab=feed" target="_self">Fraud Alerts{nbf}</a>
  <a class="navtab {'active' if t=='cases' else ''}" href="?tab=cases" target="_self">Case Manager{nbc}</a>
  <a class="navtab {'active' if t=='analytics' else ''}" href="?tab=analytics" target="_self">Analytics</a>
</div>
""", unsafe_allow_html=True)

# Nav driven by URL query param — zero Streamlit widgets rendered, no second tab bar
params = st.query_params
if "tab" in params and params["tab"] in ("feed", "cases", "analytics"):
    if params["tab"] != S["tab"]:
        S["tab"] = params["tab"]
        st.rerun()
# ─────────────────────────────────────────────
# TAB: FRAUD ALERTS
# ─────────────────────────────────────────────
if t == "feed":

    @st.fragment(run_every=2)
    def feed_panel():
        # FIX 2: Always read fresh from session_state inside fragment
        # (not a stale local snapshot captured at fragment definition time)
        S    = st.session_state
        feed = S["feed"]          # fresh read every 2s tick
        fc_  = len(feed)
        tb_  = S["blocked"]
        tf_  = S["flagged"]

        st.markdown('<div class="page">', unsafe_allow_html=True)

        # FIX 3: Export CSV — build CSV from current feed and serve via download_button
        def build_csv(feed_data):
            rows = []
            for txn in feed_data:
                cust = txn.get("customer", {})
                rows.append({
                    "Time":         txn["det"],
                    "Case ID":      txn["cid"],
                    "Fraud Type":   txn["ft"],
                    "Code":         txn["code"],
                    "Detection":    txn["hl"],
                    "Amount":       txn["amt_s"],
                    "Risk Score":   f"{txn['score']:.4f}",
                    "Label":        txn["label"],
                    "Status":       "BLOCKED" if txn["label"] == "HIGH" else "FLAGGED",
                    "Customer":     cust.get("name", "—"),
                    "City":         cust.get("city", "—"),
                    "Bank":         cust.get("bank", "—"),
                    "Device":       cust.get("device", "—"),
                    "Account Type": cust.get("account_type", "—"),
                    "Avg Txn":      fmt_inr(cust.get("avg_txn", 0)),
                    "Balance":      fmt_inr(cust.get("balance", 0)),
                    "Risk History": cust.get("risk_history", "—"),
                })
            return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")

        # Toolbar
        c1, c2, c3, c4 = st.columns([1, 1, 1, 6])
        with c1:
            lbl = "Pause Feed" if S["running"] else "Start Feed"
            if st.button(lbl, key="sim_tog", use_container_width=True):
                S["running"] = not S["running"]; st.rerun()
        with c2:
            if st.button("Clear Feed", key="clr", use_container_width=True):
                S["feed"] = []; st.rerun()
        with c3:
            # FIX 3: Working Export CSV via st.download_button
            csv_data = build_csv(feed) if feed else b"No data"
            fname    = f"fraudops_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            st.download_button(
                label="Export CSV",
                data=csv_data,
                file_name=fname,
                mime="text/csv",
                key="exp",
                use_container_width=True,
                disabled=not feed,
            )

        # Build table
        tbl  = '<div class="feed-wrap">'
        tbl += '<div class="feed-toolbar">'
        tbl += f'<div><div class="feed-title">Live Transaction Alerts</div><div class="feed-sub">High-volume feed · only fraud events surface · clean transactions pass silently</div></div>'
        tbl += f'<div style="display:flex;gap:8px"><span class="feed-stat r">{tb_} BLOCKED</span><span class="feed-stat a">{tf_} FLAGGED</span></div>'
        tbl += '</div>'

        tbl += '<div class="feed-thead">'
        tbl += '<div class="fth">Time</div>'
        tbl += '<div class="fth">Case ID</div>'
        tbl += '<div class="fth">Fraud Type</div>'
        tbl += '<div class="fth">Detection Reason</div>'
        tbl += '<div class="fth">Amount</div>'
        tbl += '<div class="fth">Customer</div>'
        tbl += '<div class="fth">Risk</div>'
        tbl += '<div class="fth">Status</div>'
        tbl += '</div>'

        if not feed:
            tbl += '<div class="feed-empty">'
            tbl += '<div class="feed-empty-title">No fraud detected yet</div>'
            tbl += '<div class="feed-empty-sub">The system is processing ~500 transactions per minute.<br>Clean transactions pass silently — only blocked and flagged events appear here.</div>'
            tbl += '</div>'
        else:
            for txn in reversed(feed[-50:]):
                l    = txn["label"]
                rc   = "H" if l == "HIGH" else "M"
                st_  = "BLOCKED" if l == "HIGH" else "FLAGGED"
                sc   = "BLOCKED" if l == "HIGH" else "FLAGGED"
                # FIX 2: customer dict is always present (set at txn creation),
                # but guard defensively so empty dict gives "—" not a KeyError
                cust = txn.get("customer", {})
                cust_name = cust.get("name") or "—"
                cust_city = cust.get("city") or "—"

                tbl += f'<div class="frow {rc}">'
                tbl += f'<div class="fc mo">{txn["det"]}</div>'
                tbl += f'<div class="fc mo">{txn["cid"]}</div>'
                tbl += f'<div class="fc"><span class="ftag {txn["code"]}">{txn["code"]}</span><br><span style="font-size:11px;color:var(--text2)">{txn["ft"]}</span></div>'
                tbl += f'<div class="fc"><div style="font-size:11px;color:var(--text2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:190px">{txn["hl"]}</div></div>'
                tbl += f'<div class="fc bold">{txn["amt_s"]}</div>'
                tbl += f'<div class="fc"><div style="font-size:12px;font-weight:600;color:var(--text1)">{cust_name}</div><div class="fc sm">{cust_city}</div></div>'
                tbl += f'<div class="fc"><span class="rtag {l}">{l}</span><br><span style="font-family:var(--mono);font-size:10px;color:var(--text3)">{txn["score"]:.3f}</span></div>'
                tbl += f'<div class="fc"><span class="stag {sc}">{st_}</span></div>'
                tbl += '</div>'

        tbl += '</div>'
        st.markdown(tbl, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    feed_panel()

# ─────────────────────────────────────────────
# TAB: CASE MANAGER
# ─────────────────────────────────────────────
elif t == "cases":
    cases = S["cases"]

    st.markdown('<div class="page">', unsafe_allow_html=True)

    if not cases:
        st.markdown('<div class="empty"><div class="empty-t">No open cases</div><div class="empty-s">Start the feed to begin processing transactions.<br>Fraud events will automatically populate here as investigable cases.<br>Each case requires an analyst decision before it can be closed.</div></div>', unsafe_allow_html=True)
    else:
        vids = [c["cid"] for c in cases]
        if S["act_case"] not in vids:
            S["act_case"] = cases[-1]["cid"]
        ac = next((c for c in cases if c["cid"] == S["act_case"]), cases[-1])

        st.markdown('<div class="cm-layout">', unsafe_allow_html=True)
        left, right = st.columns([1, 2.4], gap="medium")

        # ── LEFT: case list ──────────────────────
        with left:
            hc = sum(1 for c in cases if c["label"] == "HIGH")
            mc = sum(1 for c in cases if c["label"] == "MEDIUM")
            st.markdown(f"""
<div class="clist">
  <div class="clist-hdr">
    <div class="clist-title">Open Cases</div>
    <div class="clist-counts">
      <span class="clist-badge r">{hc} high</span>
      <span class="clist-badge a">{mc} med</span>
    </div>
  </div>
""", unsafe_allow_html=True)

            for c in reversed(cases):
                sel  = c["cid"] == S["act_case"]
                cust = c.get("customer", {})
                sel_cls = "sel" if sel else c["label"]
                fc_col, fb = FRAUD_COLORS.get(c["code"], ("#374151","#F3F5F8"))

                st.markdown(f"""
<div class="citem {sel_cls}">
  <div class="ci-top">
    <span class="ci-id">{c["cid"]}</span>
    <span class="ftag {c["code"]}">{c["code"]}</span>
  </div>
  <div class="ci-ft">{c["ft"]}</div>
  <div class="ci-hl">{c["hl"]}</div>
  <div class="ci-foot">
    <span class="ci-amt">{c["amt_s"]}</span>
    <span class="ci-time">{c["det"]}</span>
  </div>
  <div class="ci-cust">{cust.get("name") or "—"} &nbsp;·&nbsp; {cust.get("city") or "—"} &nbsp;·&nbsp; {cust.get("bank") or "—"}</div>
</div>
""", unsafe_allow_html=True)
                if st.button(f"Review  {c['cid']}", key=f"sel_{c['cid']}", use_container_width=True):
                    S["act_case"] = c["cid"]; st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        # ── RIGHT: case detail ───────────────────
        with right:
            is_high = ac["label"] == "HIGH"
            vc      = "red" if is_high else "amber"
            cust    = ac.get("customer", {})
            sys_a   = "Auto-blocked by AI model" if is_high else "Auto-flagged — analyst review required"

            st.markdown('<div class="cdetail">', unsafe_allow_html=True)

            # Alert header
            st.markdown(f"""
<div class="card">
  <div class="alert-hdr {ac['label']}">
    <div class="alert-case-id {ac['label']}">
      {ac['cid']} &nbsp;·&nbsp; <span class="ftag {ac['code']}">{ac['code']}</span> &nbsp;·&nbsp; {ac['ft']}
    </div>
    <div class="alert-hl">{ac['hl']}</div>
    <div class="alert-det">Detected at {ac['det']} &nbsp;·&nbsp; Assigned to {ac.get('assigned','W. Mautsa')}</div>
  </div>
  <div class="meta4">
    <div class="mf"><div class="ml">Amount at Risk</div><div class="mv {vc}">{ac['amt_s']}</div></div>
    <div class="mf"><div class="ml">AI Risk Score</div><div class="mv {vc}">{ac['score']:.4f}</div></div>
    <div class="mf"><div class="ml">Fraud Type</div><div class="mv sm">{ac['ft']}</div></div>
    <div class="mf"><div class="ml">System Action</div><div class="mv {vc} sm">{sys_a}</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

            # Customer profile
            rh = cust.get("risk_history", "")
            risk_cls = "bad" if "2 flags" in rh else ("warn" if ("1 flag" in rh or "New" in rh) else "ok")
            dev_warn = "Unknown" in cust.get("device", "")
            st.markdown(f"""
<div class="card">
  <div class="card-hdr"><div class="card-title">Customer Profile</div></div>
  <div class="cust-banner">
    <div class="cust-av">{cust.get('initials','?')}</div>
    <div>
      <div class="cust-name">{cust.get('name') or '—'}</div>
      <div class="cust-sub">{cust.get('account_type','—')} Account &nbsp;·&nbsp; {cust.get('account_no','—')} &nbsp;·&nbsp; {cust.get('bank','—')}</div>
    </div>
    <div class="cust-bal">
      <div class="cust-bal-v">{fmt_inr(cust.get('balance',0))}</div>
      <div class="cust-bal-l">Available Balance</div>
    </div>
  </div>
  <div class="meta3">
    <div class="mf mf3"><div class="ml">Location</div><div class="mv sm">{cust.get('city','—')}</div></div>
    <div class="mf mf3"><div class="ml">Device</div><div class="mv sm" style="color:{'var(--red)' if dev_warn else 'var(--text1)'}">{cust.get('device','—')}</div></div>
    <div class="mf mf3"><div class="ml">Last Login</div><div class="mv sm">{cust.get('last_login','—')}</div></div>
    <div class="mf mf3"><div class="ml">30-Day Avg Txn</div><div class="mv sm">{fmt_inr(cust.get('avg_txn',0))}</div></div>
    <div class="mf mf3"><div class="ml">Txns This Month</div><div class="mv sm">{cust.get('txn_30d','—')}</div></div>
    <div class="mf mf3"><div class="ml">Risk History</div><div class="mv sm"><span class="risk-hist {risk_cls}">{rh}</span></div></div>
  </div>
</div>
""", unsafe_allow_html=True)

            # SHAP explanation
            reasons = ac.get("reasons", [])
            sw = [1.0, 0.62, 0.54, 0.30]
            sv = ["+1.644", "+1.021", "+0.887", "+0.498"]
            sh = '<div class="card"><div class="card-hdr"><div class="card-title">AI Explanation — Why This Was Flagged (SHAP)</div></div><div class="card-body">'
            for i, (ln, desc) in enumerate(reasons[:4]):
                w = sw[i] if i < len(sw) else 0.2
                v = sv[i] if i < len(sv) else "+0.200"
                sh += f'<div class="shap-item"><div class="shap-row"><div class="shap-name">{ln}</div><div class="shap-val">{v}</div></div><div class="shap-bar"><div class="shap-fill" style="width:{int(w*100)}%"></div></div><div class="shap-desc">{desc}</div></div>'
            st.markdown(sh + '</div></div>', unsafe_allow_html=True)

            # Analyst note
            st.markdown('<div class="card"><div class="card-hdr"><div class="card-title">Analyst Notes</div></div><div class="card-body">', unsafe_allow_html=True)
            note = st.text_area("Add investigation note (optional)", value=S.get("note_draft",""), key="note_area", height=80, label_visibility="collapsed", placeholder="Add investigation note — e.g. called customer, confirmed device, escalating due to prior flags...")
            S["note_draft"] = note
            st.markdown('</div></div>', unsafe_allow_html=True)

            # Actions
            st.markdown('<div class="card"><div class="card-hdr"><div class="card-title">Take Action</div></div><div class="card-body">', unsafe_allow_html=True)

            def resolve(action, ck=None):
                S["cases"] = [c for c in S["cases"] if c["cid"] != ac["cid"]]
                S["resolved"] += 1
                if ck: S[ck] += 1
                S["rlog"].append({
                    "cid":    ac["cid"],
                    "ft":     ac["ft"],
                    "code":   ac["code"],
                    "amt_s":  ac["amt_s"],
                    "action": action,
                    "det":    ac["det"],
                    "name":   cust.get("name", "—"),
                    "note":   S.get("note_draft", "").strip(),
                })
                S["note_draft"] = ""
                rem = S["cases"]
                S["act_case"] = rem[-1]["cid"] if rem else None

            a1, a2 = st.columns(2)
            with a1:
                if st.button("Block Transaction",  key="ab", use_container_width=True):
                    resolve("BLOCKED"); st.rerun()
                if st.button("Alert Customer",     key="aa", use_container_width=True):
                    resolve("ALERTED","alerted"); st.rerun()
            with a2:
                if st.button("Freeze Account",     key="af", use_container_width=True):
                    resolve("FROZEN","frozen"); st.rerun()
                if st.button("Escalate to L2",     key="ae", use_container_width=True):
                    resolve("ESCALATED","escalated"); st.rerun()

            st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
            if st.button("Clear — Mark as False Positive", key="afp", use_container_width=True):
                resolve("FALSE POSITIVE","fp"); st.rerun()

            st.markdown("""
<div style="margin-top:10px;padding:10px 12px;background:var(--bg);border-radius:4px;
font-size:11px;color:var(--text3);line-height:1.6">
Each action is logged with your note and the case is closed. The next open case loads automatically.
The fraud event remains in the Fraud Alerts feed for audit purposes.
</div>
</div></div>
""", unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)  # close cdetail

        st.markdown('</div>', unsafe_allow_html=True)  # close cm-layout

    # Resolved log
    rlog = S["rlog"]
    if rlog:
        ACTION_STYLE = {
            "BLOCKED":       ("#FDEDEC","#C0392B"),
            "FROZEN":        ("#FDEDEC","#C0392B"),
            "ALERTED":       ("#E8F5EE","#1B5E3B"),
            "ESCALATED":     ("#EBF2FB","#1A4A8A"),
            "FALSE POSITIVE":("#F5F6F8","#4A5568"),
        }
        st.markdown(f"""
<div style="margin-top:20px">
<div style="font-size:11px;font-weight:700;color:var(--text3);text-transform:uppercase;
letter-spacing:1px;margin-bottom:8px;display:flex;align-items:center;gap:8px">
  Resolved Today
  <span style="background:var(--bg);border:1px solid var(--border);border-radius:3px;
  padding:1px 8px;font-family:var(--mono);color:var(--text2);font-size:11px">{len(rlog)}</span>
</div>
""", unsafe_allow_html=True)

        tbl2 = '<div class="card"><div style="padding:0">'
        for item in reversed(rlog[-15:]):
            bg, cl = ACTION_STYLE.get(item["action"], ("#F5F6F8","#4A5568"))
            nm = item.get("name","—")
            note_txt = f'<div class="rlog-note">Note: {item["note"]}</div>' if item.get("note") else ""
            tbl2 += f"""
<div class="rlog-item">
  <div class="rlog-icon" style="background:{bg}"><span class="ftag {item['code']}">{item['code']}</span></div>
  <div>
    <div class="rlog-main">{item['ft']} &nbsp;·&nbsp; {item['amt_s']} &nbsp;·&nbsp; {nm}</div>
    <div class="rlog-sub">#{item['cid']} &nbsp;·&nbsp; {item['det']}</div>
    {note_txt}
  </div>
  <div class="rlog-act" style="background:{bg};color:{cl}">{item['action']}</div>
</div>"""
        st.markdown(tbl2 + '</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="summary-tiles">', unsafe_allow_html=True)
        tiles = [
            ("Frozen",    S["frozen"],    "#FDEDEC","#C0392B"),
            ("Escalated", S["escalated"],"#EBF2FB","#1A4A8A"),
            ("Alerted",   S["alerted"],  "#E8F5EE","#1B5E3B"),
            ("False +ve", S["fp"],       "#F5F6F8","#4A5568"),
        ]
        tile_cols = st.columns(4)
        for i, (lbl, val, bg, cl) in enumerate(tiles):
            with tile_cols[i]:
                st.markdown(f"""
<div class="stile">
  <div class="stile-v" style="color:{cl}">{val}</div>
  <div class="stile-l">{lbl}</div>
</div>
""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)  # close margin-top div

    st.markdown('</div>', unsafe_allow_html=True)  # close page

# ─────────────────────────────────────────────
# TAB: ANALYTICS
# ─────────────────────────────────────────────
elif t == "analytics":
    st.markdown('<div class="page">', unsafe_allow_html=True)

    fd = S["feed"]
    tp = S["processed"]; tb = S["blocked"]; tf = S["flagged"]; ts = S["safe"]

    a1, a2 = st.columns(2)

    CHART_LAYOUT = dict(
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="IBM Plex Sans", size=11, color="#4A5568"),
        margin=dict(t=0, b=0, l=0, r=0),
    )

    with a1:
        st.markdown('<div class="ccrd"><div class="ccrd-title">Fraud Detections by Type</div>', unsafe_allow_html=True)
        if fd:
            tc   = Counter(txn["ft"] for txn in fd)
            df_t = pd.DataFrame(list(tc.items()), columns=["T","C"]).sort_values("C")
            CM   = {"Account Takeover":"#C0392B","Velocity Fraud":"#E67E22","Large Amount":"#F39C12","Off-Hours Fraud":"#8E44AD","Anomalous Pattern":"#2980B9"}
            fig  = go.Figure(go.Bar(
                x=df_t["C"], y=df_t["T"], orientation="h",
                marker_color=[CM.get(x,"#2980B9") for x in df_t["T"]],
                marker_opacity=0.85,
                hovertemplate="%{y}: %{x} cases<extra></extra>"))
            fig.update_layout(**CHART_LAYOUT, height=200,
                xaxis=dict(gridcolor="#F3F5F8", tickfont=dict(size=10)),
                yaxis=dict(tickfont=dict(size=10)), bargap=0.3)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        else:
            st.markdown('<div style="height:200px;display:flex;align-items:center;justify-content:center;color:var(--text3);font-size:12px">Start feed to populate</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="ccrd"><div class="ccrd-title">Risk Score Distribution — Fraud Events Only</div>', unsafe_allow_html=True)
        if fd:
            fig2 = go.Figure(go.Histogram(
                x=[txn["score"] for txn in fd], nbinsx=20,
                marker_color="#1B5E3B", marker_opacity=0.75,
                hovertemplate="Score %{x:.2f}: %{y}<extra></extra>"))
            fig2.update_layout(**CHART_LAYOUT, height=170,
                xaxis=dict(gridcolor="#F3F5F8",tickfont=dict(size=10),title="Risk Score"),
                yaxis=dict(gridcolor="#F3F5F8",tickfont=dict(size=10)),bargap=0.08)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
        else:
            st.markdown('<div style="height:170px;display:flex;align-items:center;justify-content:center;color:var(--text3);font-size:12px">Start feed to populate</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with a2:
        st.markdown('<div class="ccrd"><div class="ccrd-title">All Transactions — Outcome Breakdown</div>', unsafe_allow_html=True)
        fig3 = go.Figure(go.Pie(
            labels=["Passed Silently","Flagged","Blocked"],
            values=[max(ts,1), max(tf,1), max(tb,1)],
            hole=0.60,
            marker_colors=["#27AE60","#F39C12","#C0392B"],
            textinfo="percent",
            textfont=dict(size=11, color="white"),
            hovertemplate="%{label}: %{value:,}<extra></extra>",
            showlegend=True))
        fig3.update_layout(
            **CHART_LAYOUT,
            height=240,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2,
                        xanchor="center", x=0.5, font=dict(size=10, color="#4A5568")),
            margin=dict(t=0,b=50,l=0,r=0),
            annotations=[dict(text=f"<b>{tp:,}</b>", x=0.5, y=0.5,
                               font=dict(size=14, color="#0F1923"), showarrow=False)])
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="ccrd"><div class="ccrd-title">Fraud Detections by Hour of Day</div>', unsafe_allow_html=True)
        if fd:
            def parse_hour(s):
                try:
                    h = int(s.split(":")[0])
                    if "PM" in s and h != 12: h += 12
                    if "AM" in s and h == 12: h = 0
                    return h
                except: return 0
            hc = Counter(parse_hour(txn["det"]) for txn in fd)
            hs = sorted(hc.keys())
            fig4 = go.Figure(go.Bar(
                x=hs, y=[hc[h] for h in hs],
                marker_color="#C0392B", marker_opacity=0.8,
                hovertemplate="%{x}:00 — %{y} alerts<extra></extra>"))
            fig4.update_layout(**CHART_LAYOUT, height=170,
                xaxis=dict(tickfont=dict(size=10), gridcolor="#F3F5F8", title="Hour"),
                yaxis=dict(tickfont=dict(size=10), gridcolor="#F3F5F8"), bargap=0.25)
            st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar":False})
        else:
            st.markdown('<div style="height:170px;display:flex;align-items:center;justify-content:center;color:var(--text3);font-size:12px">Start feed to populate</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # SHAP — full width
    st.markdown('<div class="ccrd"><div class="ccrd-title">AI Model Feature Importance — Mean SHAP Values (Why the Model Flags Transactions)</div>', unsafe_allow_html=True)
    shap_d = [
        ("Nighttime activity (11 PM – 5 AM)",               1.644, "#C0392B"),
        ("Off-hours transaction time",                      1.021, "#C0392B"),
        ("Number of transactions on this card today",       0.887, "#E67E22"),
        ("Number of distinct cards linked to this device",  0.754, "#E67E22"),
        ("Number of addresses associated with this card",   0.621, "#E67E22"),
        ("Transaction amount (absolute value)",             0.534, "#1A4A8A"),
        ("Device changed since last transaction",           0.498, "#1A4A8A"),
        ("Transaction amount vs customer 30-day average",   0.412, "#1A4A8A"),
    ]
    fig5 = go.Figure(go.Bar(
        x=[s[1] for s in shap_d],
        y=[s[0] for s in shap_d],
        orientation="h",
        marker_color=[s[2] for s in shap_d],
        marker_opacity=0.85,
        hovertemplate="%{y}: SHAP %{x:.3f}<extra></extra>"))
    fig5.update_layout(
        **CHART_LAYOUT,
        height=260,
        margin=dict(t=0,b=0,l=0,r=16),
        xaxis=dict(
            title="Mean |SHAP value| — higher = stronger influence on the fraud decision",
            gridcolor="#F3F5F8",
            tickfont=dict(size=10),
            title_font=dict(size=10, color="#8A95A3")),
        yaxis=dict(tickfont=dict(size=10), autorange="reversed"),
        bargap=0.3)
    st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # close page

# ─────────────────────────────────────────────
# SIMULATION ENGINE (fragment, never disrupts tabs)
# 17 txns per 2s tick = ~510 txn/min
# Fraud rate: 2–4 per 200 txns (real institutional rate ~1–2%)
# ─────────────────────────────────────────────
@st.fragment(run_every=2)
def sim():
    if not st.session_state["running"]:
        return

    S = st.session_state
    new_fraud = []

    for _ in range(17):
        i  = S["idx"]
        wp = i % 200

        if wp == 0:
            n_fraud = random.randint(2, 4)
            S["fslots"] = sorted(random.sample(range(1, 200), n_fraud))

        is_fraud = (wp in S["fslots"]) and wp > 0
        label    = ("HIGH" if random.random() < 0.60 else "MEDIUM") if is_fraud else "LOW"

        pidx  = random.choice(POOLS[label])
        score = float(scores.loc[pidx, "final_score"])
        amt   = float(X["TransactionAmt"].iloc[pidx])
        if amt < 200:
            amt = round(random.uniform(1200, 180000), 2)
        hour = random.randint(0, 23)

        S["processed"] += 1
        S["idx"]       += 1

        if label in ("HIGH", "MEDIUM"):
            if label == "HIGH": S["blocked"] += 1
            else:               S["flagged"] += 1

            code  = pick_code(label)
            cust  = make_customer()
            hl_map = {
                "ATO": "Login from unrecognised device",
                "VEL": f"{random.randint(4,22)} transactions in rapid succession",
                "AMT": f"{fmt_inr(amt)} — {round(amt/max(cust['avg_txn'],1),1)}x customer average",
                "NGT": f"Transaction at {fmt_time(hour)} — outside normal window",
                "ANO": "Significant deviation from customer profile",
            }
            txn = {
                "cid":      f"FR-{S['ctr']:05d}",
                "code":     code,
                "ft":       FRAUD_TYPES[code],
                "hl":       hl_map[code],
                "reasons":  build_reasons(code, amt, hour, score, cust),
                "amt":      amt,
                "amt_s":    fmt_inr(amt),
                "hour":     hour,
                "det":      ts_now(),
                "label":    label,
                "score":    score,
                "customer": cust,
                "status":   "OPEN",
                "note":     "",
                "assigned": "W. Mautsa",
            }
            S["ctr"] += 1
            new_fraud.append(txn)
        else:
            S["safe"] += 1

    if new_fraud:
        S["feed"].extend(new_fraud)
        S["cases"].extend(new_fraud)
        if len(S["feed"])  > 300: S["feed"]  = S["feed"][-300:]
        if len(S["cases"]) > 50:  S["cases"] = S["cases"][-50:]

    S["tps"] = 510

sim()
