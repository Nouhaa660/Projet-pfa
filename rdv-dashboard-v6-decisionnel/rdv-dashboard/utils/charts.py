"""
Graphiques Plotly — rendu corporate NEXTHORIZON.

Principes :
- une couleur métier dominante (bleu)
- vert / rouge uniquement pour le sens (confirmé / annulé)
- pas de palette arc-en-ciel
- labels discrets, hover précis, densités faibles
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.ui import BLUE, GREEN, AMBER, RED, NAVY, MUTED, BORDER

# Nuances sobres (pas de violet / cyan flashy)
SLATE = "#64748B"
SLATE_LIGHT = "#94A3B8"
BLUE_DEEP = "#1E3A8A"
BLUE_SOFT = "#93C5FD"
INK = "#334155"
GRID = "#F1F5F9"

STATUS_COLORS = {
    "Confirmé": "#0F766E",   # teal sombre, plus corporate que vert vif
    "Annulé": "#B91C1C",     # rouge mat
}

# Empilements : dégradé bleu-gris uniquement
STACK_BLUES = [
    "#1E40AF",
    "#2563EB",
    "#3B82F6",
    "#93C5FD",
    "#CBD5E1",
]


def _base(fig, height=300, show_legend=True):
    fig.update_layout(
        height=height,
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(
            family="IBM Plex Sans, Segoe UI, Helvetica, Arial, sans-serif",
            color=INK,
            size=11,
        ),
        margin=dict(l=4, r=12, t=28 if show_legend else 12, b=4),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="left",
            x=0,
            font=dict(size=10, color=SLATE),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            itemsizing="constant",
            traceorder="normal",
        ) if show_legend else dict(visible=False),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor=BORDER,
            font=dict(color=NAVY, size=11, family="IBM Plex Sans, sans-serif"),
        ),
        hovermode="closest",
        bargap=0.28,
        bargroupgap=0.08,
        separators=", ",
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=True,
        linewidth=1,
        linecolor="#E2E8F0",
        ticks="outside",
        ticklen=3,
        tickcolor="#E2E8F0",
        tickfont=dict(size=10, color=SLATE),
        title=dict(text="", font=dict(size=10, color=SLATE)),
        automargin=True,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=GRID,
        gridwidth=1,
        zeroline=False,
        showline=False,
        tickfont=dict(size=10, color=SLATE),
        title=dict(text="", font=dict(size=10, color=SLATE)),
        automargin=True,
    )
    return fig


def chart_evolution_mensuelle(df, colonne_date="date_rdv"):
    d = df.copy()
    d[colonne_date] = pd.to_datetime(d[colonne_date], errors="coerce")
    d = d.dropna(subset=[colonne_date])
    d["mois"] = d[colonne_date].dt.to_period("M").dt.to_timestamp()

    if "status" in d.columns:
        trend = d.groupby(["mois", "status"]).size().reset_index(name="nombre")
        fig = go.Figure()
        for status, color in STATUS_COLORS.items():
            s = trend[trend["status"] == status]
            if s.empty:
                continue
            fig.add_trace(
                go.Scatter(
                    x=s["mois"],
                    y=s["nombre"],
                    name=status,
                    mode="lines",
                    line=dict(color=color, width=2),
                    hovertemplate="%{x|%b %Y}<br>%{y:,} RDV<extra>" + status + "</extra>",
                )
            )
    else:
        trend = d.groupby("mois").size().reset_index(name="nombre")
        fig = go.Figure(
            go.Scatter(
                x=trend["mois"],
                y=trend["nombre"],
                mode="lines",
                line=dict(color=BLUE, width=2),
                hovertemplate="%{x|%b %Y}<br>%{y:,} RDV<extra></extra>",
                showlegend=False,
            )
        )

    fig.update_yaxes(title_text="Nombre de RDV")
    return _base(fig, 290)


def chart_repartition_statuts(df, colonne_statut="status"):
    counts = df[colonne_statut].value_counts()
    labels = counts.index.tolist()
    values = counts.values.tolist()
    colors = [STATUS_COLORS.get(l, SLATE) for l in labels]
    total = sum(values) or 1

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.68,
            marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value:,} · %{percent}<extra></extra>",
            sort=False,
        )
    )
    # Annotation centrale sobre
    fig.update_layout(
        annotations=[
            dict(
                text=f"<b>{total:,}</b><br><span style='font-size:11px;color:{SLATE}'>RDV</span>".replace(",", " "),
                x=0.5, y=0.5, showarrow=False, font=dict(size=16, color=NAVY),
            )
        ]
    )
    return _base(fig, 270)


def chart_classement_agents(perf_df, moyenne, value_col="Taux confirmation", max_rows=12):
    """Ancien classement confirmation — conservé pour compatibilité."""
    d = perf_df.sort_values(value_col, ascending=True).tail(max_rows)
    fig = go.Figure(
        go.Bar(
            x=d[value_col],
            y=d["agent"],
            orientation="h",
            marker=dict(color=BLUE, line=dict(width=0)),
            hovertemplate="<b>%{y}</b><br>%{x:.1f}%<extra></extra>",
            showlegend=False,
        )
    )
    fig.add_vline(
        x=moyenne,
        line=dict(color=SLATE_LIGHT, width=1, dash="dot"),
        annotation=dict(
            text=f"Moyenne {moyenne:.0f}%",
            font=dict(size=10, color=SLATE),
            bgcolor="rgba(255,255,255,.85)",
        ),
        annotation_position="top",
    )
    fig.update_xaxes(ticksuffix="%", range=[0, max(100, float(d[value_col].max()) + 8)])
    return _base(fig, max(240, min(360, 90 + len(d) * 20)), show_legend=False)


def chart_performance_agents(diag_df, global_rate: float, min_rdv: int = 10, max_rows: int = 15):
    """
    Classement décisionnel : taux d'annulation des agents à volume suffisant.
    Couleur selon l'écart vs taux global (à investiguer / norme / favorable).
    """
    d = diag_df.copy()
    if "RDV" in d.columns:
        d = d[d["RDV"] >= min_rdv]
    if d.empty or "Taux annulation" not in d.columns:
        return None

    d = d.sort_values("Taux annulation", ascending=True).tail(max_rows)

    colors = []
    for _, row in d.iterrows():
        ecart = float(row.get("Écart vs global", row["Taux annulation"] - global_rate))
        if ecart >= 10:
            colors.append("#B91C1C")      # à investiguer
        elif ecart <= -10:
            colors.append("#0F766E")      # favorable
        else:
            colors.append(BLUE)           # norme

    fig = go.Figure(
        go.Bar(
            x=d["Taux annulation"],
            y=d["agent"],
            orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            customdata=d[["RDV", "Écart vs global", "Confirmés", "Annulés"]].to_numpy()
            if all(c in d.columns for c in ["RDV", "Écart vs global", "Confirmés", "Annulés"])
            else None,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Annulation : %{x:.1f}%<br>"
                "Écart : %{customdata[1]:+.1f} pts<br>"
                "Volume : %{customdata[0]} RDV"
                "<extra></extra>"
            ),
            showlegend=False,
        )
    )
    fig.add_vline(
        x=global_rate,
        line=dict(color=SLATE, width=1.2, dash="dot"),
        annotation=dict(
            text=f"Global {global_rate:.0f}%",
            font=dict(size=10, color=SLATE),
            bgcolor="rgba(255,255,255,.9)",
        ),
        annotation_position="top",
    )
    xmax = max(100.0, float(d["Taux annulation"].max()) + 8)
    fig.update_xaxes(ticksuffix="%", range=[0, xmax], title_text="Taux d'annulation")
    return _base(fig, max(260, min(400, 100 + len(d) * 22)), show_legend=False)


def chart_taux_annulation_agents(agent_df, value_col="taux_annulation", max_rows=12):
    d = agent_df.sort_values(value_col, ascending=True).tail(max_rows)
    # Une seule teinte : intensité selon la valeur (lecture indicative)
    vmax = max(float(d[value_col].max()), 1)
    colors = [
        f"rgba(37,99,235,{0.35 + 0.55 * (v / vmax)})"
        for v in d[value_col]
    ]
    fig = go.Figure(
        go.Bar(
            x=d[value_col],
            y=d["agent"],
            orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=[f"{v:.0f}%" for v in d[value_col]],
            textposition="outside",
            textfont=dict(size=10, color=SLATE),
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>%{x:.1f}%<extra></extra>",
            showlegend=False,
        )
    )
    fig.update_xaxes(ticksuffix="%")
    return _base(fig, max(240, min(360, 90 + len(d) * 20)), show_legend=False)


def chart_taux_par_jour(df, colonne_date="date_rdv"):
    ordre = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    noms = dict(zip(ordre, ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]))
    d = df.copy()
    d[colonne_date] = pd.to_datetime(d[colonne_date], errors="coerce")
    d["est_annule"] = d["status"] == "Annulé"
    d["jour"] = d[colonne_date].dt.day_name()
    s = d.groupby("jour")["est_annule"].mean().reindex(ordre) * 100
    p = s.reset_index()
    p.columns = ["Jour", "Taux"]
    p["Jour"] = p["Jour"].map(noms)

    fig = go.Figure(
        go.Bar(
            x=p["Jour"],
            y=p["Taux"],
            marker=dict(color=BLUE, line=dict(width=0)),
            hovertemplate="<b>%{x}</b><br>%{y:.1f}%<extra></extra>",
            showlegend=False,
        )
    )
    fig.update_yaxes(ticksuffix="%", title_text="Taux d'annulation")
    return _base(fig, 270, show_legend=False)


def _extraire_heure(val):
    if pd.isna(val):
        return None
    if hasattr(val, "hour"):
        return val.hour
    try:
        return int(str(val).split(":")[0])
    except (ValueError, IndexError):
        return None


def chart_taux_par_heure(df, colonne_heure="heure_rdv"):
    if colonne_heure not in df.columns or df[colonne_heure].isna().all():
        return None
    d = df.copy()
    d["est_annule"] = d["status"] == "Annulé"
    d["heure"] = d[colonne_heure].apply(_extraire_heure)
    d = d.dropna(subset=["heure"])
    if d.empty:
        return None
    p = d.groupby("heure")["est_annule"].mean().reset_index()
    p["est_annule"] *= 100

    fig = go.Figure(
        go.Scatter(
            x=p["heure"],
            y=p["est_annule"],
            mode="lines",
            line=dict(color=BLUE, width=2),
            hovertemplate="Heure %{x}h<br>%{y:.1f}%<extra></extra>",
            showlegend=False,
        )
    )
    fig.update_xaxes(dtick=1, title_text="Heure")
    fig.update_yaxes(ticksuffix="%", title_text="Taux d'annulation")
    return _base(fig, 270, show_legend=False)


def chart_taux_par_mois(df, colonne_date="date_rdv"):
    d = df.copy()
    d[colonne_date] = pd.to_datetime(d[colonne_date], errors="coerce")
    d["est_annule"] = d["status"] == "Annulé"
    d["mois"] = d[colonne_date].dt.to_period("M").dt.to_timestamp()
    p = d.groupby("mois")["est_annule"].mean().reset_index()
    p["est_annule"] *= 100

    fig = go.Figure(
        go.Scatter(
            x=p["mois"],
            y=p["est_annule"],
            mode="lines",
            line=dict(color=BLUE, width=2),
            hovertemplate="%{x|%b %Y}<br>%{y:.1f}%<extra></extra>",
            showlegend=False,
        )
    )
    fig.update_yaxes(ticksuffix="%", title_text="Taux d'annulation")
    return _base(fig, 270, show_legend=False)


def chart_motifs_repartition(df, colonne_motif="motif"):
    p = (
        df[colonne_motif].value_counts(normalize=True)
        .mul(100).round(1).reset_index()
    )
    p.columns = ["Motif", "Pourcentage"]
    p = p.sort_values("Pourcentage", ascending=True).tail(8)

    fig = go.Figure(
        go.Bar(
            x=p["Pourcentage"],
            y=p["Motif"],
            orientation="h",
            marker=dict(color=BLUE, line=dict(width=0)),
            text=[f"{v:.0f}%" for v in p["Pourcentage"]],
            textposition="outside",
            textfont=dict(size=10, color=SLATE),
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>%{x:.1f}%<extra></extra>",
            showlegend=False,
        )
    )
    fig.update_xaxes(ticksuffix="%")
    return _base(fig, max(250, 80 + len(p) * 22), show_legend=False)


def chart_motifs_evolution(df, colonne_date="date_rdv", colonne_motif="motif"):
    d = df.copy()
    d[colonne_date] = pd.to_datetime(d[colonne_date], errors="coerce")
    d["mois"] = d[colonne_date].dt.to_period("M").dt.to_timestamp()

    top = d[colonne_motif].value_counts().head(5).index.tolist()
    d = d[d[colonne_motif].isin(top)]
    p = d.groupby(["mois", colonne_motif]).size().reset_index(name="nombre")

    fig = go.Figure()
    for i, motif in enumerate(top):
        s = p[p[colonne_motif] == motif]
        fig.add_trace(
            go.Bar(
                x=s["mois"],
                y=s["nombre"],
                name=str(motif)[:42],
                marker=dict(color=STACK_BLUES[i % len(STACK_BLUES)], line=dict(width=0)),
                hovertemplate="%{x|%b %Y}<br>%{y} — " + str(motif)[:40] + "<extra></extra>",
            )
        )
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Annulations")
    return _base(fig, 300)


def chart_distribution_risque(df, colonne_niveau="niveau"):
    ordre = ["Faible", "Moyen", "Élevé"]
    colors_map = {"Faible": "#0F766E", "Moyen": "#B45309", "Élevé": "#B91C1C"}
    p = df[colonne_niveau].value_counts().reindex(ordre, fill_value=0)
    fig = go.Figure(
        go.Pie(
            labels=p.index.tolist(),
            values=p.values.tolist(),
            hole=0.68,
            marker=dict(
                colors=[colors_map[k] for k in p.index],
                line=dict(color="#FFFFFF", width=2),
            ),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value} · %{percent}<extra></extra>",
            sort=False,
        )
    )
    return _base(fig, 270)


def chart_completude(completude_df):
    d = completude_df.sort_values("Complétude (%)", ascending=True)
    # Une seule teinte bleue ; seuil bas → gris (pas de feux de signalisation criards)
    colors = [
        BLUE if v >= 85 else (SLATE_LIGHT if v >= 60 else "#94A3B8")
        for v in d["Complétude (%)"]
    ]
    fig = go.Figure(
        go.Bar(
            x=d["Complétude (%)"],
            y=d["Colonne"],
            orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=[f"{v:.0f}%" for v in d["Complétude (%)"]],
            textposition="outside",
            textfont=dict(size=9, color=SLATE),
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>%{x:.1f}%<extra></extra>",
            showlegend=False,
        )
    )
    fig.update_xaxes(range=[0, 112], ticksuffix="%")
    return _base(fig, max(240, min(400, 70 + len(d) * 16)), show_legend=False)
