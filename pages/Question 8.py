# Datei: pages/2_RQ4_Top_Actors.py
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="RQ4 | Top Actors by Event", layout="wide")

# --------------------------------------------------
# RQ4 – Titel & Beschreibung
# --------------------------------------------------
st.markdown("""
### Research Question 4
How frequently are specific political leaders (Merz, Trump, Biden, and Scholz) associated with positive and negative tone in news coverage across two legislative periods? 
""")

st.divider()

# --------------------------------------------------
# Daten laden
# --------------------------------------------------
@st.cache_data
def load_rq4_event_actor_top():
    # Pfad anpassen, je nachdem, wo du die Datei abgelegt hast
    return pd.read_csv("data/rq4_event_actor_top.csv")

event_actor_top = load_rq4_event_actor_top()

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
# UI: Event-Auswahl
# --------------------------------------------------
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
        This visualization shows the most frequently mentioned actors for the selected event type,
        based on the total number of related news articles.
        """
    )

st.divider()

# --------------------------------------------------
# Daten für Auswahl filtern
# --------------------------------------------------
df_sel = (
    event_actor_top[event_actor_top["EventLabel"] == selected_event]
    .sort_values("total_articles", ascending=False)
    .head(top_k)
)

if df_sel.empty:
    st.warning("No actors found for this event.")
else:
    fig = px.bar(
        df_sel,
        x="total_articles",
        y="ActorName",
        color="ActorName",
        orientation="h",
        color_discrete_sequence=px.colors.sequential.Blues_r,
        title=f"Top {top_k} actors for '{selected_event}'",
        labels={
            "total_articles": "Total Articles",
            "ActorName": "Actor",
        },
        height=500,
    )

    fig.update_layout(
        xaxis_title="Total number of articles",
        yaxis_title="Actor",
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    fig.update_traces(
        hovertemplate="Actor: %{y}<br>Total Articles: %{x}<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"""
    The chart above highlights which actors dominate coverage for the event type
    **{selected_event}**, based on the number of associated articles.
    """)

st.divider()
