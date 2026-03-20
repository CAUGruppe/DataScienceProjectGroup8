import streamlit as st

st.set_page_config(page_title="About | Media Analysis Dashboard", layout="wide")

st.markdown("## About this project")

st.markdown("""
This Website was developed as part of our Data Science Project (inf-DSProj-01a) in the 5th Semester.
Therefore we formulated a set of research questions and tried to answer them with the help of GDELT data and interactive visualizations and interpreted the results.
Our main goal is to understand how often leading politicians are mentioned in the news, and how positively or negatively they are portrayed over time and across different media outlets. We use GDELT's Global Knowledge Graph (GKG) as our core data source and combine it with custom filtering and aggregation to focus on our set of research questions.
""")

st.markdown("## Team")

st.markdown("""
We are a group of students with backgrounds in business informatics (Wirtschaftsinformatik) at the Christian Albrechts Universität Kiel [CAU Kiel](https://www.uni-kiel.de/de/). 
""")

st.markdown("""Our project was supervised by:
""")
st.markdown("""
            - Prof. Dr. Peer Kröger
            - Mirjam Bayer, M.Sc.
            - Dr. Rükiye Altin
            - Aftab Anjum, Ph.D.
            - Sweety Mohanty, M.Sc.
            """)
st.markdown("""
            The project was developed by:
            """)
st.markdown("""
            - Jeremy Chaniago
            - Beytullah Yigit
            - Milad Sahili
            - Muhammed Kaan Sevinc

            - With Dr. Rükiye Altin as our main supervisor
            """)

st.markdown("## Motivation")

st.markdown("""
We started this project from a simple brain storming session about what we find interesting and can observe with APIS.
            Our first topics were Politics and Media, Media influence on Stock Market Performance, Airport Delays.
            We then decided to focus on Politics and Media, because we found it interesting to see how media portrays politicians and how this changes over time and across different media outlets.

Our motivation was therefore to:

- Translate complex GDELT data into an intuitive, interactive interface.  
- Compare media tone across countries and outlets.  
""")

st.markdown("## Methods and data")

st.markdown("""
- Data source: GDELT GKG v2.0 for 2021–2026 (Selected outlets: Tagesschau, ZDF, PBS, Fox News, Bild).  
- Processing: Python (pandas), partitioned Parquet files, custom leader and tone extraction.  
- Visualization: Streamlit, Plotly (bar charts, donut charts, small multiples and more).
- Github Repository: [Github Link](https://github.com/CAUGruppe/DataScienceProjectGroup8)
""")

st.markdown("## University")
st.markdown("""
Christian-Albrechts-Universität zu Kiel""")
st.markdown("Christian-Albrechts-Platz 4, 24118 Kiel, Germany")