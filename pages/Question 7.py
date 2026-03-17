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

df = df[df['SourceCommonName'].str.contains('tagesschau|foxnews', case=False, na=False)]






df['Month'] = df['Date'].dt.strftime('%Y-%m')

fig = px.scatter(
    df.sort_values('Month'), 
    x="tone", 
    y="polarity", 
    animation_frame="Month", # Das erzeugt den Zeit-Slider
    animation_group="SourceCommonName",
    color="SourceCommonName",
    hover_name="DocumentIdentifier",
    range_x=[-10, 5], 
    range_y=[0, 15],
    title="Die Evolution der Berichterstattung (Monat für Monat)"
)

st.plotly_chart(fig, use_container_width=True)


df_monthly= df.groupby(['SourceCommonName', pd.Grouper(key='Date', freq='W')]).agg({
    'tone': 'mean',
    'polarity': 'mean'
}).reset_index().sort_values('Date')

# --- 2. Farben festlegen ---
color_map = {
    'foxnews.com': '#FF0000',      # Klassisches Rot
    'tagesschau.de': '#004494'     # Tagesschau-Blau
}

# --- 3. Den Pfad-Plot erstellen ---
fig = px.line(
    df_monthly, 
    x="tone", 
    y="polarity", 
    color="SourceCommonName",
    color_discrete_map=color_map, # Hier setzen wir deine Farben
    markers=True,                 # Zeigt die einzelnen Wochenpunkte an
    hover_data={'Date': "|%m."}, 
    title="Monthly Average movement ",
    labels={'tone': 'Average Tone', 'polarity': 'Average Polarity'}
)

# Das Design etwas "sauberer" machen
fig.update_traces(line=dict(width=3), marker=dict(size=8))
fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)

st.plotly_chart(fig, use_container_width=True)