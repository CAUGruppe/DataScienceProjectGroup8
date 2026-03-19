import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="RQ2 — Social Movement Framing",
    page_icon="📰",
    layout="wide"
)

st.title("📰 RQ2 — Social Movement Framing")
st.markdown("**Tagesschau vs. Bild · GDELT GKG**")

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ 1. DATEN LADEN                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@st.cache_data
def load_data():
    df = pd.read_csv(
        "tagesschau_zdf_pbs_foxnews_bild_gkg_partitioned_full.csv",
        on_bad_lines='skip', low_memory=False,
        usecols=['DATE', 'url', 'V2Tone']
    )
    return df

with st.spinner("Daten werden geladen..."):
    df_raw = load_data()

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ 2. DATEN AUFBEREITEN                                                    ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@st.cache_data
def prepare(_df):
    df = _df.copy()

    def label_outlet(url):
        url = str(url).lower()
        if 'tagesschau.de' in url: return 'Tagesschau'
        if 'bild.de' in url:       return 'Bild'
        return None

    df['Outlet'] = df['url'].apply(label_outlet)
    df = df[df['Outlet'].notna()].copy()

    df['AvgTone'] = pd.to_numeric(
        df['V2Tone'].astype(str).str.split(',').str[0], errors='coerce')

    KEYWORDS = (
        'protest|demonstration|demo-|streik|kundgebung|bewegung|aktivist|'
        'fridays-for-future|klimaprotest|verdi|gewerkschaft|arbeitskampf|'
        'blockade|bauernprotest|klimastreik|buergerinitiative'
    )
    df_soc = df[df['url'].fillna('').str.lower().str.contains(KEYWORDS)].copy()

    def classify(t):
        try:
            t = float(t)
            if t > 1.0:    return 'Positive'
            elif t < -1.0: return 'Negative'
            else:           return 'Neutral'
        except:
            return None

    df_soc['ToneLabel'] = df_soc['AvgTone'].apply(classify)
    df_soc = df_soc.dropna(subset=['ToneLabel'])

    # Tone-Verteilung
    summary = (df_soc.groupby(['Outlet','ToneLabel'])
               .size().reset_index(name='Count'))
    summary['Total'] = summary.groupby('Outlet')['Count'].transform('sum')
    summary['Pct']   = summary['Count'] / summary['Total'] * 100

    # Zeitreihe
    df_soc['_date'] = pd.to_datetime(
        df_soc['DATE'].astype(str).str[:8], format='%Y%m%d', errors='coerce')
    df_soc = df_soc.dropna(subset=['_date'])
    df_soc['_month'] = df_soc['_date'].dt.to_period('M')
    monthly = (df_soc.groupby(['_month','Outlet'])['AvgTone']
               .agg(AvgTone='mean', Count='count').reset_index())
    monthly['Date'] = monthly['_month'].dt.to_timestamp()
    monthly = monthly[monthly['Count'] >= 3].sort_values('Date')

    return summary, monthly

summary, monthly = prepare(df_raw)

OUTLETS    = [o for o in ['Tagesschau','Bild'] if o in summary['Outlet'].values]
TONE_ORDER = ['Negative','Neutral','Positive']
TS_COLOR   = '#1565C0'
BILD_COLOR = '#C62828'
bar_colors = {
    'Tagesschau': {'Negative': '#1565C0', 'Neutral': '#1565C0', 'Positive': '#1565C0'},
    'Bild':       {'Negative': '#C62828',  'Neutral': '#C62828',  'Positive': '#C62828'},
}

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ 3. CHART 1 — GROUPED BAR                                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝

st.subheader("Tone-Verteilung bei sozialen Bewegungen")

fig_bar = go.Figure()
for outlet in OUTLETS:
    pct_vals, count_vals = [], []
    for tone in TONE_ORDER:
        row = summary[(summary['Outlet']==outlet) & (summary['ToneLabel']==tone)]
        pct_vals.append(round(row['Pct'].values[0], 2) if len(row) else 0.0)
        count_vals.append(int(row['Count'].values[0]) if len(row) else 0)

    color    = TS_COLOR if outlet == 'Tagesschau' else BILD_COLOR
    bar_clrs = [bar_colors[outlet][t] for t in TONE_ORDER]
    emoji    = '📺' if outlet == 'Tagesschau' else '🗞'

    fig_bar.add_trace(go.Bar(
        name=outlet,
        x=TONE_ORDER,
        y=pct_vals,
        marker_color=bar_clrs,
        marker_line=dict(color='white', width=1.5),
        customdata=list(zip(count_vals, [f"{p:.1f}" for p in pct_vals])),
        hovertemplate=(
            f"<b>{emoji} {outlet} – %{{x}}</b><br>"
            "Anteil: %{customdata[1]}%<br>"
            "Artikel: %{customdata[0]}<extra></extra>"
        ),
        text=[f"{p:.1f}%" for p in pct_vals],
        textposition='outside',
        textfont=dict(size=12, color=color),
    ))

n_ts   = int(summary[summary['Outlet']=='Tagesschau']['Count'].sum()) if 'Tagesschau' in OUTLETS else 0
n_bild = int(summary[summary['Outlet']=='Bild']['Count'].sum())       if 'Bild' in OUTLETS else 0

