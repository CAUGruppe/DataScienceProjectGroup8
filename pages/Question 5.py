import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import utils

st.set_page_config(page_title="RQ5 | Government Framing", layout="wide")

# --------------------------------------------------
# RQ5
# --------------------------------------------------
st.markdown("""
### Research Question 5
How do the tone and framing of German media coverage of governments change during
national election periods compared with non-election periods?
""")

st.divider()

# --------------------------------------------------
# Load data
# --------------------------------------------------
@st.cache_data
def load_rq5_data():
    df = pd.read_csv(
        "tagesschau_zdf_pbs_events.csv",
        dtype={"EventCode": str},
        on_bad_lines="skip",
        low_memory=False,
    )
    df.columns = ["SQLDATE", "SOURCEURL", "AvgTone", "NumArticles",
                  "Actor1Name", "Actor2Name", "EventCode"]
    df["SQLDATE"] = pd.to_datetime(
        df["SQLDATE"].astype(str), format="%Y%m%d", errors="coerce"
    )
    return df

with st.spinner("Daten werden geladen..."):
    df_raw = load_rq5_data()

# --------------------------------------------------
# Prepare shared columns
# --------------------------------------------------
@st.cache_data
def prepare(_df):
    df = _df.copy()

    def label_outlet(url):
        url = str(url).lower()
        if "tagesschau.de" in url: return "Tagesschau"
        if "zdf.de" in url:        return "ZDF"
        return None

    df["Outlet"] = df["SOURCEURL"].map(label_outlet)
    df = df[df["Outlet"].notna()].copy()

    GOV_PATTERN = (
        r"GERMANY|GERMAN GOVERNMENT|GERMAN FEDERAL|BUNDESTAG|BUNDESRAT|"
        r"BUNDESREGIER|GERMAN CHANCELLOR|GERMAN MINISTER|GERMAN PARLIAMENT"
    )
    df_gov = df[
        df["Actor1Name"].fillna("").str.upper().str.contains(GOV_PATTERN, regex=True) |
        df["Actor2Name"].fillna("").str.upper().str.contains(GOV_PATTERN, regex=True)
    ].copy()

    return df_gov

df_gov = prepare(df_raw)

# --------------------------------------------------
# Shared config
# --------------------------------------------------
OUTLET_COLORS = {"Tagesschau": "#1565C0", "ZDF": "#E65100"}
OUTLETS       = ["Tagesschau", "ZDF"]

EVENTS = [
    {
        "label":     "Federal Election 2025 (23 Feb)",
        "prestart":  pd.Timestamp("2025-01-12"),
        "election":  pd.Timestamp("2025-02-23"),
        "postend":   pd.Timestamp("2025-03-23"),
        "color":     "#1565C0",
        "fillcolor": "rgba(21, 101, 192, 0.10)",
    },
    {
        "label":     "EU Election 2024 (9 Jun)",
        "prestart":  pd.Timestamp("2024-04-28"),
        "election":  pd.Timestamp("2024-06-09"),
        "postend":   pd.Timestamp("2024-07-07"),
        "color":     "#2E7D32",
        "fillcolor": "rgba(46, 125, 50, 0.10)",
    },
    {
        "label":     "Coalition Collapse (7 Nov)",
        "prestart":  pd.Timestamp("2024-10-28"),
        "election":  pd.Timestamp("2024-11-07"),
        "postend":   pd.Timestamp("2024-12-07"),
        "color":     "#B71C1C",
        "fillcolor": "rgba(183, 28, 28, 0.10)",
    },
]

EVENTS_ANIM = [
    {
        "label":    "Federal Election 2025",
        "prestart": pd.Timestamp("2025-01-12"),
        "postend":  pd.Timestamp("2025-03-23"),
        "color":    "rgba(21, 101, 192, 0.10)",
        "border":   "#1565C0",
    },
    {
        "label":    "EU Election 2024",
        "prestart": pd.Timestamp("2024-04-28"),
        "postend":  pd.Timestamp("2024-07-07"),
        "color":    "rgba(46, 125, 50, 0.10)",
        "border":   "#2E7D32",
    },
    {
        "label":    "Coalition Collapse",
        "prestart": pd.Timestamp("2024-10-28"),
        "postend":  pd.Timestamp("2024-12-07"),
        "color":    "rgba(183, 28, 28, 0.10)",
        "border":   "#B71C1C",
    },
]

