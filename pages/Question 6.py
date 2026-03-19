import streamlit as st
import pandas as pd
import numpy as np
import re
import utils
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="RQ6 | Sentiment by Country", layout="wide")

st.markdown("""
### Research Question 6
Which countries receive the most positive, neutral or negative sentiment in German media coverage and how does this sentiment vary between Tagesschau and ZDF?
""")

st.divider()

@st.cache_data
def load_rq6_data():
    return utils.load_data().copy()

df = load_rq6_data()
def first_tone(x):
    try:
        return float(str(x).split(",")[0])
    except Exception:
        return np.nan

df["tone"] = df["V2Tone"].map(first_tone)

# only German public broadcasters
df = df[df["SourceCommonName"].isin(["tagesschau.de", "zdf.de"])].copy()

df["outlet"] = df["SourceCommonName"].replace({
    "tagesschau.de": "Tagesschau",
    "zdf.de": "ZDF"
})

# extract first location name
def extract_first_location_name(loc_string):
    try:
        first_loc = str(loc_string).split(";")[0]
        parts = first_loc.split("#")
        if len(parts) > 1:
            return parts[1].strip()
        return np.nan
    except Exception:
        return np.nan

df["location_name"] = df["Locations"].apply(extract_first_location_name)

# convert location to country
def extract_country(location_name):
    if pd.isna(location_name):
        return np.nan

    location_name = str(location_name).strip()

    if "," in location_name:
        return location_name.split(",")[-1].strip()

    return location_name

df["country"] = df["location_name"].apply(extract_country)

# remove missing tone/country
df = df.dropna(subset=["tone", "country"])

# remove non-country labels
exclude_labels = {"World", "Europe", "Asia", "Middle East", "European Union"}
df = df[~df["country"].isin(exclude_labels)].copy()

# top countries
top_countries = df["country"].value_counts().head(12).index.tolist()
df_top = df[df["country"].isin(top_countries)].copy()

def tone_category(x):
    if x < -1:
        return "Negative"
    elif x > 1:
        return "Positive"
    return "Neutral"

df_top["tone_category"] = df_top["tone"].apply(tone_category)

# absolute counts
counts = (
    df_top.groupby(["country", "outlet", "tone_category"])
    .size()
    .unstack(fill_value=0)
)

for col in ["Negative", "Neutral", "Positive"]:
    if col not in counts.columns:
        counts[col] = 0

counts = counts[["Negative", "Neutral", "Positive"]].reset_index()

# percentage shares
shares = counts.copy()
shares[["Negative", "Neutral", "Positive"]] = (
    shares[["Negative", "Neutral", "Positive"]]
    .div(shares[["Negative", "Neutral", "Positive"]].sum(axis=1), axis=0) * 100
)

# order countries by average negative share
country_order = (
    shares.groupby("country")["Negative"]
    .mean()
    .sort_values()
    .index
    .tolist()
)

shares["country"] = pd.Categorical(shares["country"], categories=country_order, ordered=True)
shares = shares.sort_values("country")

counts["country"] = pd.Categorical(counts["country"], categories=country_order, ordered=True)
counts = counts.sort_values("country")

outlets = ["Tagesschau", "ZDF"]
sentiments = ["Negative", "Neutral", "Positive"]

colors = {
    "Negative": "#4C78A8",
    "Neutral": "#B0B0B0",
    "Positive": "#F58518"
}

fig = make_subplots(
    rows=1, cols=2,
    shared_yaxes=True,
    subplot_titles=("Tagesschau", "ZDF")
)

trace_indices = {s: [] for s in sentiments}

