import streamlit as st


# Page Configuration
st.set_page_config(page_title="Group 8 | Media Analysis", layout="wide")

# --- Header ---
st.title("📊 Group 8: Media Analysis Project")
st.subheader("Exploring Global News Trends with GDELT")

st.markdown("""
Welcome to our university project! We are investigating how the media shapes our view of the world. 
Instead of relying on gut feelings, we use data from **GDELT** to measure sentiment, focus, and emotional intensity in global news coverage.
""")

st.divider()

# --- Section 1: International Hot Topics ---
st.header("🌍 International Hot Topics")
col1, col2 = st.columns([2, 1])

with col1:
    st.write("How does the tone change during global conflicts and between superpowers?")
    
    # Links to the RQs
    st.page_link("pages/Question 1.py", label="**RQ1:** Difference in Tone changes about Israel/Palestine", icon="🕊️")
    st.page_link("pages/Question 6.py", label="**RQ6:*Which countries receive the most positive, neutral, or negative sentiment in German media coverage ", icon="🗺️")
    st.page_link("pages/Question 7.py", label="**RQ7:** China: FoxNews vs. Tagesschau", icon="🇨🇳")

with col2:
    # Placeholder for an image (e.g., World Map)
    #st.info("💡 Pro Tip: Insert a screenshot of your World Map (RQ6) here.")
    st.image("images/GlobalConflicts.jpg")

st.divider()

# --- Section 2: Politicians & The 'Vibe' ---
st.header("👔 Politicians & The 'Vibe'")
col3, col4 = st.columns([1, 2])

with col3:
    # Placeholder for an image (e.g., Radar Chart)
    #st.info("💡 A radar chart or a 'Fingerprint' comparison would look great here.")
    st.image("images/trumpmuskharris.jpg")
with col4:
    st.write("Who gets the best press, and who is viewed most critically?")
    st.page_link("pages/Question 3.py", label="**RQ3:** Media Fingerprints of Prominent Figures", icon="🧬")
    st.page_link("pages/Question 4.py", label="**RQ4:** Merz, Scholz, Trump & Biden Comparison", icon="⚖️")
    st.page_link("pages/Question 5.py", label="**RQ5:** Media During Election Periods", icon="🗳️")

st.divider()

# --- Section 3: Movements & Massive Events ---
st.header("📣 Movements & Massive Events")
st.write("What grabs the most attention, and how is it framed by the media?")

c1, c2 = st.columns(2)
with c1:
    st.page_link("pages/Question 2.py", label="**RQ2:** Framing of Social Movements", icon="📢")
with c2:
    st.page_link("pages/Question 8.py", label="**RQ8:** Which events generate the most attention?", icon="🔥")
st.image("images/SocialMovements.jpg")
st.divider()

# --- Footer / Data Source ---
st.markdown("### 🛠️ Our Data Sources")
st.write("""
We utilize the **GDELT News API**, which scans global news in real-time.. 
This project was developed as part of our Data Science Project Course.
""")

st.caption("Created by Jeremy, Milad, Kaan & Beytu | Group 8")