# --------------------------------------------------
# Monthly aggregation (shared by all charts)
# --------------------------------------------------
@st.cache_data
def monthly_agg(_df_gov):
    df = _df_gov.copy()
    df["YearMonth"] = df["SQLDATE"].dt.to_period("M")
    monthly = (
        df.groupby(["Outlet", "YearMonth"])["AvgTone"]
        .agg(mean="mean", n="count")
        .reset_index()
    )
    monthly["Date"]      = monthly["YearMonth"].dt.to_timestamp()
    monthly["DateLabel"] = monthly["Date"].dt.strftime("%b %Y")
    monthly = monthly[monthly["n"] >= 3].sort_values("Date")
    return monthly

monthly = monthly_agg(df_gov)

y_min = monthly["mean"].min() - 0.5
y_max = monthly["mean"].max() + 0.8

# ══════════════════════════════════════════════════════════════════
# Visualization 1 — Line Chart + Shaded Election Windows
# ══════════════════════════════════════════════════════════════════
fig1 = go.Figure()

# Shaded election windows
for ev in EVENTS:
    fig1.add_shape(
        type="rect", xref="x", yref="y",
        x0=ev["prestart"], x1=ev["postend"],
        y0=y_min,          y1=y_max,
        fillcolor=ev["fillcolor"],
        line=dict(width=0), layer="below",
    )
    fig1.add_shape(
        type="line", xref="x", yref="y",
        x0=ev["election"], x1=ev["election"],
        y0=y_min,          y1=y_max,
        line=dict(color=ev["color"], width=1.6, dash="dash"),
        layer="below",
    )
    fig1.add_annotation(
        x=ev["election"], y=y_max - 0.05,
        text=ev["label"], showarrow=False,
        font=dict(size=9, color=ev["color"]),
        yanchor="top", xanchor="center",
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor=ev["color"], borderwidth=1, borderpad=2,
    )

# Line traces per outlet
for outlet in OUTLETS:
    sub   = monthly[monthly["Outlet"] == outlet].sort_values("Date")
    color = OUTLET_COLORS[outlet]
    fig1.add_trace(go.Scatter(
        x=sub["Date"],
        y=sub["mean"],
        mode="lines+markers",
        name=outlet,
        line=dict(color=color, width=2.5),
        marker=dict(size=7, color=color, line=dict(color="white", width=1.5)),
        customdata=np.stack([sub["n"], sub["DateLabel"]], axis=1),
        hovertemplate=(
            f"<b>{outlet}</b><br>"
            "Month: %{customdata[1]}<br>"
            "Avg Tone: %{y:.2f}<br>"
            "Articles: %{customdata[0]:,}<extra></extra>"
        ),
    ))

fig1.add_hline(
    y=0, line_dash="dot", line_color="gray", line_width=1.2,
    annotation_text=" Neutral (0)", annotation_position="right",
    annotation_font=dict(color="gray", size=10),
)

n_ts  = len(df_gov[df_gov["Outlet"] == "Tagesschau"])
n_zdf = len(df_gov[df_gov["Outlet"] == "ZDF"])

fig1.update_layout(
    title="Tone of German Media Coverage of Government: Election Periods vs. Non-Election Periods",
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
                        {"title": "Tone of German Media Coverage of Government: Election Periods vs. Non-Election Periods"}
                    ]
                ),
                dict(
                    label="Tagesschau only",
                    method="update",
                    args=[
                        {"visible": [True, False]},
                        {"title": "Tone of Government Coverage — Tagesschau"}
                    ]
                ),
                dict(
                    label="ZDF only",
                    method="update",
                    args=[
                        {"visible": [False, True]},
                        {"title": "Tone of Government Coverage — ZDF"}
                    ]
                ),
            ],
            direction="down",
            showactive=True,
            x=1.02, xanchor="left",
            y=1.15, yanchor="top",
        )
    ],
    annotations=[
        dict(
            text=(
                f"Source: GDELT Events | Tagesschau n={n_ts:,}, ZDF n={n_zdf:,} | "
                "Shaded areas = election windows (6 weeks pre/post)"
            ),
            xref="paper", yref="paper", x=0.5, y=-0.14,
            showarrow=False, font=dict(size=10, color="gray"), xanchor="center",
        ),
    ],
)

