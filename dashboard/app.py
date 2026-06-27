import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# Connexion PostgreSQL
def get_engine():
    user     = os.getenv("POSTGRES_USER", "etl_user")
    password = os.getenv("POSTGRES_PASSWORD", "etl_password")
    host     = os.getenv("POSTGRES_HOST", "localhost")
    port     = int(os.getenv("POSTGRES_PORT", "5433").strip())
    db       = os.getenv("POSTGRES_DB", "financial_db")
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")

def load_data():
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT date, close, daily_return, ma_7, ma_30, volatility_30
            FROM transformed_stock_data
            WHERE ticker = 'GOOGL'
            ORDER BY date
        """), conn)
    df["date"] = pd.to_datetime(df["date"])
    return df

# Initialiser l'app
app = dash.Dash(__name__)
app.title = "Financial ETL Dashboard — GOOGL"

# Layout
app.layout = html.Div([

    # Header
    html.Div([
        html.H1("📈 Financial ETL Dashboard", style={"color": "white", "margin": "0"}),
        html.P("Google (GOOGL) — Analyse sur 2 ans", style={"color": "#aaa", "margin": "5px 0 0 0"}),
    ], style={
        "background": "#1a1a2e",
        "padding": "20px 30px",
        "marginBottom": "20px"
    }),

    # KPI Cards
    html.Div(id="kpi-cards", style={
        "display": "flex",
        "gap": "15px",
        "padding": "0 30px",
        "marginBottom": "20px"
    }),

    # Graphiques
    html.Div([
        # Prix de clôture + moyennes mobiles
        html.Div([
            html.H3("Prix de clôture & Moyennes mobiles", style={"color": "#333"}),
            dcc.Graph(id="price-chart"),
        ], style={"background": "white", "padding": "20px", "borderRadius": "8px",
                  "boxShadow": "0 2px 8px rgba(0,0,0,0.1)", "marginBottom": "20px"}),

        # Rendement journalier
        html.Div([
            html.H3("Rendement journalier (%)", style={"color": "#333"}),
            dcc.Graph(id="return-chart"),
        ], style={"background": "white", "padding": "20px", "borderRadius": "8px",
                  "boxShadow": "0 2px 8px rgba(0,0,0,0.1)", "marginBottom": "20px"}),

        # Volatilité
        html.Div([
            html.H3("Volatilité 30 jours", style={"color": "#333"}),
            dcc.Graph(id="volatility-chart"),
        ], style={"background": "white", "padding": "20px", "borderRadius": "8px",
                  "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),

    ], style={"padding": "0 30px 30px"}),

    # Intervalle de rafraîchissement
    dcc.Interval(id="interval", interval=60*1000, n_intervals=0)

], style={"background": "#f5f5f5", "minHeight": "100vh", "fontFamily": "Arial"})


def make_kpi_card(title, value, color):
    return html.Div([
        html.P(title, style={"margin": "0", "color": "#666", "fontSize": "12px"}),
        html.H2(value, style={"margin": "5px 0 0 0", "color": color}),
    ], style={
        "background": "white",
        "padding": "15px 20px",
        "borderRadius": "8px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
        "flex": "1",
        "borderLeft": f"4px solid {color}"
    })


@app.callback(
    Output("kpi-cards", "children"),
    Output("price-chart", "figure"),
    Output("return-chart", "figure"),
    Output("volatility-chart", "figure"),
    Input("interval", "n_intervals")
)
def update_dashboard(n):
    df = load_data()

    # KPI Cards
    prix_actuel = f"${df['close'].iloc[-1]:.2f}"
    rendement   = f"{df['daily_return'].mean():.2f}%"
    volatilite  = f"{df['volatility_30'].mean():.2f}%"
    prix_max    = f"${df['close'].max():.2f}"

    cards = [
        make_kpi_card("Prix actuel",       prix_actuel, "#2196F3"),
        make_kpi_card("Rendement moyen",   rendement,   "#4CAF50"),
        make_kpi_card("Volatilité moyenne",volatilite,  "#FF9800"),
        make_kpi_card("Prix max 2 ans",    prix_max,    "#9C27B0"),
    ]

    # Graphique 1 — Prix + Moyennes mobiles
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df["date"], y=df["close"],
                              name="Clôture", line=dict(color="#2196F3", width=1.5)))
    fig1.add_trace(go.Scatter(x=df["date"], y=df["ma_7"],
                              name="MA 7j", line=dict(color="#FF9800", dash="dash")))
    fig1.add_trace(go.Scatter(x=df["date"], y=df["ma_30"],
                              name="MA 30j", line=dict(color="#F44336", dash="dot")))
    fig1.update_layout(
        height=350, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=1.1),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#eee"),
        yaxis=dict(showgrid=True, gridcolor="#eee", tickprefix="$")
    )

    # Graphique 2 — Rendement journalier
    colors = ["#4CAF50" if r >= 0 else "#F44336" for r in df["daily_return"]]
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=df["date"], y=df["daily_return"],
                          marker_color=colors, name="Rendement"))
    fig2.update_layout(
        height=300, margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#eee"),
        yaxis=dict(showgrid=True, gridcolor="#eee", ticksuffix="%")
    )

    # Graphique 3 — Volatilité
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=df["date"], y=df["volatility_30"],
                              fill="tozeroy", name="Volatilité 30j",
                              line=dict(color="#9C27B0")))
    fig3.update_layout(
        height=300, margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#eee"),
        yaxis=dict(showgrid=True, gridcolor="#eee", ticksuffix="%")
    )

    return cards, fig1, fig2, fig3


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)