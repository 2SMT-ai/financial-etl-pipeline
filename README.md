# 📊 Financial ETL Pipeline

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Airflow](https://img.shields.io/badge/Airflow-2.9.1-red)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![Status](https://img.shields.io/badge/Status-In%20Progress-yellow)

> Pipeline ETL automatisé pour l'analyse de données financières (Google/GOOGL)
> avec Apache Airflow, PostgreSQL et un dashboard Plotly Dash.

## 🏗️ Architecture

## ⚙️ Stack technique
| Couche | Technologie |
|---|---|
| Extraction | yfinance |
| Transformation | Pandas, NumPy |
| Chargement | PostgreSQL 15 |
| Orchestration | Apache Airflow 2.9.1 |
| Visualisation | Plotly Dash |
| Conteneurisation | Docker Compose |

## 🚀 Lancer le projet

```bash
# 1. Cloner le repo
git clone https://github.com/2SMT-ai/financial-etl-pipeline.git
cd financial-etl-pipeline

# 2. Configurer l'environnement
cp .env.example .env

# 3. Lancer les services
docker compose up airflow-init
docker compose up -d

# 4. Accéder aux interfaces
# Airflow   → http://localhost:8080
# Dashboard → http://localhost:8050
```

## 📁 Structure du projet
...

## 👤 Auteur
**Serigne Saliou Mbacke Thiam** — [@2SMT-ai](https://github.com/2SMT-ai)