st.plotly_chart(fig1, use_container_width=True)

st.markdown("""
### Interpretation
This line chart shows the monthly average tone of government-related coverage for
Tagesschau and ZDF, with shaded regions marking the three key political windows:
the EU Election (June 2024), the Coalition Collapse (November 2024), and the Federal
Election (February 2025). Both outlets remain consistently below zero, confirming
predominantly negative framing of government topics. Both outlets tend toward a
slightly elevated (less negative) tone during election periods compared to
non-election months — Tagesschau at –2.52 vs. –2.83 and ZDF at –2.28 vs. –3.06 —
suggesting a modest softening of framing during politically heightened periods.
""")

st.divider()

# ══════════════════════════════════════════════════════════════════
# Visualization 2 — Bubble Chart
# ══════════════════════════════════════════════════════════════════
max_n = monthly["n"].max()
monthly["BubbleSize"] = (monthly["n"] / max_n * 55).clip(lower=6)

fig2 = go.Figure()

for ev in EVENTS:
    fig2.add_shape(
        type="rect", xref="x", yref="y",
        x0=ev["prestart"], x1=ev["postend"],
        y0=y_min,          y1=y_max,
        fillcolor=ev["fillcolor"],
        line=dict(width=0), layer="below",
    )
    fig2.add_shape(
        type="line", xref="x", yref="y",
        x0=ev["election"], x1=ev["election"],
        y0=y_min,          y1=y_max,
        line=dict(color=ev["color"], width=1.6, dash="dash"),
        layer="below",
    )
    fig2.add_annotation(
        x=ev["election"], y=y_max - 0.05,
        text=ev["label"], showarrow=False,
        font=dict(size=9, color=ev["color"]),
        yanchor="top", xanchor="center",
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor=ev["color"], borderwidth=1, borderpad=2,
    )

for outlet in OUTLETS:
    df_out = monthly[monthly["Outlet"] == outlet].sort_values("Date")
    color  = OUTLET_COLORS[outlet]
    fig2.add_trace(go.Scatter(
        x=df_out["Date"], y=df_out["mean"],
        mode="markers", name=outlet,
        marker=dict(
            size=df_out["BubbleSize"],
            color=color, opacity=0.72,
            line=dict(color="white", width=1),
            sizemode="diameter",
        ),
        customdata=df_out["n"],
        hovertemplate=(
            f"<b>{outlet}</b><br>"
            "Month: %{x|%B %Y}<br>"
            "AvgTone: %{y:.2f}<br>"
            "Articles: %{customdata:,}<extra></extra>"
        ),
    ))

fig2.add_hline(
    y=0, line_dash="dot", line_color="gray", line_width=1.2,
    annotation_text=" Neutral (0)", annotation_position="right",
    annotation_font=dict(color="gray", size=10),
)

# Bubble size legend
ref_sizes = [50, 200, 500]
x_ref     = monthly["Date"].max() + pd.DateOffset(months=2)
fig2.add_annotation(
    x=x_ref, y=y_max - 0.1, text="Article Count",
    showarrow=False, font=dict(size=9, color="#555"), xanchor="center",
)
for i, ref_n in enumerate(ref_sizes):
    bubble_px = ref_n / max_n * 55
    y_pos     = y_max - 0.55 - i * 1.1
    fig2.add_trace(go.Scatter(
        x=[x_ref], y=[y_pos],
        mode="markers+text", showlegend=False, hoverinfo="skip",
        marker=dict(
            size=bubble_px, color="#9E9E9E", opacity=0.45,
            line=dict(color="#757575", width=1), sizemode="diameter",
        ),
        text=[f" {ref_n}"],
        textfont=dict(size=8.5, color="#555"),
        textposition="middle right",
    ))

