import streamlit as st
import plotly.express as px
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
import sys
import os
import utils



df = utils.load_data()
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
    animation_frame="Month", 
    animation_group="SourceCommonName",
    color="SourceCommonName",
    hover_name="DocumentIdentifier",
    range_x=[-10, 5], 
    range_y=[0, 15],
    title="Evolution of Article releases  (Month after Month)"
)


st.plotly_chart(fig, use_container_width=True)


df_monthly= df.groupby(['SourceCommonName', pd.Grouper(key='Date', freq='W')]).agg({
    'tone': 'mean',
    'polarity': 'mean'
}).reset_index().sort_values('Date')

# --- 2. Farben festlegen ---
color_map = {
    'foxnews.com': '#FF0000',      
    'tagesschau.de': '#004494'     
}


fig = px.line(
    df_monthly, 
    x="tone", 
    y="polarity", 
    color="SourceCommonName",
    color_discrete_map=color_map, 
    markers=True,                 # Zeigt die einzelnen Wochenpunkte an
    hover_data={'Date': "|%m."}, 
    title="Monthly Average movement ",
    labels={'tone': 'Average Tone', 'polarity': 'Average Polarity'}
)

# Das Design etwas "sauberer" machen
fig.update_traces(line=dict(width=3), marker=dict(size=8))
fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
st.markdown("""In this Plot you can see the evolution of the monthly average tone for foxnews and tagesschau.
            Whats interesting here is the movement from the top left to the bottom right. This indicates that in general
            Article with a negative tone tend to polarize more with their language. By plotting the trajectory it will get even clearer.
            """)

st.markdown("""
### Research Question 7
How does the sentiment (tone) of China-related coverage on Foxnews correlate emotional intensity (polarity) compared to Tagesschau?""")

st.plotly_chart(fig, use_container_width=True)

st.divider()



df_fox = df[df['SourceCommonName'].str.contains('foxnews.com', case=False, na=False)]
df_ts = df[df['SourceCommonName'].str.contains('tagesschau', case=False, na=False)]

# 2. Subplots erstellen
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), sharex=True, sharey=True)

extent = [-7, 5, 0, 12] 

# Hexbin für Foxnews
hb1 = ax1.hexbin(df_fox['tone'], df_fox['polarity'], gridsize=25, cmap='Reds', mincnt=1, extent=extent)
ax1.set_title('Density-Focus: Foxnews', fontsize=14)
ax1.set_xlabel('Tone')
ax1.set_ylabel('Polarity')
fig.colorbar(hb1, ax=ax1, label='Anzahl Artikel')

# Hexbin für Tagesschau
hb2 = ax2.hexbin(df_ts['tone'], df_ts['polarity'], gridsize=25, cmap='Blues', mincnt=1, extent=extent)
ax2.set_title('Density-Focus: Tagesschau', fontsize=14)
ax2.set_xlabel('Tone')
fig.colorbar(hb2, ax=ax2, label='Amount of Articles')

# Nulllinie zur Orientierung
for ax in [ax1, ax2]:
    ax.axvline(0, color='black', linestyle='--', alpha=0.3)

plt.suptitle('Comparison of coverage', fontsize=16)
plt.tight_layout(rect=[0, 0.03, 1, 0.95])

st.pyplot(fig)
st.markdown("""
            The Hexbin plot supports our thesis. The Red cloud getting denser towards the top left indicates that Foxnews
            seems to polarize way more with their language, when it comes to negative articles, compared to Tagesschau.
            """)
