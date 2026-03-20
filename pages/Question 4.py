import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import utils


# --------------------------------------------------
# Grundkonfiguration
# --------------------------------------------------
st.set_page_config(page_title="RQ4 | Leaders & Tone", layout="wide")

st.markdown("""
### Research Question 4  
How frequently are specific political leaders (Merz, Trump, Biden, and Scholz) associated with positive and negative tone in news coverage across two legislative periods?
""")

st.divider()

# --------------------------------------------------
# Daten laden & vorbereiten
# --------------------------------------------------
@st.cache_data
def load_rq4_data():
    df = utils.load_data_rq4().copy()

    df["Datetime"] = pd.to_datetime(
        df["DATE"].astype(str).str[:14], format="%Y%m%d%H%M%S"
    )
    df["Date"] = df["Datetime"].dt.date
    df["Tone"] = df["V2Tone"].str.split(",").str[0].astype(float)

    leaders = ["Biden", "Trump", "Scholz", "Merz"]

    def extract_leader(persons_str):
        if not isinstance(persons_str, str):
            return None
        for leader in leaders:
            if leader in persons_str:
                return leader
        return None

    df["Leader"] = df["V2Persons"].apply(extract_leader)
    leaders_df = df[df["Leader"].notna()].copy()
    leaders_df["Date"] = pd.to_datetime(leaders_df["Date"])

    tone_bins = [-100, -0.01, 0.01, 100]
    tone_labels = ["Negative", "Neutral/none", "Positive"]
    leaders_df["ToneCategory"] = pd.cut(
        leaders_df["Tone"],
        bins=tone_bins,
        labels=tone_labels,
        right=True,
    )

    leaders_country = {
        "Scholz": "DE",
        "Merz": "DE",
        "Biden": "US",
        "Trump": "US",
    }
    leaders_df["Country"] = leaders_df["Leader"].map(leaders_country)

    def map_german_period(ts):
        ts = pd.Timestamp(ts)
        if pd.Timestamp("2021-12-08") <= ts <= pd.Timestamp("2025-05-06"):
            return "PeriodDE1"
        elif pd.Timestamp("2025-05-06") <= ts <= pd.Timestamp("2026-03-16"):
            return "PeriodDE2"
        else:
            return "OutsideDE"

    def map_us_period(ts):
        ts = pd.Timestamp(ts)
        if pd.Timestamp("2021-12-08") <= ts <= pd.Timestamp("2025-01-20"):
            return "PeriodUS1"
        elif pd.Timestamp("2025-01-20") <= ts <= pd.Timestamp("2026-03-16"):
            return "PeriodUS2"
        else:
            return "OutsideUS"

    leaders_df["PeriodLegis"] = None
    mask_de = leaders_df["Country"] == "DE"
    mask_us = leaders_df["Country"] == "US"
    leaders_df.loc[mask_de, "PeriodLegis"] = leaders_df.loc[mask_de, "Date"].apply(
        map_german_period
    )
    leaders_df.loc[mask_us, "PeriodLegis"] = leaders_df.loc[mask_us, "Date"].apply(
        map_us_period
    )

    valid_periods = ["PeriodDE1", "PeriodDE2", "PeriodUS1", "PeriodUS2"]
    leaders_df = leaders_df[leaders_df["PeriodLegis"].isin(valid_periods)].copy()

    period_label_map = {
        "PeriodDE1": "08.12.2021 – 06.05.2025",
        "PeriodDE2": "06.05.2025 – 16.03.2026",
        "PeriodUS1": "08.12.2021 – 20.01.2025",
        "PeriodUS2": "20.01.2025 – 16.03.2026",
    }

    counts = (
        leaders_df
        .groupby(["Leader", "PeriodLegis", "ToneCategory"], as_index=False, observed=True)
        .size()
        .rename(columns={"size": "NumArticles"})
    )

    counts_pct = counts.copy()
    counts_pct["TotalLeaderPeriod"] = counts_pct.groupby(
        ["Leader", "PeriodLegis"]
    )["NumArticles"].transform("sum")
    counts_pct["Pct"] = 100 * counts_pct["NumArticles"] / counts_pct["TotalLeaderPeriod"]
    counts_pct["PeriodLabel"] = counts_pct["PeriodLegis"].map(period_label_map)

    totals_de_us = (
        leaders_df
        .groupby(["Country", "ToneCategory"], as_index=False, observed=True)
        .size()
        .rename(columns={"size": "NumArticles"})
    )

    return counts_pct, totals_de_us