fig2.update_layout(
    title=dict(
        text=(
            "Tone of German Media Coverage of Government:<br>"
            "Election Periods vs. Non-Election Periods (Tagesschau vs. ZDF)"
        ),
        font=dict(size=16, family="Arial"), x=0.5, xanchor="center",
    ),
    xaxis=dict(
        title="Month", tickformat="%b %Y",
        range=[
            monthly["Date"].min() - pd.DateOffset(months=1),
            monthly["Date"].max() + pd.DateOffset(months=5),
        ],
    ),
    yaxis=dict(title="Ø AvgTone Score", zeroline=False, gridcolor="#f0f0f0"),
    legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center", font=dict(size=13)),
    plot_bgcolor="white", paper_bgcolor="white",
    height=520, margin=dict(t=130, b=80, l=60, r=130),
    hovermode="closest",
    hoverlabel=dict(bgcolor="white", font_size=13, bordercolor="#cccccc"),
)

st.plotly_chart(fig2, use_container_width=True)

st.markdown("""
### Interpretation
This bubble chart encodes article volume as bubble size, making it easier to see
which months had more coverage. Tagesschau dominates in volume throughout, while
ZDF has fewer monthly data points. The spatial pattern confirms that tone slightly
improves during election windows, and the Coalition Collapse period is one of the
most negatively framed across both outlets.
""")

st.divider()

# ══════════════════════════════════════════════════════════════════
# Visualization 3 — Animated Bar Chart
# ══════════════════════════════════════════════════════════════════
def get_event_anim(date):
    for ev in EVENTS_ANIM:
        if ev["prestart"] <= date <= ev["postend"]:
            return ev
    return None

all_months = sorted(monthly["Date"].unique())
y_min2     = monthly["mean"].min() - 0.8
y_max2     = monthly["mean"].max() + 1.2

frames = []
for month in all_months:
    month_ts  = pd.Timestamp(month)
    month_str = month_ts.strftime("%b %Y")
    ev        = get_event_anim(month_ts)

    bar_data = []
    for outlet in OUTLETS:
        row = monthly[(monthly["Outlet"] == outlet) & (monthly["Date"] == month)]
        bar_data.append({
            "outlet":   outlet,
            "tone":     row["mean"].values[0] if len(row) > 0 else 0,
            "n":        row["n"].values[0]    if len(row) > 0 else 0,
            "has_data": len(row) > 0,
        })

    event_label = f" ⚑ {ev['label']}" if ev else ""

    frames.append(go.Frame(
        data=[
            go.Bar(
                x=[b["outlet"] for b in bar_data],
                y=[b["tone"] if b["has_data"] else 0 for b in bar_data],
                marker_color=[
                    OUTLET_COLORS[b["outlet"]] if b["has_data"] else "rgba(0,0,0,0)"
                    for b in bar_data
                ],
                marker_line=dict(color="white", width=1.5),
                opacity=0.85, width=0.45,
                text=[f"{b['tone']:.2f}" if b["has_data"] else "" for b in bar_data],
                textposition="outside",
                textfont=dict(
                    size=13,
                    color=[OUTLET_COLORS[b["outlet"]] for b in bar_data],
                ),
                customdata=[[b["n"]] for b in bar_data],
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    f"{month_str}<br>"
                    "AvgTone: %{y:.2f}<br>"
                    "Articles: %{customdata[0]:,}<extra></extra>"
                ),
            ),
            go.Scatter(
                x=["Tagesschau", "ZDF"], y=[0, 0],
                mode="lines",
                line=dict(color="gray", width=1.2, dash="dot"),
                hoverinfo="skip", showlegend=False,
            ),
        ],
        name=month_str,
        layout=go.Layout(
            title_text=(
                f"Monthly AvgTone – Government Coverage (RQ5)<br>"
                f"<span style='font-size:13px'>{month_str}{event_label}</span>"
            ),
            paper_bgcolor=ev["color"] if ev else "white",
        ),
    ))

first_month = all_months[0]
first_str   = pd.Timestamp(first_month).strftime("%b %Y")

