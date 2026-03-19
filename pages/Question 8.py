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
rq8_top_events = load_rq8_top_events()
rq8_events_non_unknown = load_rq8_events_non_unknown()
events_tone = rq8_events_non_unknown[["EventCode", "avg_tone"]].copy()
events_tone["EventCode"] = events_tone["EventCode"].astype(str)

event_actor_with_tone = event_actor_top.merge(
    events_tone,
    on="EventCode",
    how="left",
)
top_k_3d = 20
actors_agg = (
    event_actor_with_tone
    .groupby("ActorName", as_index=False)
    .agg(
        total_articles=("total_articles", "sum"),
        avg_tone=("avg_tone", "mean"),      # Durchschnitt über alle Eventtypen
        num_events=("EventCode", "nunique") # in wie vielen Eventtypen Actor vorkommt
    )
    .sort_values("total_articles", ascending=False)
    .head(top_k_3d)
)
top_k_overall = 15  # oder 10 – wie du magst

top_actors_overall = (
    event_actor_top
    .groupby("ActorName", as_index=False)["total_articles"]
    .sum()
    .sort_values("total_articles", ascending=False)
    .head(top_k_overall)
)

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
This bubble chart shows each event type by its average tone and the total number of related articles where larger bubbles represent events with higher overall media attention and the color indicates the average tone. In Addition to that the sliders allow you to adjust the range of total articles.
       We can identify that most event types with high media attention tend to have a negative average tone, which may reflect the nature of news reporting that often focuses on conflicts, crises, and other negative events. However, there are also some event types with a more neutral or slightly positive tone, indicating that not all widely covered events are negative. The distribution of bubbles can help us understand which types of events are most prominent in the media and how they are generally portrayed in terms of sentiment.     
""")
st.divider()

# --------------------------------------------------
# FIGURE 2: Top-Actors Overall
# --------------------------------------------------

st.markdown("### Top actors overall: attention, tone, and event spread")

if actors_agg.empty:
    st.warning("No actors found for 3D view.")
else:
    fig_3d = px.scatter_3d(
        actors_agg,
        x="avg_tone",          # Tone
        y="total_articles",    # Artikel
        z="num_events",        # Event-Typen
        size="total_articles",
        color="avg_tone",
        hover_name="ActorName",
        hover_data={
            "total_articles": True,
            "avg_tone": True,
            "num_events": True,
        },
        color_continuous_scale="Viridis",
        title=f"Top {top_k_3d} actors: media attention, tone, and event spread",
        height=700,
    )

    max_size = actors_agg["total_articles"].max()

    fig_3d.update_traces(
        marker=dict(
            sizemode="diameter",
            sizeref=max_size / (10**2),  # größerer Wert -> kleinere Bubbles
            sizemin=3,
            line=dict(width=1.0, color="#333333"),
            opacity=0.85,
        ),
        hovertemplate=(
            "Actor: %{hovertext}<br>"
            "Total Articles: %{y}<br>"
            "Avg tone: %{x:.2f}<br>"
            "Event types: %{z}<extra></extra>"
        ),
    )

    fig_3d.update_layout(
        scene=dict(
            xaxis_title="Average tone",
            yaxis_title="Total Articles",
            zaxis_title="Number of event types",
        ),
        margin=dict(l=0, r=0, t=80, b=0),
    )

    st.plotly_chart(fig_3d, use_container_width=True)

st.markdown("""
### Interpretation
Media attention is highly concentrated on a few key actors who appear across many different event types. As an example, Ukraine provides a good example for this pattern. With 5513 articles across 55 event types, Ukraine is the most covered actor in our dataset, reflecting its central role in german news during the period analyzed. The average tone for Ukraine is -3.60, indicating that the coverage is mostly negative, likely due to the ongoing conflict and associated crises. This highlights how certain actors can dominate media attention and how their portrayal can be shaped by the nature of the events they are involved in.
            """)

st.divider()
# --------------------------------------------------
# FIGURE 3: Event-Auswahl für Top-Actors
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

st.markdown("""
### Interpretation
The chart makes it possible to see wether attention is concentrated on a few key actors or distributed across many different actors and how the acotr landscape changes between different event types.
            """)

st.divider()

st.markdown("""
### Overall Answer of RQ8
Across all event types a few events dominate media attention and these events tend to have a more negative average tone. At the same time, within each event type a small set of actors dominate the coverage, reflecting the media's focus on key figures associated with major events. This suggests that media attention is often concentrated on a few high-profile events and actors, which can shape public perception and discourse around these topics. Use of Unconvetional Mass Violence is the most frequent event type covering over 10.000 articles in the dataset. It refers to extreme forms of material violence such as mass killings, large-scale violent acts and so on. The top actor associated with this event type is Ukraine due to the ongoing conflict and war.
            """)