counts_pct, totals_de_us = load_rq4_data()

# Ordnung & Farben
# Ordnung & Farben
tone_order = ["Positive", "Negative", "Neutral/none"]
leader_order = ["Scholz", "Merz", "Biden", "Trump"]

tone_colors = {
    "Positive": "seagreen",
    "Negative": "firebrick",
    "Neutral/none": "gray",
}

# Mapping für schöne Perioden-Titel
period_title_map = {
    "08.12.2021 – 06.05.2025": "Legislative Period (Scholz): 08.12.2021–06.05.2025",
    "06.05.2025 – 16.03.2026": "Legislative Period (Merz): 06.05.2025–16.03.2026",
    "08.12.2021 – 20.01.2025": "Legislative Period (Biden): 08.12.2021–20.01.2025",
    "20.01.2025 – 16.03.2026": "Legislative Period (Trump): 20.01.2025–16.03.2026",
}

# --------------------------------------------------
# FIGURE 1: Stacked Bar – Tone per Leader & Legislative Period
# --------------------------------------------------
st.markdown("### Tone per leader and legislative period")

leader_group = st.radio(
    "Select leader group",
    options=["Germany (Scholz, Merz)", "US (Biden, Trump)"],
    index=0,
    horizontal=True,
)

if leader_group == "Germany (Scholz, Merz)":
    selected_leaders = ["Scholz", "Merz"]
else:
    selected_leaders = ["Biden", "Trump"]

df_long = counts_pct[
    counts_pct["ToneCategory"].isin(tone_order)
    & counts_pct["Leader"].isin(selected_leaders)
].copy()

df_long["Leader"] = pd.Categorical(
    df_long["Leader"], categories=selected_leaders, ordered=True
)
df_long["ToneCategory"] = pd.Categorical(
    df_long["ToneCategory"], categories=tone_order, ordered=True
)

small_screen = st.checkbox(
    "Use stacked layout (better on small screens)",
    value=False,
)

base_height = 380
height = base_height + 60 * (len(selected_leaders) - 2)

if not small_screen:
    # Facet-Layout
    fig_bar = px.bar(
        df_long,
        x="Leader",
        y="Pct",
        color="ToneCategory",
        barmode="stack",
        facet_col="PeriodLabel",
        facet_col_spacing=0.09,
        category_orders={
            "Leader": selected_leaders,
            "ToneCategory": tone_order,
        },
        color_discrete_map=tone_colors,
        height=height,
        labels={
            "Pct": "Share of tone categories",
            "Leader": "Leader",
            "ToneCategory": "Tone category",
            "PeriodLabel": "Legislative period",
        },
        custom_data=["PeriodLabel", "ToneCategory", "NumArticles"],
    )

    fig_bar.update_traces(
        hovertemplate=(
            "Leader: %{x}<br>"
            "Period: %{customdata[0]}<br>"
            "Tone: %{customdata[1]}<br>"
            "Articles: %{customdata[2]:,}<br>"
            "Share: %{y:.1f}%<extra></extra>"
        ),
    )

    fig_bar.update_yaxes(
        title="Share of tone categories",
        matches=None,
        showticklabels=True,
    )
    fig_bar.update_xaxes(title="Leader")

    fig_bar.update_layout(
        legend_title_text="Tone category",
        margin=dict(l=10, r=10, t=60, b=40),
    )

    # Facet-Annotationen "Legislative period = ..." durch period_title_map ersetzen
    def _update_ann(a):
        # a.text z.B. "Legislative period = 08.12.2021 – 06.05.2025"
        val = a.text.split("=")[-1].strip()
        a.update(text=period_title_map.get(val, val))

    fig_bar.for_each_annotation(_update_ann)

    st.plotly_chart(fig_bar, use_container_width=True)

