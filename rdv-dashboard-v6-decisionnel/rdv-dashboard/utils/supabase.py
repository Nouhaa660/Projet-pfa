"""
Connexion Supabase (PostgreSQL) et fonction unique d'accès aux rendez-vous.

Toutes les pages passent par get_rendez_vous() plutôt que d'écrire leur
propre SQL, pour centraliser la logique d'accès aux données.
"""

import os

import pandas as pd
import psycopg2
import streamlit as st


def _get_secret(key: str, default: str = None) -> str:
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)


def get_connection_params() -> dict:
    return {
        "host": _get_secret("SUPABASE_DB_HOST"),
        "port": _get_secret("SUPABASE_DB_PORT", "5432"),
        "dbname": _get_secret("SUPABASE_DB_NAME", "postgres"),
        "user": _get_secret("SUPABASE_DB_USER"),
        "password": _get_secret("SUPABASE_DB_PASSWORD"),
    }


@st.cache_resource(show_spinner=False)
def get_connection():
    params = get_connection_params()
    missing = [k for k, v in params.items() if not v and k != "port"]
    if missing:
        raise RuntimeError(
            f"Paramètres de connexion Supabase manquants : {missing}. "
            f"Vérifiez .streamlit/secrets.toml ou les variables d'environnement."
        )
    return psycopg2.connect(**params)


def run_query(query: str, params: tuple = None) -> pd.DataFrame:
    conn = get_connection()
    try:
        return pd.read_sql_query(query, conn, params=params)
    except psycopg2.InterfaceError:
        get_connection.clear()
        conn = get_connection()
        return pd.read_sql_query(query, conn, params=params)


def get_rendez_vous(
    columns: list = None,
    where: str = None,
    order_by: str = None,
    limit: int = None,
) -> pd.DataFrame:
    """
    Fonction unique d'accès à la table rendez_vous, utilisée par toutes les pages.

    - columns : liste de colonnes à charger (None = toutes les colonnes)
    - where   : condition SQL brute (ex: "status = 'Annulé'"), sans le mot WHERE
    - order_by: clause de tri brute (ex: "date_rdv DESC"), sans ORDER BY
    - limit   : nombre max de lignes

    Note : where/order_by sont des chaînes fixes écrites dans le code des
    pages (jamais construites depuis une saisie utilisateur), donc pas de
    risque d'injection SQL ici.
    """
    cols = ", ".join(columns) if columns else "*"
    query = f"SELECT {cols} FROM rendez_vous"
    if where:
        query += f" WHERE {where}"
    if order_by:
        query += f" ORDER BY {order_by}"
    if limit:
        query += f" LIMIT {int(limit)}"
    query += ";"
    return run_query(query)