for col_idx, outlet in enumerate(outlets, start=1):
    outlet_share = (
        shares[shares["outlet"] == outlet]
        .set_index("country")
        .reindex(country_order)
    )

    outlet_count = (
        counts[counts["outlet"] == outlet]
        .set_index("country")
        .reindex(country_order)
    )

    countries = outlet_share.index.tolist()

    for sentiment in sentiments:
        customdata = np.array([
            countries,
            [outlet] * len(countries),
            [sentiment] * len(countries),
            outlet_count[sentiment].fillna(0).astype(int).values
        ]).T

        trace = go.Bar(
            y=countries,
            x=outlet_share[sentiment].fillna(0),
            name=sentiment,
            orientation="h",
            marker_color=colors[sentiment],
            customdata=customdata,
            hovertemplate=(
                "Country: %{customdata[0]}<br>"
                "Outlet: %{customdata[1]}<br>"
                "Sentiment: %{customdata[2]}<br>"
                "Share: %{x:.1f}%<br>"
                "Articles: %{customdata[3]}<extra></extra>"
            ),
            showlegend=(col_idx == 1)
        )

        fig.add_trace(trace, row=1, col=col_idx)
        trace_indices[sentiment].append(len(fig.data) - 1)

fig.update_layout(
    title="Sentiment Distribution by Country in Tagesschau and ZDF",
    barmode="stack",
    template="plotly_white",
    height=800,
    margin=dict(t=100, b=90, l=80, r=40),
    legend=dict(
        orientation="h",
        x=0.5,
        xanchor="center",
        y=-0.08,
        title="Sentiment"
    ),
    updatemenus=[
        dict(
            type="buttons",
            direction="right",
            x=0.5,
            xanchor="center",
            y=1.12,
            yanchor="top",
            showactive=True,
            buttons=[
                dict(
                    label="All sentiments",
                    method="update",
                    args=[{"visible": [True] * len(fig.data)}]
                ),
                dict(
                    label="Negative only",
                    method="update",
                    args=[{"visible": [i in trace_indices["Negative"] for i in range(len(fig.data))]}]
                ),
                dict(
                    label="Neutral only",
                    method="update",
                    args=[{"visible": [i in trace_indices["Neutral"] for i in range(len(fig.data))]}]
                ),
                dict(
                    label="Positive only",
                    method="update",
                    args=[{"visible": [i in trace_indices["Positive"] for i in range(len(fig.data))]}]
                ),
            ]
        )
    ]
)