else:
    # Stacked layout: je legislative period ein eigenes Chart untereinander
    for period_label in sorted(df_long["PeriodLabel"].unique()):
        sub = df_long[df_long["PeriodLabel"] == period_label].copy()
        if sub.empty:
            continue

        # auch hier period_title_map nutzen
        title_text = period_title_map.get(
            period_label, f"Legislative period: {period_label}"
        )

        fig_bar_single = px.bar(
            sub,
            x="Leader",
            y="Pct",
            color="ToneCategory",
            barmode="stack",
            category_orders={
                "Leader": selected_leaders,
                "ToneCategory": tone_order,
            },
            color_discrete_map=tone_colors,
            height=height,
            labels={
                "Pct": "Share of tone categories",
                "Leader": "Leader",
                "ToneCategory": "Tone category",
            },
            title=title_text,
            custom_data=["ToneCategory", "NumArticles"],
        )

        fig_bar_single.update_traces(
            hovertemplate=(
                "Leader: %{x}<br>"
                "Tone: %{customdata[0]}<br>"
                "Articles: %{customdata[1]:,}<br>"
                "Share: %{y:.1f}%<extra></extra>"
            ),
        )

        fig_bar_single.update_yaxes(
            title="Share of tone categories",
            showticklabels=True,
        )
        fig_bar_single.update_xaxes(title="Leader")

        fig_bar_single.update_layout(
            legend_title_text="Tone category",
            margin=dict(l=10, r=10, t=50, b=40),
        )

        st.plotly_chart(fig_bar_single, use_container_width=True)

st.markdown("""
### Interpretation
This stacked bar chart shows, for each leader and legislative period, the share of positive, negative, and neutral coverage in the news. This allows us to compare not only how strongly each leader is criticized or praised overall, but also how these tone patterns change between the first and second legislative periods in Germany and the United States. As an example, it shows that articles about Merz were more positive when Scholz was chancellor than they are now with Merz as chancellor.
""")

st.divider()

# --------------------------------------------------
# FIGURE 2: Overall tone distribution for DE vs US leaders
# --------------------------------------------------
st.markdown("### Overall tone distribution across all leaders and periods")

de_totals = totals_de_us[totals_de_us["Country"] == "DE"].copy()
us_totals = totals_de_us[totals_de_us["Country"] == "US"].copy()

de_totals = (
    de_totals.set_index("ToneCategory")
    .reindex(tone_order)
    .dropna(subset=["NumArticles"])
)
us_totals = (
    us_totals.set_index("ToneCategory")
    .reindex(tone_order)
    .dropna(subset=["NumArticles"])
)

fig_pies = make_subplots(
    rows=1,
    cols=2,
    specs=[[{"type": "domain"}, {"type": "domain"}]],
    subplot_titles=("Biden & Trump", "Scholz & Merz"),
)

fig_pies.add_trace(
    go.Pie(
        labels=us_totals.index,
        values=us_totals["NumArticles"],
        name="Biden & Trump",
        marker=dict(colors=[tone_colors[t] for t in us_totals.index]),
        hovertemplate=(
            "Tone: %{label}<br>"
            "Number of Articles: %{value}<br>"
            "Share: %{percent}<extra></extra>"
        ),
    ),
    row=1,
    col=1,
)

fig_pies.add_trace(
    go.Pie(
        labels=de_totals.index,
        values=de_totals["NumArticles"],
        name="Scholz & Merz",
        marker=dict(colors=[tone_colors[t] for t in de_totals.index]),
        hovertemplate=(
            "Tone: %{label}<br>"
            "Number of Articles: %{value}<br>"
            "Share: %{percent}<extra></extra>"
        ),
    ),
    row=1,
    col=2,
)

fig_pies.update_layout(
    title_text="Tone distribution over entire dataset (08.12.2021–16.03.2026)",
    legend_title_text="Tone category",
    margin=dict(l=40, r=40, t=80, b=40),
)

st.plotly_chart(fig_pies, use_container_width=True)

