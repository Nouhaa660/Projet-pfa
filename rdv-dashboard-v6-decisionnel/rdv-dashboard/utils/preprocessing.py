"""
Fonctions de préparation des données, partagées entre les deux modèles.

IMPORTANT : ces fonctions doivent rester IDENTIQUES à celles utilisées dans
les notebooks d'entraînement (prediction.ML et nlp_bertopic_ameliore.ipynb).
Toute différence ici introduit un décalage entraînement / inférence.
"""

from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Feature engineering pour le modèle XGBoost
# ---------------------------------------------------------------------------

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "revenu" in df.columns:
        df["revenu"] = pd.to_numeric(df["revenu"], errors="coerce")
    if "credits_en_cours" in df.columns:
        df["credits_en_cours"] = pd.to_numeric(df["credits_en_cours"], errors="coerce")

    df["conso_m2"] = (
        df["facture_annuelle"] / df["superficie_habitable"].replace(0, np.nan)
    )
    df["conso_m2"] = df["conso_m2"].fillna(0)

    df["date_appel"] = pd.to_datetime(df["date_appel"], errors="coerce")
    df["date_rdv"] = pd.to_datetime(df["date_rdv"], errors="coerce")

    df["delai_appel_rdv_jours"] = (
        df["date_rdv"].dt.normalize() - df["date_appel"].dt.normalize()
    ).dt.days

    df["jour_semaine_rdv"] = df["date_rdv"].dt.dayofweek
    df["est_fin_mois"] = df["date_rdv"].dt.is_month_end.astype(float)

    return df


XGB_FEATURE_COLUMNS = [
    "agent", "confirmateur", "enfants_a_charge", "type_fiche",
    "credits_en_cours", "situation_professionnelle_mr", "situation_professionnelle_mme",
    "revenu", "mode_chauffage", "facture_annuelle", "superficie_habitable",
    "conso_m2", "delai_appel_rdv_jours", "jour_semaine_rdv", "est_fin_mois",
]

# ---------------------------------------------------------------------------
# Nettoyage des noms d'agents (hors artefacts Excel / vides)
# ---------------------------------------------------------------------------

_INVALID_AGENT_PATTERNS = (
    r"^[\s\-–—_/.]*$",
    r"^feuille\b",
    r"^sheet\b",
    r"^onglet\b",
    r"^nan$",
    r"^none$",
    r"^null$",
    r"^n/?a$",
    r"^inconnu",
    r"^non\s*renseign",
    r"^test\b",
)


def is_valid_agent_name(name) -> bool:
    """Exclut FEUILLE 16, tirets, vides, etc."""
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return False
    text = str(name).strip()
    if len(text) < 2:
        return False
    low = text.lower()
    for pat in _INVALID_AGENT_PATTERNS:
        if re.search(pat, low, flags=re.IGNORECASE):
            return False
    # Uniquement chiffres / ponctuation
    if re.fullmatch(r"[\d\s\-_.]+", text):
        return False
    return True


def filtrer_agents_valides(df: pd.DataFrame, colonne: str = "agent") -> pd.DataFrame:
    """Retire les lignes dont le nom d'agent n'est pas exploitable."""
    if df is None or df.empty or colonne not in df.columns:
        return df
    d = df.copy()
    d[colonne] = d[colonne].astype(str).str.strip()
    mask = d[colonne].map(is_valid_agent_name)
    return d.loc[mask].copy()


# ---------------------------------------------------------------------------
# Nettoyage de texte pour BERTopic
# Aligné sur nlp_bertopic_ameliore.ipynb (clean_comment)
# ---------------------------------------------------------------------------

WORDS_TO_REMOVE = {
    "mr",
    "mme",
    "monsieur",
    "madame",
    "rdv",
    "confirmé",
    "confirme",
    "pv",
    "pac",
    "chauffage",
    "facture",
    "client",
}

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", flags=re.IGNORECASE)
NON_LETTER_PATTERN = re.compile(r"[^a-zàâäéèêëïîôöùûüçœ0-9' -]+", flags=re.IGNORECASE)
MULTISPACE_PATTERN = re.compile(r"\s+")


def _remove_accents_for_matching(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def clean_comment(text: object) -> str:
    """Nettoyage léger orienté NLP — identique au notebook BERTopic."""
    if pd.isna(text):
        return ""

    text = str(text).strip().lower()
    if not text:
        return ""

    text = URL_PATTERN.sub(" ", text)
    text = text.replace("'", "'").replace("'", "'")
    text = NON_LETTER_PATTERN.sub(" ", text)
    text = MULTISPACE_PATTERN.sub(" ", text).strip()

    tokens = []
    for token in text.split():
        token_for_matching = _remove_accents_for_matching(token)
        if token_for_matching in WORDS_TO_REMOVE:
            continue
        tokens.append(token)

    return " ".join(tokens)


def nettoyer_leger(txt) -> str:
    """Alias conservé pour compatibilité avec l'ancien code."""
    return clean_comment(txt)
