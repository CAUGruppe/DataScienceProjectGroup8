import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    return pd.read_parquet("Data/FULL_DATASET_GKG.parquet")

def load_data_rq4():
    parts = [
        "Data/gkg_partitioned_2021_part1.parquet",
        "Data/gkg_partitioned_2021_part2.parquet",
        "Data/gkg_partitioned_2021_part3.parquet",
        "Data/gkg_partitioned_2021_part4.parquet"
    ]
    df_list = [pd.read_parquet(p) for p in parts]
    return pd.concat(df_list, ignore_index=True)