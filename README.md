# 📊 Financial ETL Pipeline

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Airflow](https://img.shields.io/badge/Apache%20Airflow-2.7.3-017CEE?logo=apacheairflow)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![Plotly](https://img.shields.io/badge/Plotly%20Dash-2.17-3F4F75?logo=plotly)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen)

> Pipeline ETL automatisé pour l'analyse de données financières de Google (GOOGL) sur 2 ans.  
> Extraction via Yahoo Finance, transformation avec Pandas, chargement dans PostgreSQL,  
> orchestration avec Apache Airflow et visualisation avec un dashboard Plotly Dash interactif.

---

## 🏗️ Architecture du projet

```
Yahoo Finance API
       │
       ▼
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│   EXTRACT   │────▶│    TRANSFORM     │────▶│     LOAD     │
│  yfinance   │     │ Pandas + KPIs    │     │  PostgreSQL  │
│  501 lignes │     │ MA7, MA30, Vol.  │     │  2 tables    │
└─────────────┘     └──────────────────┘     └──────────────┘
                              │
                    ┌─────────────────┐
                    │  Apache Airflow  │
                    │  Orchestration  │
                    │  DAG quotidien  │
                    └─────────────────┘
                              │
                    ┌─────────────────┐
                    │  Plotly Dash    │
                    │  Dashboard      │
                    │  Interactif     │
                    └─────────────────┘
```

---

## ⚙️ Stack technique

| Couche | Technologie | Version |
|---|---|---|
| Extraction | yfinance | 0.2.36 |
| Transformation | Pandas, NumPy | 2.0.3, 1.24.4 |
| Chargement | PostgreSQL | 15 |
| ORM | SQLAlchemy + psycopg2 | 1.4.52 |
| Orchestration | Apache Airflow | 2.7.3 |
| Visualisation | Plotly Dash | 2.17.1 |
| Conteneurisation | Docker Compose | v3.8 |
| Versioning | Git + GitHub | — |

---

## 📁 Structure du projet

```
financial-etl-pipeline/
│
├── dags/
│   └── financial_etl_dag.py       # DAG Airflow (4 tâches)
│
├── etl/
│   ├── __init__.py
│   ├── extract.py                  # Extraction yfinance + fallback CSV
│   ├── transform.py                # Calcul KPIs financiers
│   └── load.py                     # Chargement PostgreSQL (UPSERT)
│
├── dashboard/
│   └── app.py                      # Dashboard Plotly Dash
│
├── sql/
│   └── init.sql                    # Création des tables PostgreSQL
│
├── data/                           # Données CSV (non versionnées)
│   └── GOOGL_raw.csv
│
├── logs/                           # Logs Airflow
├── plugins/                        # Plugins Airflow
│
├── .env                            # Variables d'environnement (non versionné)
├── .env.example                    # Template .env
├── .gitignore
├── docker-compose.yml
├── requirements.txt                # Dépendances Python (local)
├── requirements-airflow.txt        # Dépendances Python (Airflow/Docker)
└── README.md
```

---

## 📊 KPIs calculés

| KPI | Description | Formule |
|---|---|---|
| `daily_return` | Rendement journalier | `(close_t - close_t-1) / close_t-1 × 100` |
| `ma_7` | Moyenne mobile 7 jours | `mean(close, window=7)` |
| `ma_30` | Moyenne mobile 30 jours | `mean(close, window=30)` |
| `volatility_30` | Volatilité 30 jours | `std(daily_return, window=30)` |

---

## 🗄️ Schéma de base de données

```sql
-- Données brutes
CREATE TABLE raw_stock_data (
    id          SERIAL PRIMARY KEY,
    ticker      VARCHAR(10),
    date        DATE,
    open        NUMERIC(12, 4),
    high        NUMERIC(12, 4),
    low         NUMERIC(12, 4),
    close       NUMERIC(12, 4),
    volume      BIGINT,
    loaded_at   TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker, date)
);

-- Données transformées
CREATE TABLE transformed_stock_data (
    id              SERIAL PRIMARY KEY,
    ticker          VARCHAR(10),
    date            DATE,
    close           NUMERIC(12, 4),
    daily_return    NUMERIC(8, 4),
    ma_7            NUMERIC(12, 4),
    ma_30           NUMERIC(12, 4),
    volatility_30   NUMERIC(8, 4),
    processed_at    TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker, date)
);
```

---

## 🚀 Lancer le projet

### Prérequis
- Docker & Docker Compose
- Python 3.11+
- Git

### Installation

```bash
# 1. Cloner le repo
git clone https://github.com/2SMT-ai/financial-etl-pipeline.git
cd financial-etl-pipeline

# 2. Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos paramètres

# 3. Créer le venv et installer les dépendances
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Générer les données CSV (extraction locale)
python3 -c "
from etl.extract import extract_stock_data
df = extract_stock_data('GOOGL', '2y')
df.to_csv('data/GOOGL_raw.csv', index=False)
print(f'✅ {len(df)} lignes générées')
"

# 5. Lancer PostgreSQL
docker compose up -d postgres

# 6. Initialiser Airflow
docker compose up airflow-init

# 7. Lancer tous les services
docker compose up -d airflow-webserver airflow-scheduler

# 8. Lancer le dashboard
python dashboard/app.py
```

### Accès aux interfaces

| Interface | URL | Identifiants |
|---|---|---|
| Airflow | http://localhost:8080 | admin / admin123 |
| Dashboard | http://localhost:8050 | — |
| PostgreSQL | localhost:5433 | etl_user / etl_password |

---

## 🔄 DAG Airflow

Le DAG `financial_etl_pipeline` s'exécute automatiquement du lundi au vendredi à 18h00 UTC.

```
extract ──▶ transform ──▶ load ──▶ verify
```

| Tâche | Description |
|---|---|
| `extract` | Lit les données depuis CSV ou Yahoo Finance |
| `transform` | Calcule les KPIs financiers |
| `load` | Charge dans PostgreSQL avec UPSERT |
| `verify` | Vérifie l'intégrité des données chargées |

---

## 📈 Résultats

Sur la période **juin 2024 → juin 2026** :

| Métrique | Valeur |
|---|---|
| Lignes extraites | 501 |
| Prix min | $144.11 |
| Prix max | $402.38 |
| Rendement moyen | +0.15%/jour |
| Volatilité moyenne | 1.89% |
| Performance 2 ans | +140% 🚀 |

---

## 🌿 Git Flow utilisé

```
main          ← code stable, production-ready
│
└── develop   ← intégration
      ├── feature/extract
      ├── feature/transform
      ├── feature/load
      ├── feature/airflow-dag
      └── feature/dashboard
```

### Convention de commits

```
feat(scope): description en français
fix(scope): description en français
chore(scope): description en français
docs(scope): description en français
```

---

## 👤 Auteur

**Serigne Saliou Mbacke Thiam**  
Étudiant en Big Data — Dakar Institute of Technology (DIT)  
Promotion 2SMT-ai

[![GitHub](https://img.shields.io/badge/GitHub-2SMT--ai-181717?logo=github)](https://github.com/2SMT-ai)

---

## 📄 Licence

MIT License — Libre d'utilisation à des fins éducatives et professionnelles.
