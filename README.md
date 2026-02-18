📊 SmartInvest AI  
### Plateforme intelligente d’aide à la décision boursière  
Projet académique – Business Intelligence & Artificial Intelligence

---

## 🎓 Contexte

Nous sommes 4 étudiantes en 2ème année cycle ingénieur en informatique – spécialité Data Science.

Ce projet est réalisé dans le cadre du module **Business Intelligence & Artificial Intelligence**.

Il s'agit d’un projet semestriel 100% pratique comprenant :
- Business Intelligence
- Data Warehouse
- Machine Learning
- NLP (Sentiment Analysis)
- Développement d’une application

---

## 💡 Objectif du Projet

SmartInvest AI est une plateforme intelligente qui vise à :

- 📈 Analyser les marchés financiers
- 📊 Visualiser les performances et risques
- 🤖 Prédire les tendances à court terme (J+1)
- 🌍 Intégrer des indicateurs macroéconomiques
- 📰 Exploiter le sentiment des news financières
- 🧠 Aider à la prise de décision d’investissement

⚠️ Projet académique – aucune opération de trading réel.

---

## 🏗 Architecture du Projet

Le projet suit une architecture end-to-end :

Data Sources (Yahoo Finance, FRED, Kaggle)
↓
Data Ingestion (Python)
↓
Data Cleaning & Feature Engineering
↓
Data Warehouse (PostgreSQL)
↓
BI Dashboard (Power BI)
↓
Machine Learning & NLP
↓
Application Streamlit


---

## 📊 Sources de Données

1️⃣ **Données Boursières**
- Source : Yahoo Finance (via yfinance)
- Actions : AAPL, MSFT, NVDA, TSLA, AMZN...
- Indices : S&P 500, NASDAQ

2️⃣ **Données Macroéconomiques**
- Source : FRED API
- Taux d’intérêt
- Inflation
- Chômage
- PIB

3️⃣ **News Financières**
- Dataset Kaggle
- Analyse de sentiment (VADER / FinBERT)

---

## 🧰 Stack Technique

- Python 3.10+
- pandas, numpy
- yfinance, fredapi
- scikit-learn, xgboost
- vaderSentiment
- sqlalchemy, psycopg2
- streamlit, plotly
- PostgreSQL
- Power BI
- Git & GitHub

---

## 📁 Structure du Projet

smartinvest-ai/
│
├── data/
├── docs/
│ └── latex/
├── notebooks/
├── sql/
├── src/
│ ├── ingestion/
│ ├── processing/
│ ├── ml/
│ └── app/
│
├── requirements.txt
├── .env.example
└── README.md


---

## ⚙️ Installation (Local)

1️⃣ Cloner le repo :

```bash
git clone https://github.com/<your-repo>/smartinvest-ai.git
cd smartinvest-ai
2️⃣ Créer un environnement virtuel :

python -m venv .venv
.\.venv\Scripts\activate
3️⃣ Installer les dépendances :

pip install -r requirements.txt
👩‍💻 Équipe
Nour Ben Hassine

Hadir Felli

Nouha Briki

Nouhe Ben Khelil

🏆 Objectif Final
Développer un projet professionnel, structuré et compétition-ready pour le Project Gala.