fig.update_xaxes(title_text="Share of articles (%)", range=[0, 100], row=1, col=1)
fig.update_xaxes(title_text="Share of articles (%)", range=[0, 100], row=1, col=2)
fig.update_yaxes(title_text="Country", autorange="reversed", row=1, col=1)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
### Interpretation
This chart compares the sentiment distribution of the most frequently mentioned countries in Tagesschau and ZDF. It shows how strongly coverage of each country is dominated by negative, neutral or positive articles, and makes it easier to compare country-related framing across the two broadcasters.
""")


st.divider()

# --------------------------------------------------
# Visualization 2
# --------------------------------------------------
import plotly.express as px

rq6_viz2 = df.copy()

# exclude Germany here, because otherwise it dominates the chart
exclude_labels_viz2 = {"World", "Europe", "Asia", "Middle East", "European Union", "Germany"}
rq6_viz2 = rq6_viz2[~rq6_viz2["country"].isin(exclude_labels_viz2)].copy()

all_unique_countries = rq6_viz2["country"].dropna().unique()

color_palette = px.colors.qualitative.Alphabet + px.colors.qualitative.Dark24
country_color_map = {
    country: color_palette[i % len(color_palette)]
    for i, country in enumerate(all_unique_countries)
}
country_color_map["Others"] = "#B0B0B0"

brand_colors = {
    "United States": "#4C78A8",
    "Russia": "#E45756",
    "Ukraine": "#EECA3B",
    "Israel": "#9D755D"
}
country_color_map.update(brand_colors)

def filter_sentiment(data, sentiment):
    if sentiment == "Positive":
        return data[data["tone"] > 1].copy()
    elif sentiment == "Negative":
        return data[data["tone"] < -1].copy()
    return data[(data["tone"] >= -1) & (data["tone"] <= 1)].copy()

def prepare_donut_data(data, outlet_name, top_n=15):
    outlet_data = (
        data[data["outlet"] == outlet_name]
        .groupby("country")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    top = outlet_data.head(top_n).copy()
    rest = outlet_data.iloc[top_n:]["count"].sum()

    if rest > 0:
        top = pd.concat(
            [top, pd.DataFrame({"country": ["Others"], "count": [rest]})],
            ignore_index=True
        )
    return top

def top_legend_countries(data, top_n=8):
    top = (
        data.groupby("country")
        .size()
        .sort_values(ascending=False)
        .head(top_n)
        .index
        .tolist()
    )
    if "Others" not in top:
        top.append("Others")
    return top

sentiments = ["Positive", "Negative", "Neutral"]
outlets = ["Tagesschau", "ZDF"]

fig2 = make_subplots(
    rows=1,
    cols=2,
    specs=[[{"type": "domain"}, {"type": "domain"}]],
    subplot_titles=("Tagesschau", "ZDF")
)

pie_trace_map = {s: [] for s in sentiments}
legend_trace_map = {s: [] for s in sentiments}

for sentiment in sentiments:
    filtered = filter_sentiment(rq6_viz2, sentiment)

    # donut traces
    for col_idx, outlet in enumerate(outlets, start=1):
        donut_data = prepare_donut_data(filtered, outlet)
        colors = [country_color_map.get(c, "#CCCCCC") for c in donut_data["country"]]

        trace = go.Pie(
            labels=donut_data["country"],
            values=donut_data["count"],
            hole=0.58,
            sort=False,
            marker=dict(colors=colors, line=dict(color="white", width=1)),
            textinfo="percent",
            textposition="inside",
            hovertemplate=(
                "<b>Country:</b> %{label}<br>"
                "<b>Articles:</b> %{value}<br>"
                "<b>Share:</b> %{percent}<extra></extra>"
            ),
            showlegend=False,
            visible=(sentiment == "Positive")
        )
        fig2.add_trace(trace, row=1, col=col_idx)
        pie_trace_map[sentiment].append(len(fig2.data) - 1)

    # legend traces
    for country in top_legend_countries(filtered):
        trace = go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=10, color=country_color_map.get(country, "#CCCCCC")),
            name=country,
            showlegend=True,
            hoverinfo="skip",
            visible=(sentiment == "Positive")
        )
        fig2.add_trace(trace)
        legend_trace_map[sentiment].append(len(fig2.data) - 1)

buttons = []
for sentiment in sentiments:
    visible_mask = [False] * len(fig2.data)
    for idx in pie_trace_map[sentiment] + legend_trace_map[sentiment]:
        visible_mask[idx] = True

    buttons.append(
        dict(
            label=sentiment,
            method="update",
            args=[
                {"visible": visible_mask},
                {
                    "title.text": f"Distribution of {sentiment.lower()} country-related articles by outlet (excluding Germany)"
                }
            ]
        )
    )

fig2.update_layout(
    title=dict(
        text="Distribution of positive country-related articles by outlet (excluding Germany)",
        x=0.5,
        xanchor="center"
    ),
    template="plotly_white",
    margin=dict(t=150, b=70, l=40, r=40),
    updatemenus=[
        dict(
            type="buttons",
            direction="right",
            buttons=buttons,
            x=0.5,
            xanchor="center",
            y=1.18,
            showactive=True
        )
    ],
    legend=dict(title="Top 8 countries", x=1.02, y=0.5, yanchor="middle")
)

fig2.update_xaxes(visible=False)
fig2.update_yaxes(visible=False)

st.plotly_chart(fig2, use_container_width=True)

st.markdown("""
### Interpretation
This donut chart shows how positive, negative or neutral country-related articles are distributed across countries in Tagesschau and ZDF, excluding Germany. Germany was removed because it appears much more often in the dataset and would otherwise dominate the visualisation. 
For each selected sentiment, the chart highlights which countries make up the largest share of coverage in each outlet, while smaller country groups are combined into “Others.” This makes it easier to compare whether positive, negative or neutral country-related coverage is concentrated on the same countries in both broadcasters or distributed differently.""")

st.divider()

# --------------------------------------------------
# Visualization 3
# --------------------------------------------------
import plotly.express as px

rq6_viz3 = df.copy()

exclude_labels_viz3 = {"World", "Europe", "Asia", "Middle East", "European Union", "Germany"}
rq6_viz3 = rq6_viz3[~rq6_viz3["country"].isin(exclude_labels_viz3)].copy()

all_countries = sorted(rq6_viz3["country"].dropna().unique())
palette = px.colors.qualitative.Alphabet + px.colors.qualitative.Dark24
country_color_map = {country: palette[i % len(palette)] for i, country in enumerate(all_countries)}
country_color_map["Others"] = "#D3D3D3"

def get_sentiment_df(data, sentiment):
    if sentiment == "Positive":
        return data[data["tone"] > 1].copy()
    if sentiment == "Negative":
        return data[data["tone"] < -1].copy()
    return data[(data["tone"] >= -1) & (data["tone"] <= 1)].copy()

def prepare_treemap_data_with_others(data, outlet_name, top_n=25):
    outlet_data = data[data["outlet"] == outlet_name]
    counts = (
        outlet_data.groupby("country")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    top = counts.head(top_n).copy()
    rest_sum = counts.iloc[top_n:]["count"].sum()

    if rest_sum > 0:
        others_df = pd.DataFrame({"country": ["Others"], "count": [rest_sum]})
        top = pd.concat([top, others_df], ignore_index=True)

    return top

sentiments = ["Negative", "Neutral", "Positive"]
outlets = ["Tagesschau", "ZDF"]

fig3 = go.Figure()
trace_indices = {s: [] for s in sentiments}

for sentiment in sentiments:
    filtered_sentiment = get_sentiment_df(rq6_viz3, sentiment)

    for outlet in outlets:
        plot_data = prepare_treemap_data_with_others(filtered_sentiment, outlet, top_n=25)
        node_colors = [country_color_map.get(c, "#BEBEBE") for c in plot_data["country"]]

        trace = go.Treemap(
            ids=[f"{outlet}-{country}" for country in plot_data["country"]],
            labels=plot_data["country"],
            parents=[""] * len(plot_data),
            values=plot_data["count"],
            branchvalues="total",
            marker=dict(colors=node_colors, line=dict(color="white", width=2)),
            textinfo="label+value",
            hovertemplate=(
                "<b>Outlet:</b> " + outlet +
                "<br><b>Country:</b> %{label}"
                "<br><b>Articles:</b> %{value}<extra></extra>"
            ),
            visible=(sentiment == "Negative"),
            domain={"x": [0, 0.49] if outlet == "Tagesschau" else [0.51, 1], "y": [0, 1]}
        )

        fig3.add_trace(trace)
        trace_indices[sentiment].append(len(fig3.data) - 1)

buttons = []
for sentiment in sentiments:
    visible_mask = [False] * len(fig3.data)
    for idx in trace_indices[sentiment]:
        visible_mask[idx] = True

    buttons.append(
        dict(
            label=sentiment,
            method="update",
            args=[
                {"visible": visible_mask},
                {"title.text": f"Top 25 {sentiment.lower()} country-related articles by outlet (excluding Germany)"}
            ]
        )
    )

fig3.update_layout(
    title=dict(
        text="Top 25 negative country-related articles by outlet (excluding Germany)",
        x=0.5,
        y=0.98,
        xanchor="center",
        yanchor="top",
        font=dict(size=20)
    ),
    template="plotly_white",
    margin=dict(t=180, b=20, l=20, r=20),
    updatemenus=[
        dict(
            type="buttons",
            direction="right",
            buttons=buttons,
            x=0.5,
            xanchor="center",
            y=1.15,
            yanchor="top",
            showactive=True
        )
    ],
    annotations=[
        dict(x=0.245, y=1.05, text="<b>Tagesschau</b>", showarrow=False,
             xref="paper", yref="paper", font=dict(size=16)),
        dict(x=0.755, y=1.05, text="<b>ZDF</b>", showarrow=False,
             xref="paper", yref="paper", font=dict(size=16))
    ]
)

st.plotly_chart(fig3, use_container_width=True)

st.markdown("""
### Interpretation
This treemap highlights which countries appear most often within negative, neutral or positive country-related coverage in each outlet, excluding Germany. Larger boxes represent countries with more articles. The chart makes it easy to see which countries dominate each sentiment category and whether Tagesschau and ZDF emphasise different countries within the same sentiment.
""")