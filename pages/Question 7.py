import streamlit as st
import plotly.express as px
import pandas as pd


@st.cache_data
def load_data():
    return pd.read_parquet("data/FULL_DATASET_GKG.parquet")


df = load_data()
df['Date'] = pd.to_datetime(df['DATE'], format='%Y%m%d%H%M%S')


df['Year-Month'] = df['Date'].dt.strftime('%Y-%m')


df[['tone','positive_score','negative_score','polarity', 'activity_density','self_group_density','word_count']] = df['V2Tone'].str.split(',', expand=True).astype(float)

df_china = df[
    df['Locations'].str.contains('china', case=False, na=False) |
    df['DocumentIdentifier'].str.contains('china', case=False, na=False)
]

df = df_china
# Titel der App
st.title("Media Coverage Analysis: China")

# --- Sidebar für Filter (Optional) ---
st.sidebar.header("Filter Optionen")
source_filter = st.sidebar.multiselect(
    "Quellen auswählen:",
    options=df['SourceCommonName'].unique(),
    default=df['SourceCommonName'].unique()
)

# Daten filtern basierend auf Auswahl
df_filtered = df[df['SourceCommonName'].isin(source_filter)]

# --- Plotly Density Heatmap ---
# Wir nutzen facet_col, um Foxnews und Tagesschau nebeneinander zu zeigen
fig = px.density_heatmap(
    df_filtered, 
    x="tone", 
    y="polarity", 
    facet_col="SourceCommonName",
    nbinsx=30, 
    nbinsy=30,
    range_x=[-7, 5], 
    range_y=[0, 12],
    color_continuous_scale="Viridis", # Oder 'Reds'/'Blues'
    labels={'tone': 'Tone (Sentiment)', 'polarity': 'Polarity (Intensity)'},
    title="Interactive Density Focus"
)

# Layout-Anpassungen (Null-Linie hinzufügen)
fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)

# Plot in Streamlit anzeigen
st.plotly_chart(fig, use_container_width=True)