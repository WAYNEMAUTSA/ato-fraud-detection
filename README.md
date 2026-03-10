# 🛡 ATO Shield
AI-Powered Account Takeover Fraud Detection for Mobile Money Platforms

![Python](https://img.shields.io/badge/Python-3.11-blue)
![XGBoost](https://img.shields.io/badge/XGBoost-3.2.0-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-1.55.0-red)
![SHAP](https://img.shields.io/badge/SHAP-0.51.0-green)

---

## 📋 Project Overview
This project builds an AI system that automatically detects Account Takeover (ATO) 
fraud in mobile money transactions. It uses two AI models working together and 
explains every decision in plain language.

The system has two interfaces:
- 👤 **Customer View** — Paytm-style UI showing alerts on suspicious transactions
- 📊 **Analyst Dashboard** — Full fraud investigation dashboard with SHAP explanations

---

## 🏗 Project Structure
```
ato-fraud-detection/
  ├── data/
  │   ├── raw/                        # IEEE-CIS dataset (not on GitHub)
  │   └── processed/                  # Cleaned & balanced data (not on GitHub)
  ├── src/
  │   ├── preprocessing/
  │   │   └── pipeline.py             # Step 2: data cleaning + SMOTE
  │   ├── models/
  │   │   ├── xgboost_model.py        # Step 3: supervised fraud detector
  │   │   ├── isolation_forest.py     # Step 4: anomaly detector
  │   │   └── saved/                  # Trained .pkl model files
  │   ├── scoring/
  │   │   └── risk_scorer.py          # Step 5: 70/30 score fusion
  │   └── explainability/
  │       └── shap_explainer.py       # Step 6: SHAP feature importance
  ├── app/
  │   ├── home.py                     # Landing page
  │   ├── customer.py                 # Customer alert UI (Paytm style)
  │   └── dashboard.py                # Analyst dashboard
  ├── requirements.txt
  └── README.md
```

---

## 🤖 Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
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
| Logistic Regression | 0.71 | 0.62 | 0.66 | 0.84 |
| Random Forest | 0.84 | 0.79 | 0.81 | 0.91 |
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
- Download train_transaction.csv and train_identity.csv
- Place them in data/raw/

### 4. Run preprocessing
```bash
python src/preprocessing/pipeline.py
```

### 5. Train the models
```bash
python src/models/xgboost_model.py
python src/models/isolation_forest.py
```

### 6. Run the app
```bash
streamlit run app/home.py
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
- **Dataset:** IEEE-CIS Fraud Detection (Vesta Corporation)
- **References:** Sarna et al. (2025), ASEP Framework (2025)