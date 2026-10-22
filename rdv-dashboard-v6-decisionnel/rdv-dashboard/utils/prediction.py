"""
Prédiction ML (XGBoost) + classification des motifs d'annulation (BERTopic).

Chargement NLP aligné sur nlp_bertopic_ameliore.ipynb :
- modèle sauvegardé en safetensors (ctfidf + topic_embeddings)
- embedding SentenceTransformer rechargé à l'inférence
  (paraphrase-multilingual-MiniLM-L12-v2)
"""

from __future__ import annotations

import json
import os

import joblib
import pandas as pd
import streamlit as st

from utils.preprocessing import engineer_features, clean_comment

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
XGB_BUNDLE_PATH = os.path.join(MODELS_DIR, "xgb_prediction_bundle.pkl")
BERTOPIC_PATH = os.path.join(MODELS_DIR, "bertopic_motifs")
NOMS_MOTIFS_PATH = os.path.join(MODELS_DIR, "noms_motifs.json")
TOPICS_PATH = os.path.join(BERTOPIC_PATH, "topics.json")
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


# ---------------------------------------------------------------------------
# Chargement (mis en cache)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner="Chargement du modèle de prédiction...")
def load_xgb_bundle() -> dict:
    if not os.path.exists(XGB_BUNDLE_PATH):
        raise FileNotFoundError(
            f"Modèle XGBoost introuvable : {XGB_BUNDLE_PATH}."
        )
    return joblib.load(XGB_BUNDLE_PATH)


@st.cache_resource(show_spinner="Chargement du modèle d'analyse de motifs...")
def load_bertopic_model():
    """
    Charge le modèle BERTopic exporté en safetensors.

    L'embedding n'est pas toujours sérialisé dans le dossier : on le
    réinjecte explicitement, comme prévu par le notebook.
    """
    from bertopic import BERTopic
    from sentence_transformers import SentenceTransformer

    if not os.path.isdir(BERTOPIC_PATH):
        raise FileNotFoundError(f"Dossier BERTopic introuvable : {BERTOPIC_PATH}")

    required = ["config.json", "topics.json"]
    missing = [f for f in required if not os.path.exists(os.path.join(BERTOPIC_PATH, f))]
    if missing:
        raise FileNotFoundError(
            f"Export BERTopic incomplet ({', '.join(missing)} manquant)."
        )

    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return BERTopic.load(BERTOPIC_PATH, embedding_model=embedding_model)


@st.cache_resource(show_spinner=False)
def load_noms_motifs() -> dict:
    if not os.path.exists(NOMS_MOTIFS_PATH):
        raise FileNotFoundError(f"Fichier introuvable : {NOMS_MOTIFS_PATH}.")
    with open(NOMS_MOTIFS_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return {str(k): str(v).strip() for k, v in raw.items()}


@st.cache_resource(show_spinner=False)
def load_topic_keywords() -> dict:
    """Fallback mots-clés si BERTopic.transform échoue."""
    if not os.path.exists(TOPICS_PATH):
        return {}
    with open(TOPICS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    reps = data.get("topic_representations") or {}
    out = {}
    for topic_id, pairs in reps.items():
        cleaned = []
        for item in pairs:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                cleaned.append((str(item[0]).lower(), float(item[1])))
        out[str(topic_id)] = cleaned
    return out


# ---------------------------------------------------------------------------
# Prédiction du risque d'annulation (XGBoost)
# ---------------------------------------------------------------------------

def predict_cancellation_risk(rdv: dict) -> float:
    bundle = load_xgb_bundle()
    model = bundle["model"]
    encoder = bundle["target_encoder"]
    categorical_columns = bundle["categorical_columns"]
    feature_columns = bundle["feature_columns"]

    df = pd.DataFrame([rdv])
    df = engineer_features(df)

    for col in feature_columns:
        if col not in df.columns:
            df[col] = None

    df_encoded = df.copy()
    df_encoded[categorical_columns] = encoder.transform(df[categorical_columns])
    X = df_encoded[feature_columns]

    proba = model.predict_proba(X)[0]
    label_mapping = bundle.get("label_mapping", {1: "confirmé", 0: "annulé"})
    idx_annule = [k for k, v in label_mapping.items() if v == "annulé"][0]
    return float(proba[idx_annule])


# ---------------------------------------------------------------------------
# Classification NLP des motifs
# ---------------------------------------------------------------------------

def _classify_with_keywords(commentaire: str, min_score: float = 0.035) -> str:
    """Classifieur rapide basé sur topics.json + noms_motifs.json."""
    noms_motifs = load_noms_motifs()
    topic_keywords = load_topic_keywords()
    texte = clean_comment(commentaire)
    if not texte:
        return noms_motifs.get("-1", "Non classé")

    best_id, best_score = "-1", 0.0
    for topic_id, pairs in topic_keywords.items():
        if topic_id == "-1":
            continue
        score = 0.0
        for word, weight in pairs:
            if word and word in texte:
                score += weight * (1.4 if " " in word else 1.0)
        if score > best_score:
            best_score, best_id = score, topic_id

    if best_score < min_score:
        return noms_motifs.get("-1", "Non classé")
    return noms_motifs.get(best_id, noms_motifs.get("-1", "Non classé"))


def predict_cancellation_reason(commentaire: str) -> str:
    """
    Classe un commentaire vers un motif métier.

    Utilise le classifieur mots-clés (topics.json) — fiable et immédiat.
    BERTopic + SentenceTransformer est désactivé ici car le téléchargement
    de l'embedding bloque Docker (spinner infini).
    """
    if not commentaire or not str(commentaire).strip():
        return "Non classé"
    return _classify_with_keywords(commentaire)


def predict_cancellation_reasons(commentaires) -> list[str]:
    """Classification batch — rapide, sans chargement BERTopic."""
    texts = list(commentaires) if commentaires is not None else []
    return [predict_cancellation_reason(t) for t in texts]


def score_rendez_vous(df: pd.DataFrame):
    """Score plusieurs RDV sans masquer les erreurs d'applicabilité du modèle."""
    scores, errors = [], []
    for _, row in df.iterrows():
        try:
            scores.append(predict_cancellation_risk(row.to_dict()))
            errors.append("")
        except Exception as e:
            scores.append(None)
            errors.append(str(e))
    out = df.copy()
    out["risque"] = scores
    out["erreur_prediction"] = errors
    return out
