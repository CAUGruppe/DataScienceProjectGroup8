import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    return pd.read_parquet("Data/FULL_DATASET_GKG.parquet")

def load_data_rq4():
    return pd.read_parquet("Data/gkg_partitioned_full_2021.parquet")