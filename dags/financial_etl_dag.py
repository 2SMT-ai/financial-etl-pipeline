from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, '/opt/airflow/etl')

from extract import extract_stock_data, validate_data
from transform import transform_stock_data
from load import get_engine, load_raw_data, load_transformed_data, verify_load

# Configuration par défaut
default_args = {
    'owner': '2SMT-ai',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Paramètres ETL
TICKER = os.getenv('TICKER', 'GOOGL')
PERIOD = os.getenv('PERIOD', '2y')


def task_extract(**context):
    """Tâche d'extraction des données Yahoo Finance."""
    df = extract_stock_data(TICKER, PERIOD)

    if not validate_data(df):
        raise ValueError("Validation des données échouée !")

    # Sauvegarder pour la tâche suivante via XCom
    context['ti'].xcom_push(key='raw_data', value=df.to_json())
    return f"✅ {len(df)} lignes extraites pour {TICKER}"


def task_transform(**context):
    """Tâche de transformation et calcul des KPIs."""
    import pandas as pd

    # Récupérer les données de la tâche précédente
    raw_json = context['ti'].xcom_pull(key='raw_data', task_ids='extract')
    df_raw = pd.read_json(raw_json)
    df_raw['date'] = pd.to_datetime(df_raw['date']).dt.date

    df_transformed = transform_stock_data(df_raw)

    # Passer au chargement
    context['ti'].xcom_push(key='raw_data', value=df_raw.to_json())
    context['ti'].xcom_push(key='transformed_data', value=df_transformed.to_json())
    return f"✅ Transformation terminée — {len(df_transformed)} lignes"


def task_load(**context):
    """Tâche de chargement dans PostgreSQL."""
    import pandas as pd

    # Récupérer les deux DataFrames
    raw_json         = context['ti'].xcom_pull(key='raw_data',         task_ids='transform')
    transformed_json = context['ti'].xcom_pull(key='transformed_data', task_ids='transform')

    df_raw         = pd.read_json(raw_json)
    df_transformed = pd.read_json(transformed_json)

    df_raw['date']         = pd.to_datetime(df_raw['date']).dt.date
    df_transformed['date'] = pd.to_datetime(df_transformed['date']).dt.date

    engine = get_engine()
    load_raw_data(df_raw, engine)
    load_transformed_data(df_transformed, engine)
    verify_load(engine, TICKER)

    return f"✅ Chargement terminé — {len(df_raw)} lignes raw, {len(df_transformed)} lignes transformées"


def task_verify(**context):
    """Tâche de vérification finale."""
    engine = get_engine()
    verify_load(engine, TICKER)
    return "✅ Vérification finale réussie"


# Définition du DAG
with DAG(
    dag_id='financial_etl_pipeline',
    default_args=default_args,
    description='Pipeline ETL pour les données financières GOOGL',
    schedule_interval='0 18 * * 1-5',  # Tous les jours de semaine à 18h
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['etl', 'finance', 'googl'],
) as dag:

    extract = PythonOperator(
        task_id='extract',
        python_callable=task_extract,
    )

    transform = PythonOperator(
        task_id='transform',
        python_callable=task_transform,
    )

    load = PythonOperator(
        task_id='load',
        python_callable=task_load,
    )

    verify = PythonOperator(
        task_id='verify',
        python_callable=task_verify,
    )

    # Définir l'ordre d'exécution
    extract >> transform >> load >> verify
    
