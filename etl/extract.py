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
    Extrait les données historiques d'une action depuis Yahoo Finance.

    Args:
        ticker: Symbole boursier (ex: 'GOOGL')
        period: Période d'historique (ex: '2y', '1y', '6mo')

    Returns:
        DataFrame avec les colonnes OHLCV
    """
    logger.info(f"📥 Extraction des données pour {ticker} sur {period}...")

    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)

        if df.empty:
            raise ValueError(f"Aucune donnée retournée pour {ticker}")

        # Nettoyage de base
        df = df.reset_index()
        df.columns = [col.lower() for col in df.columns]

        # Garder uniquement les colonnes utiles
        df = df[["date", "open", "high", "low", "close", "volume"]]

        # Nettoyer la colonne date (supprimer timezone)
        df["date"] = pd.to_datetime(df["date"]).dt.date

        # Ajouter le ticker
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