init_data = []
for outlet in OUTLETS:
    row = monthly[(monthly["Outlet"] == outlet) & (monthly["Date"] == first_month)]
    init_data.append({
        "outlet":   outlet,
        "tone":     row["mean"].values[0] if len(row) > 0 else 0,
        "n":        row["n"].values[0]    if len(row) > 0 else 0,
        "has_data": len(row) > 0,
    })

fig3 = go.Figure(
    data=[
        go.Bar(
            x=[b["outlet"] for b in init_data],
            y=[b["tone"] if b["has_data"] else 0 for b in init_data],
            marker_color=[OUTLET_COLORS[b["outlet"]] for b in init_data],
            marker_line=dict(color="white", width=1.5),
            opacity=0.85, width=0.45,
            text=[f"{b['tone']:.2f}" if b["has_data"] else "" for b in init_data],
            textposition="outside",
            textfont=dict(size=13),
            customdata=[[b["n"]] for b in init_data],
            hovertemplate=(
                "<b>%{x}</b><br>"
                f"{first_str}<br>"
                "AvgTone: %{y:.2f}<br>"
                "Articles: %{customdata[0]:,}<extra></extra>"
            ),
        ),
        go.Scatter(
            x=["Tagesschau", "ZDF"], y=[0, 0],
            mode="lines",
            line=dict(color="gray", width=1.2, dash="dot"),
            hoverinfo="skip", showlegend=False,
        ),
    ],
    frames=frames,
)

fig3.update_layout(
    title=dict(
        text=(
            f"Monthly AvgTone – Government Coverage (RQ5)<br>"
            f"<span style='font-size:13px'>{first_str}</span>"
        ),
        font=dict(size=14, color="#1a1a2e"), x=0.5,
    ),
    xaxis=dict(
        categoryarray=["Tagesschau", "ZDF"],
        categoryorder="array", showgrid=False,
        title="Outlet",
    ),
    yaxis=dict(
        title="AvgTone Score", range=[y_min2, y_max2],
        gridcolor="#e8e8e8", zeroline=True,
        zerolinecolor="gray", zerolinewidth=1.2,
    ),
    plot_bgcolor="white", paper_bgcolor="white",
    width=680, height=500,
    margin=dict(t=120, b=80, l=60, r=40),
    updatemenus=[
        dict(
            type="buttons", showactive=False,
            x=0.02, xanchor="left", y=1.18, yanchor="top",
            buttons=[
                dict(
                    label="▶ Play",
                    method="animate",
                    args=[None, {
                        "frame":       {"duration": 700, "redraw": True},
                        "fromcurrent": True,
                        "transition":  {"duration": 300, "easing": "cubic-in-out"},
                    }],
                ),
                dict(
                    label="⏸ Pause",
                    method="animate",
                    args=[[None], {
                        "frame":      {"duration": 0, "redraw": False},
                        "mode":       "immediate",
                        "transition": {"duration": 0},
                    }],
                ),
            ],
        ),
    ],
    sliders=[
        dict(
            active=0,
            steps=[
                dict(
                    label=pd.Timestamp(m).strftime("%b %Y"),
                    method="animate",
                    args=[[pd.Timestamp(m).strftime("%b %Y")], {
                        "frame":      {"duration": 300, "redraw": True},
                        "mode":       "immediate",
                        "transition": {"duration": 200},
                    }],
                )
                for m in all_months
            ],
            x=0.0, y=0, len=1.0,
            xanchor="left", yanchor="top",
            currentvalue=dict(
                font=dict(size=12), prefix="Month: ",
                visible=True, xanchor="center",
            ),
            transition=dict(duration=300, easing="cubic-in-out"),
        ),
    ],
)

st.plotly_chart(fig3, use_container_width=True)

st.markdown("""
### Interpretation
This animated bar chart steps through each month to compare the average tone of
government coverage between Tagesschau and ZDF. The background tint changes colour
during election periods to signal politically heightened windows. Both outlets exhibit
slightly elevated tone during election run-up periods, with the Coalition Collapse
(November 2024) and the Federal Election 2025 standing out as the most distinct
phases in the time series.
""")

st.divider()
