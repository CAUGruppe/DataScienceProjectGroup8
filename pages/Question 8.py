import streamlit as st
import pandas as pd
import plotly.express as px


st.set_page_config(page_title="RQ8 | Events & Top Actors", layout="wide")


# --------------------------------------------------
# RQ8 – Titel & Beschreibung
# --------------------------------------------------
st.markdown("""
### Research Question 8  
Which events generate the most media attention in German media outlets, and which actors are most frequently associated with these events?
""")


st.divider()


# --------------------------------------------------
# Daten laden
# --------------------------------------------------
@st.cache_data
def load_rq8_event_actor_top():
    # Pfad anpassen, je nachdem, wo du die Datei abgelegt hast
    return pd.read_csv("/Users/beytuygt/DataScienceProjectGroup8/Data/rq8_event_actor_top.csv")


@st.cache_data
def load_rq8_top_events():
    # Pfad ggf. an Projektstruktur anpassen
    return pd.read_csv("/Users/beytuygt/DataScienceProjectGroup8/Data/rq8_top_events_labeled.csv")


@st.cache_data
def load_rq8_events_non_unknown():
    return pd.read_csv("/Users/beytuygt/DataScienceProjectGroup8/Data/rq8_events_non_unknown.csv")


event_actor_top = load_rq8_event_actor_top()


# Datentypen normalisieren
event_actor_top["EventCode"] = event_actor_top["EventCode"].astype(str)


# Liste der auswählbaren Events
event_options = (
    event_actor_top["EventLabel"]
    .dropna()
    .unique()
)
event_options = sorted(event_options)


# --------------------------------------------------
# FIGURE 1: Bubble-Chart über alle nicht-unknown Events
# --------------------------------------------------
events_non_unknown = load_rq8_events_non_unknown()

st.markdown("### Event types: attention and tone")

max_articles_global = int(events_non_unknown["total_articles"].max())

col_min, col_max = st.columns(2)

with col_min:
    min_articles = st.slider(
        "Minimum number of articles per event type",
        min_value=0,
        max_value=max_articles_global,
        value=500,
        step=100,
    )

with col_max:
    max_articles = st.slider(
        "Maximum number of articles per event type",
        min_value=min_articles,          # darf nicht kleiner als min sein
        max_value=max_articles_global,
        value=max_articles_global,
        step=100,
    )

events_filtered = events_non_unknown[
    (events_non_unknown["total_articles"] >= min_articles)
    & (events_non_unknown["total_articles"] <= max_articles)
].copy()

if events_filtered.empty:
    st.warning("No event types match the current filter.")
else:
    fig_events = px.scatter(
        events_filtered,
        x="avg_tone",
        y="total_articles",
        size="total_articles",
        color="avg_tone",
        hover_name="EventDescription",
        hover_data={
            "EventCode": True,
            "num_event_rows": True,
            "total_articles": False,
            "avg_tone": False,
        },
        color_continuous_scale="Viridis",
        title="Media attention and average tone across event types",
        labels={
            "avg_tone": "Average tone",
            "total_articles": "Total Articles",
        },
        height=700,
    )

    fig_events.update_traces(
        marker=dict(
            sizemode="area",
            sizeref=events_filtered["total_articles"].max() / (40**2),
            line=dict(width=1.2, color="#333333"),
            opacity=0.9,
        ),
        hovertemplate=(
            "Event: %{hovertext}<br>"
            "EventCode: %{customdata[0]}<br>"
            "Total Articles: %{y:,}<br>"
            "Avg tone: %{x:.2f}<extra></extra>"
        ),
    )

    fig_events.update_layout(
        xaxis=dict(
            zeroline=True,
            zerolinecolor="lightgray",
        ),
        yaxis=dict(
            title="Total Articles",
            tickformat=",",
        ),
        coloraxis_colorbar=dict(title="Avg tone"),
        plot_bgcolor="#f5f5f8",
        paper_bgcolor="white",
        margin=dict(l=80, r=40, t=80, b=60),
    )

    st.plotly_chart(fig_events, use_container_width=True)

st.markdown("""
### Interpretation
This bubble chart show each event type by its average tone and the total number of related articles where larger bubbles represent events with higher overall media attention and the color indicates the average tone. In Addition to that the sliders allow you to adjust the range of total articles.\n
            
""")
st.divider()


# --------------------------------------------------
# FIGURE 2: Event-Auswahl für Top-Actors
# --------------------------------------------------
st.markdown("### Top actors per event type")

col1, col2 = st.columns([2, 3])

with col1:
    selected_event = st.selectbox(
        "Select event type:",
        options=event_options,
        index=0,
    )

    top_k = st.slider(
        "Number of actors to display",
        min_value=3,
        max_value=20,
        value=10,
        step=1,
    )

with col2:
    st.markdown(
        """
        This visualization shows the actors most frequently mentioned for the selected event type,
        based on the total number of related news articles.
        """
    )

st.divider()


# --------------------------------------------------
# Daten für Auswahl filtern (Top Actors)
# --------------------------------------------------
df_sel = (
    event_actor_top[event_actor_top["EventLabel"] == selected_event]
    .sort_values("total_articles", ascending=False)
    .head(top_k)
)

if df_sel.empty:
    st.warning("No actors found for this event.")
else:
    df_sel = df_sel.sort_values("total_articles", ascending=False)

    fig = px.pie(
        df_sel,
        names="ActorName",
        values="total_articles",
        hole=0.5,  # 0 = klassische Torte, 0.5 = Donut
        title=f"Top {top_k} actors for '{selected_event}'",
        color="ActorName",
        color_discrete_sequence=px.colors.sequential.Blues_r,
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate=(
            "Actor: %{label}<br>"
            "Total Articles: %{value}<br>"
            "Share: %{percent}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=80, b=40, l=40, r=40),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"""
    The chart above highlights which actors dominate coverage for the event type
    **{selected_event}**, based on the number of associated articles.
    """)

st.divider()
