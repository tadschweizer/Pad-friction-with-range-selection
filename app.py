# app.py
import streamlit as st
import tempfile
import os
import numpy as np
from force_plotter import load_raw_data, process_file, plot_individual

st.set_page_config(page_title="Pad Friction with Range Selection", layout="wide")
st.title("Pad Friction – Force-vs-Cycle Analyzer")

uploaded_files = st.file_uploader("Upload .xlsx files", type="xlsx", accept_multiple_files=True)

if uploaded_files:
    all_avg, all_peak = [], []
    dfs = {}
    for file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name
        df = load_raw_data(tmp_path)
        dfs[file.name] = (df, tmp_path)

    max_cm = max(df["Position mm"].max() / 10.0 for df, _ in dfs.values())
    cm_lo, cm_hi = st.slider("Select Centimeter Range", 0.0, float(round(max_cm, 1)), (0.0, float(round(max_cm, 1))), step=0.1)
    y_buffer = st.number_input("Add buffer to y-axis (grams)", 0, 50, 5)

    if st.button("Generate Plots"):
        for label, (df, path) in dfs.items():
            results = process_file(path, cm_lo, cm_hi)
            if not results:
                st.warning(f"No usable data in {label}")
                continue
            avg, peak = zip(*[r for r in results if not np.isnan(r[0]) and not np.isnan(r[1])])
            y_max = max(avg + peak) + y_buffer
            fig = plot_individual(path, results, save_dir=None, cm_lo=cm_lo, cm_hi=cm_hi, y_max=y_max, suffix="")
            st.subheader(label)
            st.pyplot(fig)
