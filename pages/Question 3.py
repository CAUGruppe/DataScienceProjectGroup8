import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
from sklearn.preprocessing import MinMaxScaler
import utils
# --- DATA PREPARATION ---
def prepare_data(df):
    # Explode Persons
    df_exploded = df.assign(V2Persons=df['V2Persons'].str.split(';')).explode('V2Persons')
    df_exploded['PersonName'] = df_exploded['V2Persons'].str.split(',').str[0].str.strip()
    
    blacklist = ['Los Angeles']
    df_exploded = df_exploded[~df_exploded['PersonName'].isin(blacklist)]
    return df_exploded

# --- VIZ 1: DEIN RADAR CHART (MATPLOTLIB) ---
def plot_radar_chart(df_exploded, selected_actors):
    metrics = ['tone', 'positive_score', 'negative_score', 'polarity', 'activity_density', 'self_group_density']
    
    # Filtern auf ausgewählte Personen
    profiles = df_exploded[df_exploded['PersonName'].isin(selected_actors)].groupby('PersonName')[metrics].mean()
    
  
    
    # Normalisierung
    scaler = MinMaxScaler()
    normalized_profiles = pd.DataFrame(
        scaler.fit_transform(profiles),
        columns=profiles.columns,
        index=profiles.index
    )
    
    num_vars = len(metrics)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, person in enumerate(normalized_profiles.index):
        values = normalized_profiles.loc[person].tolist()
        values += values[:1]
        ax.plot(angles, values, color=colors[i % len(colors)], linewidth=2, label=person, alpha=0.8)
        ax.fill(angles, values, color=colors[i % len(colors)], alpha=0.1)
    
    plt.xticks(angles[:-1], metrics, color='grey', size=10)
    ax.set_ylim(0, 1.1)
    plt.title('Media Fingerprint Comparison', size=15, fontweight='bold')
    plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))
    
    st.pyplot(fig)

# Bubble chart
def plot_dynamic_scatter(df_exploded, selected_actors):
    # Aggregation für die Visualisierung
    metrics = ['tone', 'activity_density', 'polarity']
    scatter_df = df_exploded[df_exploded['PersonName'].isin(selected_actors)].groupby('PersonName').agg({
        'tone': 'mean',
        'activity_density': 'mean',
        'PersonName': 'count'
    }).rename(columns={'PersonName': 'Mentions'}).reset_index()

    fig = px.scatter(
        scatter_df, 
        x="tone", 
        y="activity_density",
        size="Mentions", 
        color="PersonName",
        hover_name="PersonName",
        log_x=False, 
        size_max=60,
        title="Relation: Sentiment (Tone) vs. Activity Density",
        labels={'tone': 'Durchschnittlicher Ton', 'activity_density': 'Aktivitätsdichte'}
    )
    
    fig.update_layout(plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

# --- MAIN APP FLOW ---
st.set_page_config(page_title="Actor Analysis", layout="wide")



# Daten laden (deine utils verwenden!)
# import utils
df = utils.load_data() 
df['Date'] = pd.to_datetime(df['DATE'], format='%Y%m%d%H%M%S')


df['Year-Month'] = df['Date'].dt.strftime('%Y-%m')


df[['tone','positive_score','negative_score','polarity', 'activity_density','self_group_density','word_count']] = df['V2Tone'].str.split(',', expand=True).astype(float)


st.title("🎭 Actor Fingerprint Analysis")



st.markdown("""
### Research Question 3
How do the media fingerprints of the four most prominent figures differ in terms of emotional resonance (Polarity), collective framing (Self-Group Density), and action-oriented reporting (Activity Density)?
""")


if 'df' in locals() or 'df' in globals():
    df_clean = prepare_data(df)
    
    # Sidebar für Dynamik
    st.sidebar.header("Filter")
    all_actors = df_clean['PersonName'].value_counts().head(20).index.tolist()
    selected_actors = st.sidebar.multiselect(
        "Choose someone for comparison:", 
        options=all_actors, 
        default=all_actors[:3]
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Radar Fingerprint")
        plot_radar_chart(df_clean, selected_actors)
        st.markdown("""
        This radar chart compares the media profiles of key actors using normalized GDELT metrics like Polarity, Tone, and Activity. 
        It reveals how different individuals are framed, highlighting shifts between factual, emotional, or action-oriented reporting.
        """)
    with col2:
        st.subheader("Interactive Metrics")
        plot_dynamic_scatter(df_clean, selected_actors)
        
    st.info("💡 Use the side bar to add mentioned actors. In the scatterplot, the size of the bubble equals to the amount of articles around that person.")
