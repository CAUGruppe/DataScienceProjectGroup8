import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import utils

st.set_page_config(page_title="RQ2 | Social Movement Framing", layout="wide")

# --------------------------------------------------
# RQ2
# --------------------------------------------------
st.markdown("""
### Research Question 2
What patterns of positive, neutral, and negative framing are used in German media
when reporting on social movements, and how do these patterns vary across different
news outlets (Tagesschau vs. Bild)?
""")

st.divider()

# --------------------------------------------------
# Load data
# --------------------------------------------------
@st.cache_data
def load_rq2_data():
    return utils.load_data().copy()

df = load_rq2_data()

# --------------------------------------------------
# Prepare shared columns
# --------------------------------------------------
url_col  = "url" if "url" in df.columns else "DocumentIdentifier"
tone_col = "V2Tone"

def label_outlet(url):
    url = str(url).lower()
    if "tagesschau.de" in url: return "Tagesschau"
    if "bild.de" in url:       return "Bild"
    return None

df["outlet_group"] = df[url_col].map(label_outlet)

def parse_tone(val):
    try:    return float(str(val).split(",")[0])
    except: return np.nan

def classify_tone(t):
    try:
        t = float(t)
        if t > 1.0:    return "Positive"
        elif t < -1.0: return "Negative"
        else:           return "Neutral"
    except:
        return None

df["AvgTone"]   = df[tone_col].map(parse_tone)
df["ToneLabel"] = df["AvgTone"].map(classify_tone)

# --------------------------------------------------
# Social movement filter
# --------------------------------------------------
URL_KEYWORDS = (
    "protest|demonstration|demo-|streik|kundgebung|bewegung|aktivist|"
    "fridays-for-future|klimaprotest|verdi|gewerkschaft|arbeitskampf|"
    "blockade|bauernprotest|klimastreik|buergerinitiative"
)

df_soc = df[
    df["outlet_group"].notna()
    & df[url_col].fillna("").str.lower().str.contains(URL_KEYWORDS, regex=True)
].copy()

df_soc_dedup = (
    df_soc.groupby([url_col, "outlet_group"])["AvgTone"]
    .mean().reset_index()
)
df_soc_dedup["ToneLabel"] = df_soc_dedup["AvgTone"].map(classify_tone)
df_soc_dedup = df_soc_dedup.dropna(subset=["ToneLabel"])

# --------------------------------------------------
# Visualization 1 — Grouped Bar Chart
# --------------------------------------------------
summary = (
    df_soc_dedup.groupby(["outlet_group", "ToneLabel"])
    .size().reset_index(name="Count")
)
summary["Total"] = summary.groupby("outlet_group")["Count"].transform("sum")
summary["Pct"]   = summary["Count"] / summary["Total"] * 100

OUTLETS    = [o for o in ["Tagesschau", "Bild"] if o in df_soc_dedup["outlet_group"].values]
TONE_ORDER = ["Negative", "Neutral", "Positive"]
COLORS     = {
    "Tagesschau": "#1565C0",
    "Bild":       "#C62828",
}

fig1 = go.Figure()

for outlet in OUTLETS:
    pct_vals, count_vals = [], []
    for tone in TONE_ORDER:
        row = summary[(summary["outlet_group"] == outlet) & (summary["ToneLabel"] == tone)]
        pct_vals.append(round(row["Pct"].values[0], 2) if len(row) else 0.0)
        count_vals.append(int(row["Count"].values[0]) if len(row) else 0)

    fig1.add_trace(go.Bar(
        name=outlet,
        x=TONE_ORDER,
        y=pct_vals,
        marker_color=COLORS[outlet],
        marker_line=dict(color="white", width=1.5),
        customdata=list(zip(count_vals, [f"{p:.1f}" for p in pct_vals])),
        text=[f"{p:.1f}%" for p in pct_vals],
        textposition="outside",
        textfont=dict(size=12, color=COLORS[outlet]),
        hovertemplate=(
            f"<b>{outlet} – %{{x}}</b><br>"
            "Share: %{customdata[1]}%<br>"
            "Articles: %{customdata[0]}<extra></extra>"
        ),
    ))

n_ts   = int(summary[summary["outlet_group"] == "Tagesschau"]["Count"].sum()) if "Tagesschau" in OUTLETS else 0
n_bild = int(summary[summary["outlet_group"] == "Bild"]["Count"].sum())       if "Bild" in OUTLETS else 0