st.markdown("""
### Interpretation
These charts summarize the overall tone distribution for US leaders (Biden and Trump) and German leaders (Scholz and Merz) across the entire dataset period. They show whether coverage is predominantly negative, positive, or neutral for each country bloc, and how large the neutral segment is compared to clearly evaluative reporting. When interpreting these results, we need to be careful: although it may look as if both country groups have similar tone distributions, we have to keep in mind that there are far more articles about Biden and Trump in the dataset than about Scholz and Merz.
""")

st.divider()

# --------------------------------------------------
# FIGURE 3: Tone distribution per leader & period (small multiples)
# --------------------------------------------------
st.markdown("### Tone distribution by leader and legislative period")

leaders_order = ["Scholz", "Merz", "Biden", "Trump"]
periods_order = ["PeriodDE1", "PeriodDE2", "PeriodUS1", "PeriodUS2"]

leader_period_map = {
    "Scholz": ["PeriodDE1", "PeriodDE2"],
    "Merz": ["PeriodDE1", "PeriodDE2"],
    "Biden": ["PeriodUS1", "PeriodUS2"],
    "Trump": ["PeriodUS1", "PeriodUS2"],
}

period_label_map = {
    "PeriodDE1": "08.12.2021 – 06.05.2025",
    "PeriodDE2": "06.05.2025 – 16.03.2026",
    "PeriodUS1": "08.12.2021 – 20.01.2025",
    "PeriodUS2": "20.01.2025 – 16.03.2026",
}

nrows = len(leaders_order)
ncols = 2
vgap = 0.09
usable_height = (1 - vgap * (nrows - 1)) / nrows

fig_small = go.Figure()
annotations = []

for i, leader in enumerate(leaders_order):
    perlist = leader_period_map[leader]
    for j in range(ncols):
        if j >= len(perlist):
            continue

        per = perlist[j]
        sub = counts_pct[
            (counts_pct["Leader"] == leader)
            & (counts_pct["PeriodLegis"] == per)
            & (counts_pct["ToneCategory"].isin(tone_order))
        ].copy()

        if sub.empty or sub["NumArticles"].fillna(0).sum() == 0:
            continue

        x0 = j / ncols
        x1 = (j + 1) / ncols
        y0 = 1 - usable_height * (i + 1) - vgap * i
        y1 = 1 - usable_height * i - vgap * i

        fig_small.add_trace(
            go.Pie(
                labels=sub["ToneCategory"],
                values=sub["NumArticles"],
                name=f"{leader} {per}",
                marker=dict(colors=[tone_colors[t] for t in sub["ToneCategory"]]),
                textinfo="percent+label",
                hovertemplate=(
                    f"Leader: {leader}<br>"
                    f"Period: {period_label_map.get(per, per)}<br>"
                    "Tone: %{label}<br>"
                    "Articles: %{value}<extra></extra>"
                ),
                domain=dict(x=[x0, x1], y=[y0, y1]),
                legendgroup="Tone",
                showlegend=(i == 0 and j == 0),
            )
        )

    annotations.append(
        dict(
            x=0.5,
            y=y1 + 0.02,
            xref="paper",
            yref="paper",
            text=leader,
            showarrow=False,
            xanchor="center",
            yanchor="bottom",
            font=dict(size=12),
        )
    )

fig_small.update_layout(
    height=260 * nrows,
    width=900,
    title_text="Tone distribution by leader and legislative period (donut charts)",
    legend_title_text="Tone category",
    annotations=annotations,
    margin=dict(l=40, r=40, t=80, b=40),
)

st.plotly_chart(fig_small, use_container_width=True)

st.markdown("""
### Overall answer to RQ4
Across both German and US legislative periods, news coverage of all four leaders is dominated by negative tone, with positive stories consistently forming a much smaller share and neutral coverage filling the remaining space. Within this overall pattern, there are marked differences: some leaders receive a particularly high share of negative articles in both periods, while others show more balanced or shifting tone profiles over time. This suggests that media narratives about political leaders are not only generally critical, but also shaped by country-specific contexts and changes between legislative periods, which can amplify or soften negative portrayals.
""")
