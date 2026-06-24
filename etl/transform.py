import pandas as pd
import numpy as np
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)


def transform_stock_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applique les transformations et calcule les KPIs financiers.

    Args:
        df: DataFrame brut issu de l'extraction

    Returns:
        DataFrame enrichi avec les KPIs
    """
    logger.info("⚙️ Début de la transformation des données...")

    df = df.copy()
    df = df.sort_values("date").reset_index(drop=True)

    # 1. Rendement journalier (%)
    df["daily_return"] = df["close"].pct_change() * 100
    logger.info("✅ Rendement journalier calculé")

    # 2. Moyenne mobile 7 jours
    df["ma_7"] = df["close"].rolling(window=7).mean()
    logger.info("✅ Moyenne mobile 7 jours calculée")

    # 3. Moyenne mobile 30 jours
    df["ma_30"] = df["close"].rolling(window=30).mean()
    logger.info("✅ Moyenne mobile 30 jours calculée")

    # 4. Volatilité 30 jours (écart-type des rendements)
    df["volatility_30"] = df["daily_return"].rolling(window=30).std()
    logger.info("✅ Volatilité 30 jours calculée")

    # 5. Arrondir les valeurs numériques
    numeric_cols = ["open", "high", "low", "close",
                    "daily_return", "ma_7", "ma_30", "volatility_30"]
    df[numeric_cols] = df[numeric_cols].round(4)

    # 6. Garder uniquement les colonnes pour la table transformée
    df_transformed = df[[
        "ticker", "date", "close",
        "daily_return", "ma_7", "ma_30", "volatility_30"
    ]]

    logger.info(f"✅ Transformation terminée — {len(df_transformed)} lignes")
    logger.info(f"📊 Aperçu des KPIs :\n{df_transformed.tail(5).to_string()}")

    return df_transformed


def get_summary_stats(df: pd.DataFrame) -> dict:
    """
    Calcule des statistiques résumées sur les données transformées.

    Args:
        df: DataFrame transformé

    Returns:
        Dictionnaire de statistiques
    """
    stats = {
        "ticker": df["ticker"].iloc[0],
        "nb_jours": len(df),
        "prix_actuel": df["close"].iloc[-1],
        "prix_min": df["close"].min(),
        "prix_max": df["close"].max(),
        "rendement_moyen": round(df["daily_return"].mean(), 4),
        "volatilite_moyenne": round(df["volatility_30"].mean(), 4),
        "date_debut": str(df["date"].min()),
        "date_fin": str(df["date"].max()),
    }

    logger.info(f"\n📈 Statistiques pour {stats['ticker']} :")
    for k, v in stats.items():
        logger.info(f"   {k} : {v}")

    return stats


if __name__ == "__main__":
    # Test avec l'extraction
    from extract import extract_stock_data, validate_data

    df_raw = extract_stock_data("GOOGL", "2y")

    if validate_data(df_raw):
        df_transformed = transform_stock_data(df_raw)
        stats = get_summary_stats(df_transformed)

        print("\n--- Aperçu données transformées ---")
        print(df_transformed.head(10).to_string())
        print(f"\nShape : {df_transformed.shape}")
        print(f"\nValeurs nulles :\n{df_transformed.isnull().sum()}")