fig_bar.update_layout(
    barmode='group', bargap=0.25, bargroupgap=0.08,
    title=dict(
        text=(
            "Tone Distribution — "
            "<span style='color:#1565C0;font-weight:bold;'>Tagesschau</span>"
            " vs. "
            "<span style='color:#C62828;font-weight:bold;'>Bild</span>"
            " · Soziale Bewegungen"
        ),
        font=dict(size=18, family='Arial'), x=0.5, xanchor='center',
    ),
    xaxis=dict(title='Tone Category', tickfont=dict(size=13)),
    yaxis=dict(title='Share of Articles (%)', range=[0,115],
               gridcolor='#f0f0f0', zeroline=False),
    legend=dict(orientation='h', y=1.12, x=0.5, xanchor='center', font=dict(size=13)),
    plot_bgcolor='white', paper_bgcolor='white', height=520,
    margin=dict(t=130, b=110, l=60, r=40),
    annotations=[dict(
        text=(f"Source: GDELT GKG | Tagesschau n={n_ts}, Bild n={n_bild} | "
              "AvgTone > 1 = Positive, < −1 = Negative"),
        xref='paper', yref='paper', x=0.5, y=-0.20,
        showarrow=False, font=dict(size=10, color='gray'), xanchor='center',
    )],
    hoverlabel=dict(bgcolor='white', font_size=13, bordercolor='#cccccc'),
)

st.plotly_chart(fig_bar, use_container_width=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ 4. CHART 2 — ZEITREIHE                                                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝

st.subheader("Ø Tone über Zeit — Soziale Bewegungen")

_ts   = monthly[monthly['Outlet']=='Tagesschau']
_bild = monthly[monthly['Outlet']=='Bild']

fig_line = go.Figure()

if len(_ts) > 0:
    fig_line.add_trace(go.Scatter(
        x=_ts['Date'], y=_ts['AvgTone'],
        name='Tagesschau', mode='lines+markers',
        line=dict(color=TS_COLOR, width=3),
        marker=dict(size=7, color=TS_COLOR, line=dict(width=1.5, color='white')),
        fill='tozeroy', fillcolor='rgba(21,101,192,0.08)',
        customdata=np.stack([_ts['Count'], _ts['Date'].dt.strftime('%B %Y')], axis=1),
        hovertemplate=(
            "<b>📺 Tagesschau</b><br>%{customdata[1]}<br>"
            "Ø Tone: %{y:.2f}<br>Artikel: %{customdata[0]}<extra></extra>"
        ),
    ))
    fig_line.add_annotation(
        x=_ts['Date'].iloc[-1], y=_ts['AvgTone'].iloc[-1],
        text="📺 Tagesschau", showarrow=True, arrowhead=2,
        arrowcolor=TS_COLOR, font=dict(size=12, color=TS_COLOR, family='Arial Black'),
        bgcolor='white', bordercolor=TS_COLOR, borderwidth=1.5, ax=50, ay=30
    )

if len(_bild) > 0:
    fig_line.add_trace(go.Scatter(
        x=_bild['Date'], y=_bild['AvgTone'],
        name='Bild', mode='lines+markers',
        line=dict(color=BILD_COLOR, width=3, dash='dash'),
        marker=dict(size=8, color=BILD_COLOR, symbol='diamond',
                    line=dict(width=1.5, color='white')),
        fill='tozeroy', fillcolor='rgba(198,40,40,0.06)',
        customdata=np.stack([_bild['Count'], _bild['Date'].dt.strftime('%B %Y')], axis=1),
        hovertemplate=(
            "<b>🗞 Bild</b><br>%{customdata[1]}<br>"
            "Ø Tone: %{y:.2f}<br>Artikel: %{customdata[0]}<extra></extra>"
        ),
    ))
    fig_line.add_annotation(
        x=_bild['Date'].iloc[-1], y=_bild['AvgTone'].iloc[-1],
        text="🗞 Bild", showarrow=True, arrowhead=2,
        arrowcolor=BILD_COLOR, font=dict(size=12, color=BILD_COLOR, family='Arial Black'),
        bgcolor='white', bordercolor=BILD_COLOR, borderwidth=1.5, ax=50, ay=-30
    )

fig_line.add_shape(type='line', x0=0, x1=1, xref='x domain',
                   y0=0, y1=0, yref='y',
                   line=dict(color='gray', dash='dot'), opacity=0.5)
fig_line.add_shape(type='line', x0=0, x1=1, xref='x domain',
                   y0=-1, y1=-1, yref='y',
                   line=dict(color='#EF5350', dash='dash'), opacity=0.4)

fig_line.update_layout(
    title=dict(
        text="Ø Tone über Zeit — "
             "<span style='color:#1565C0;font-weight:bold;'>Tagesschau</span>"
             " vs. <span style='color:#C62828;font-weight:bold;'>Bild</span>"
             " · Soziale Bewegungen",
        font=dict(size=20, family='Arial'), x=0.5, xanchor='center',
    ),
    xaxis=dict(
        title='Monat', tickformat='%b %Y',
        rangeselector=dict(
            buttons=[
                dict(count=3,  label='3M', step='month', stepmode='backward'),
                dict(count=6,  label='6M', step='month', stepmode='backward'),
                dict(count=12, label='1J', step='month', stepmode='backward'),
                dict(step='all', label='Alle'),
            ],
            bgcolor='white', activecolor=TS_COLOR, font=dict(size=12),
        ),
        rangeslider=dict(visible=True, thickness=0.08),
    ),
    yaxis=dict(title='Ø AvgTone Score', zeroline=False, gridcolor='#f0f0f0'),
    hovermode='x unified',
    legend=dict(orientation='h', y=1.15, x=0.5, xanchor='center', font=dict(size=13)),
    plot_bgcolor='white', paper_bgcolor='white', height=540,
    margin=dict(t=140, b=80, l=60, r=130),
    hoverlabel=dict(bgcolor='white', font_size=13, bordercolor='#cccccc'),
)

st.plotly_chart(fig_line, use_container_width=True)
