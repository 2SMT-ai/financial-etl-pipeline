import psycopg2
import pandas as pd
from sqlalchemy import create_engine, text
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)


def get_connection_string() -> str:
    """Construit la chaîne de connexion PostgreSQL depuis les variables d'environnement."""
    user     = os.getenv("POSTGRES_USER", "etl_user")
    password = os.getenv("POSTGRES_PASSWORD", "etl_password")
    host     = os.getenv("POSTGRES_HOST", "localhost")
    port     = os.getenv("POSTGRES_PORT", "5432")
    db       = os.getenv("POSTGRES_DB", "financial_db")
    
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


def get_engine():
    """Crée et retourne un moteur SQLAlchemy."""
    conn_str = get_connection_string()
    engine = create_engine(conn_str)
    logger.info("✅ Connexion PostgreSQL établie")
    return engine


def load_raw_data(df: pd.DataFrame, engine) -> int:
    """
    Charge les données brutes dans la table raw_stock_data.
    Utilise UPSERT pour éviter les doublons.

    Args:
        df: DataFrame brut (issu de extract.py)
        engine: Moteur SQLAlchemy

    Returns:
        Nombre de lignes insérées/mises à jour
    """
    logger.info(f"📤 Chargement de {len(df)} lignes dans raw_stock_data...")

    try:
        with engine.connect() as conn:
            inserted = 0
            for _, row in df.iterrows():
                sql = text("""
                    INSERT INTO raw_stock_data
                        (ticker, date, open, high, low, close, volume)
                    VALUES
                        (:ticker, :date, :open, :high, :low, :close, :volume)
                    ON CONFLICT (ticker, date)
                    DO UPDATE SET
                        open   = EXCLUDED.open,
                        high   = EXCLUDED.high,
                        low    = EXCLUDED.low,
                        close  = EXCLUDED.close,
                        volume = EXCLUDED.volume
                """)
                conn.execute(sql, {
                    "ticker": row["ticker"],
                    "date"  : row["date"],
                    "open"  : row["open"],
                    "high"  : row["high"],
                    "low"   : row["low"],
                    "close" : row["close"],
                    "volume": row["volume"],
                })
                inserted += 1
            conn.commit()

        logger.info(f"✅ {inserted} lignes chargées dans raw_stock_data")
        return inserted

    except Exception as e:
        logger.error(f"❌ Erreur chargement raw : {e}")
        raise


def load_transformed_data(df: pd.DataFrame, engine) -> int:
    """
    Charge les données transformées dans transformed_stock_data.
    Utilise UPSERT pour éviter les doublons.

    Args:
        df: DataFrame transformé (issu de transform.py)
        engine: Moteur SQLAlchemy

    Returns:
        Nombre de lignes insérées/mises à jour
    """
    logger.info(f"📤 Chargement de {len(df)} lignes dans transformed_stock_data...")

    try:
        with engine.connect() as conn:
            inserted = 0
            for _, row in df.iterrows():
                sql = text("""
                    INSERT INTO transformed_stock_data
                        (ticker, date, close, daily_return, ma_7, ma_30, volatility_30)
                    VALUES
                        (:ticker, :date, :close, :daily_return, :ma_7, :ma_30, :volatility_30)
                    ON CONFLICT (ticker, date)
                    DO UPDATE SET
                        close         = EXCLUDED.close,
                        daily_return  = EXCLUDED.daily_return,
                        ma_7          = EXCLUDED.ma_7,
                        ma_30         = EXCLUDED.ma_30,
                        volatility_30 = EXCLUDED.volatility_30
                """)
                conn.execute(sql, {
                    "ticker"       : row["ticker"],
                    "date"         : row["date"],
                    "close"        : row["close"],
                    "daily_return" : None if pd.isna(row["daily_return"]) else row["daily_return"],
                    "ma_7"         : None if pd.isna(row["ma_7"])         else row["ma_7"],
                    "ma_30"        : None if pd.isna(row["ma_30"])        else row["ma_30"],
                    "volatility_30": None if pd.isna(row["volatility_30"])else row["volatility_30"],
                })
                inserted += 1
            conn.commit()

        logger.info(f"✅ {inserted} lignes chargées dans transformed_stock_data")
        return inserted

    except Exception as e:
        logger.error(f"❌ Erreur chargement transformed : {e}")
        raise


def verify_load(engine, ticker: str) -> None:
    """Vérifie les données chargées dans les deux tables."""
    logger.info("🔍 Vérification des données chargées...")

    with engine.connect() as conn:
        # Vérifier raw
        result = conn.execute(text(
            "SELECT COUNT(*) FROM raw_stock_data WHERE ticker = :ticker"
        ), {"ticker": ticker})
        count_raw = result.scalar()

        # Vérifier transformed
        result = conn.execute(text(
            "SELECT COUNT(*) FROM transformed_stock_data WHERE ticker = :ticker"
        ), {"ticker": ticker})
        count_transformed = result.scalar()

        # Dernière ligne transformée
        result = conn.execute(text("""
            SELECT date, close, daily_return, ma_7, ma_30
            FROM transformed_stock_data
            WHERE ticker = :ticker
            ORDER BY date DESC
            LIMIT 3
        """), {"ticker": ticker})
        rows = result.fetchall()

    logger.info(f"✅ raw_stock_data        : {count_raw} lignes")
    logger.info(f"✅ transformed_stock_data: {count_transformed} lignes")
    logger.info("📊 Dernières lignes transformées :")
    for row in rows:
        logger.info(f"   {row}")


if __name__ == "__main__":
    from extract import extract_stock_data, validate_data
    from transform import transform_stock_data

    # Extraction
    df_raw = extract_stock_data("GOOGL", "2y")
    validate_data(df_raw)

    # Transformation
    df_transformed = transform_stock_data(df_raw)

    # Connexion
    engine = get_engine()

    # Chargement
    load_raw_data(df_raw, engine)
    load_transformed_data(df_transformed, engine)

    # Vérification
    verify_load(engine, "GOOGL")