fig1.update_layout(
    title="Share of Negative, Neutral and Positive Social Movement Articles by Outlet",
    xaxis_title="Tone Category",
    yaxis=dict(title="Share of Articles (%)", range=[0, 115]),
    barmode="group",
    legend_title="Outlet",
    template="plotly_white",
    updatemenus=[
        dict(
            type="buttons",
            direction="right",
            x=0.5,
            xanchor="center",
            y=1.18,
            yanchor="top",
            showactive=True,
            buttons=[
                dict(
                    label="All outlets",
                    method="update",
                    args=[
                        {"visible": [True, True]},
                        {"title": "Share of Negative, Neutral and Positive Social Movement Articles by Outlet"}
                    ]
                ),
                dict(
                    label="Tagesschau only",
                    method="update",
                    args=[
                        {"visible": [True, False]},
                        {"title": "Share of Tones — Tagesschau"}
                    ]
                ),
                dict(
                    label="Bild only",
                    method="update",
                    args=[
                        {"visible": [False, True]},
                        {"title": "Share of Tones — Bild"}
                    ]
                ),
            ]
        )
    ],
    annotations=[dict(
        text=f"Source: GDELT GKG | Tagesschau n={n_ts}, Bild n={n_bild} | AvgTone > 1 = Positive, < −1 = Negative",
        xref="paper", yref="paper", x=0.5, y=-0.15,
        showarrow=False, font=dict(size=10, color="gray"), xanchor="center",
    )],
)

st.plotly_chart(fig1, use_container_width=True)

st.markdown("""
### Interpretation
Both outlets frame social movements predominantly negatively. Tagesschau assigns
a negative tone to around 89.8% of its social movement articles, while Bild reaches
around 81.7%. Contrary to expectations, Bild shows noticeably more neutral (11.0% vs.
8.8%) and positive (7.2% vs. 1.4%) coverage than Tagesschau. The sharpest contrast
is in positive framing: Bild's share is roughly five times higher than Tagesschau's,
suggesting Bild occasionally adopts a sympathetic framing of certain protest movements.
""")

st.divider()

# --------------------------------------------------
# Visualization 2 — Monthly Average Tone (Line Chart)
# --------------------------------------------------
df_soc["date"] = pd.to_datetime(
    df[df[url_col].isin(df_soc[url_col])]["DATE"].astype(str).str[:8],
    format="%Y%m%d", errors="coerce"
)

_df = df_soc.copy()
_df["AvgTone"] = _df[tone_col].map(parse_tone)
_df["date"]    = pd.to_datetime(_df["DATE"].astype(str).str[:8], format="%Y%m%d", errors="coerce")
_df = _df.dropna(subset=["date", "AvgTone"])
_df["month"] = _df["date"].dt.to_period("M").dt.to_timestamp()

monthly_avg   = _df.groupby(["month", "outlet_group"])["AvgTone"].mean().reset_index(name="average_tone")
monthly_count = _df.groupby(["month", "outlet_group"]).size().reset_index(name="article_count")
monthly       = monthly_avg.merge(monthly_count, on=["month", "outlet_group"], how="left")
monthly       = monthly[monthly["article_count"] >= 3]

fig2 = go.Figure()

for outlet in OUTLETS:
    sub = monthly[monthly["outlet_group"] == outlet]
    fig2.add_trace(go.Scatter(
        x=sub["month"],
        y=sub["average_tone"],
        mode="lines+markers",
        name=outlet,
        customdata=sub[["article_count"]],
        hovertemplate=(
            f"<b>{outlet}</b><br>"
            "Month: %{x|%b %Y}<br>"
            "Average tone: %{y:.2f}<br>"
            "Article count: %{customdata[0]}<extra></extra>"
        )
    ))

fig2.add_hline(y=0, line_width=1)
fig2.add_hline(y=-1, line_width=1, line_dash="dash", line_color="red",
               annotation_text="Negativity threshold (−1)",
               annotation_position="bottom right")

fig2.update_layout(
    title="Average Monthly Tone of Social Movement Coverage by Outlet",
    xaxis_title="Month",
    yaxis_title="Average Tone",
    legend_title="Outlet",
    hovermode="x unified",
    template="plotly_white",
    updatemenus=[
        dict(
            buttons=[
                dict(
                    label="All outlets",
                    method="update",
                    args=[
                        {"visible": [True, True]},
                        {"title": "Average Monthly Tone of Social Movement Coverage by Outlet"}
                    ]
                ),
                dict(
                    label="Tagesschau only",
                    method="update",
                    args=[
                        {"visible": [True, False]},
                        {"title": "Average Monthly Tone — Tagesschau"}
                    ]
                ),
                dict(
                    label="Bild only",
                    method="update",
                    args=[
                        {"visible": [False, True]},
                        {"title": "Average Monthly Tone — Bild"}
                    ]
                ),
            ],
            direction="down",
            showactive=True,
            x=1.02,
            xanchor="left",
            y=1.15,
            yanchor="top"
        )
    ]
)

st.plotly_chart(fig2, use_container_width=True)

st.markdown("""
### Interpretation
Both Tagesschau and Bild remain consistently below the neutral zero line across the
entire observation window, confirming persistently negative tone toward social movements.
Tagesschau's line is comparatively stable, while Bild shows more variation month to
month. Notable dips often coincide with major protest events such as the Bauernproteste
in January 2024.
""")

st.divider()
