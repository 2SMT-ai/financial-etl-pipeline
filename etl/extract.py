import yfinance as yf
import pandas as pd
from datetime import datetime
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)


def extract_stock_data(ticker: str, period: str = "2y") -> pd.DataFrame:
    """
    Extrait les données historiques d'une action.
    Priorité : fichier CSV local → Yahoo Finance
    """
    logger.info(f"📥 Extraction des données pour {ticker} sur {period}...")

    try:
        # Mode Docker — lire depuis CSV si disponible
        import os
        csv_path = f"/opt/airflow/data/{ticker}_raw.csv"
        local_csv = f"data/{ticker}_raw.csv"

        if os.path.exists(csv_path):
            logger.info(f"📂 Lecture depuis CSV Docker : {csv_path}")
            df = pd.read_csv(csv_path)
            df["date"] = pd.to_datetime(df["date"]).dt.date
            logger.info(f"✅ {len(df)} lignes lues depuis CSV")
            return df

        elif os.path.exists(local_csv):
            logger.info(f"📂 Lecture depuis CSV local : {local_csv}")
            df = pd.read_csv(local_csv)
            df["date"] = pd.to_datetime(df["date"]).dt.date
            logger.info(f"✅ {len(df)} lignes lues depuis CSV")
            return df

        # Fallback — Yahoo Finance
        import requests
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        stock = yf.Ticker(ticker, session=session)
        df = stock.history(period=period)

        if df.empty:
            raise ValueError(f"Aucune donnée retournée pour {ticker}")

        df = df.reset_index()
        df.columns = [col.lower() for col in df.columns]
        df = df[["date", "open", "high", "low", "close", "volume"]]
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df.insert(0, "ticker", ticker)

        logger.info(f"✅ {len(df)} lignes extraites pour {ticker}")
        logger.info(f"📅 Période : {df['date'].min()} → {df['date'].max()}")
        return df

    except Exception as e:
        logger.error(f"❌ Erreur lors de l'extraction : {e}")
        raise


def validate_data(df: pd.DataFrame) -> bool:
    """
    Valide les données extraites avant de les passer à la transformation.

    Args:
        df: DataFrame extrait

    Returns:
        True si les données sont valides
    """
    logger.info("🔍 Validation des données...")

    # Vérifier que le DataFrame n'est pas vide
    if df.empty:
        logger.error("❌ DataFrame vide !")
        return False

    # Vérifier les colonnes attendues
    expected_cols = ["ticker", "date", "open", "high", "low", "close", "volume"]
    missing = [col for col in expected_cols if col not in df.columns]
    if missing:
        logger.error(f"❌ Colonnes manquantes : {missing}")
        return False

    # Vérifier les valeurs nulles sur les colonnes critiques
    nulls = df[["close", "volume"]].isnull().sum()
    if nulls.any():
        logger.warning(f"⚠️ Valeurs nulles détectées : \n{nulls}")

    # Vérifier que close > 0
    if (df["close"] <= 0).any():
        logger.error("❌ Des valeurs de clôture négatives ou nulles détectées !")
        return False

    logger.info(f"✅ Validation réussie — {len(df)} lignes valides")
    return True


if __name__ == "__main__":
    # Test rapide
    df = extract_stock_data("GOOGL", "2y")
    print(df.head(10))
    print(f"\nShape : {df.shape}")
    print(f"\nTypes :\n{df.dtypes}")
    is_valid = validate_data(df)
    print(f"\nDonnées valides : {is_valid}")