# 🛡 ATO Shield
AI-Powered Account Takeover Fraud Detection for Mobile Money Platforms

![Python](https://img.shields.io/badge/Python-3.14-blue)
![XGBoost](https://img.shields.io/badge/XGBoost-3.2.0-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-1.55.0-red)
![SHAP](https://img.shields.io/badge/SHAP-0.51.0-green)

---

## 📋 Project Overview
ATO Shield is an AI system that automatically detects Account Takeover (ATO)
fraud in mobile money transactions. It is built as a Paytm-style mobile web app
that gives customers full visibility into their account security in one place.

---

## 📱 App Features
The app has two tabs:

**Tab 1 — Home**
- Paytm-style wallet balance card
- Send Money quick actions
- Live fraud alert with block/confirm buttons
- Recent transactions with risk badges

**Tab 2 — My Security**
- Summary: total transactions, blocked, flagged
- Blocked transactions list with reasons
- Risk breakdown (HIGH / MEDIUM / LOW)
- Top fraud signals in plain English
- Suspicious activity timeline

---

## 🏗 Project Structure
```
ato-fraud-detection/
  ├── data/
  │   ├── raw/                         # IEEE-CIS dataset (not on GitHub)
  │   └── processed/                   # Cleaned & balanced data (not on GitHub)
  ├── src/
  │   ├── preprocessing/
  │   │   └── pipeline.py              # Data cleaning + SMOTE
  │   ├── models/
  │   │   ├── xgboost_model.py         # Supervised fraud detector
  │   │   ├── isolation_forest.py      # Anomaly detector
  │   │   └── saved/                   # Trained .pkl model files
  │   ├── scoring/
  │   │   └── risk_scorer.py           # 70/30 score fusion
  │   └── explainability/
  │       └── shap_explainer.py        # SHAP feature importance
  ├── app/
  │   └── customer.py                  # Full Paytm-style customer app
  ├── requirements.txt
  └── README.md
```

---

## 🤖 Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.14 |
| Supervised Model | XGBoost |
| Unsupervised Model | Isolation Forest |
| Data Balancing | SMOTE |
| Explainability | SHAP |
| Frontend | Streamlit |
| Charts | Plotly |
| Dataset | IEEE-CIS Fraud Detection (Kaggle) |
| Deployment | Streamlit Cloud |

---

## 📊 Model Results

| Model | Precision | Recall | F1-Score | ROC-AUC |
|-------|-----------|--------|----------|---------|
| Isolation Forest only | 0.060 | 0.060 | 0.060 | 0.627 |
| XGBoost only | 0.960 | 0.909 | 0.934 | 0.982 |
| **XGBoost + Isolation Forest** | **0.960** | **0.909** | **0.934** | **0.982** |

---

## 🚀 How to Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/WAYNEMAUTSA/ato-fraud-detection.git
cd ato-fraud-detection
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Download the dataset
- Go to kaggle.com/competitions/ieee-fraud-detection
- Download train_transaction.csv and place in data/raw/

### 4. Run preprocessing
```bash
python src/preprocessing/pipeline.py
```

### 5. Train the models
```bash
python src/models/xgboost_model.py
python src/models/isolation_forest.py
python src/scoring/risk_scorer.py
```

### 6. Run the app
```bash
python -m streamlit run app/customer.py
```

---

## 📁 Dataset
- **Name:** IEEE-CIS Fraud Detection Dataset
- **Source:** Kaggle — kaggle.com/competitions/ieee-fraud-detection
- **Size:** 590,540 transactions, 394 features
- **Fraud rate:** 3.5%

---

## 👨‍🎓 Academic Information
- **Project:** AI-Powered ATO Fraud Detection for Mobile Money
- **Models:** XGBoost + Isolation Forest hybrid
- **Explainability:** SHAP
- **References:** Sarna et al. (2025), ASEP Framework (2025)