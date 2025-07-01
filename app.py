import streamlit as st
import numpy as np
import tempfile
from force_plotter import load_raw_data, process_file

import matplotlib.pyplot as plt
from pathlib import Path

def make_fig(file_path, results, cm_lo, cm_hi, y_max):
    runs = range(1, len(results) + 1)
    avg = [r[0] for r in results]
    peak = [r[1] for r in results]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(runs, avg, marker="o", label="Average Force")
    ax.plot(runs, peak, marker="o", label="Peak Force")
    ax.set(
        xlabel="Run Number",
        ylabel="Grams",
        title=f"{Path(file_path).stem}  ({cm_lo:.1f}–{cm_hi:.1f} cm)",
        ylim=(0, y_max),
    )
    ax.grid(True)
    ax.legend()
    return fig

st.set_page_config("Force Plotter", layout="wide")
st.title("Force-vs-Cycle Plotter")

uploaded_files = st.file_uploader(
    "Upload one or more .xlsx files",
    type=["xlsx"],
    accept_multiple_files=True,
)

if uploaded_files:
    tmp_paths = []
    all_results = []
    all_forces = []

    for up_file in uploaded_files:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        tmp.write(up_file.read())
        tmp.close()
        tmp_paths.append(tmp.name)

    max_cm = max(load_raw_data(path)["Position mm"].max() / 10 for path in tmp_paths)

    cm_lo, cm_hi = st.slider("Select Centimeter Range", 0.0, float(round(max_cm, 1)), (0.0, float(round(max_cm, 1))), step=0.1)
    y_buffer = st.number_input("Extra y-axis space (grams)", 0, 50, 5)

    if st.button("Generate Plots"):
        for path in tmp_paths:
            results = process_file(path, cm_lo, cm_hi)
            all_results.append((path, results))
            for a, p in results:
                if not np.isnan(a): all_forces.append(a)
                if not np.isnan(p): all_forces.append(p)

        if not all_forces:
            st.error("No usable force data found.")
        else:
            y_max = max(all_forces) + y_buffer
            for path, results in all_results:
                fig = make_fig(path, results, cm_lo, cm_hi, y_max)
                st.pyplot(fig)
