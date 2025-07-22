import streamlit as st
import tempfile
import os
import numpy as np
from force_plotter import load_raw_data, process_file, plot_individual
import plotly.graph_objects as go

st.set_page_config(page_title="Pad Friction with Range Selection", layout="wide")
st.title("Pad Friction – Force-vs-Cycle Analyzer")

# Upload files
uploaded_files = st.file_uploader("Upload .xlsx files", type="xlsx", accept_multiple_files=True)

if uploaded_files:
    all_results = {}
    # Load data
dfs = {}
    for file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name
        df = load_raw_data(tmp_path)
        dfs[file.name] = (df, tmp_path)

    # Slider for range
    max_cm = max(df["Position mm"].max() / 10.0 for df, _ in dfs.values())
    cm_lo, cm_hi = st.slider("Select Centimeter Range", 0.0, float(round(max_cm, 1)), (0.0, float(round(max_cm, 1))), step=0.1)
    y_buffer = st.number_input("Add buffer to y-axis (grams)", 0, 50, 5)

    # Detect groups by prefix
    # Assumes filenames like 'GroupName_sampleX.xlsx'
    prefixes = sorted({name.split('_')[0] for name in dfs.keys()})
    st.subheader("Assign Colors to Groups")
    color_map = {}
    for prefix in prefixes:
        color_map[prefix] = st.color_picker(f"Color for '{prefix}'", '#'+''.join(np.random.choice(list('0123456789ABCDEF'), size=6)))

    if st.button("Generate Individual Plots"):
        for label, (df, path) in dfs.items():
            results = process_file(path, cm_lo, cm_hi)
            if not results:
                st.warning(f"No usable data in {label}")
                continue
            avg, peak = zip(*[r for r in results if not np.isnan(r[0]) and not np.isnan(r[1])])
            y_max = max(avg + peak) + y_buffer
            fig = plot_individual(path, results, save_dir=None, cm_lo=cm_lo, cm_hi=cm_hi, y_max=y_max, suffix="")
            st.subheader(label)
            st.plotly_chart(fig, use_container_width=True)

    if st.button("Generate Combined Average Plot"):
        # Collect average data
        combined_fig = go.Figure()
        for label, (df, path) in dfs.items():
            results = process_file(path, cm_lo, cm_hi)
            if not results:
                continue
            positions, avg_vals = zip(*[(r[2], r[0]) for r in results])
            prefix = label.split('_')[0]
            combined_fig.add_trace(
                go.Scatter(
                    x=positions,
                    y=avg_vals,
                    mode='lines+markers',
                    name=label,
                    line=dict(color=color_map.get(prefix)),
                    marker=dict(color=color_map.get(prefix))
                )
            )
        combined_fig.update_layout(
            title="Combined Average Force vs Position", 
            xaxis_title="Position (cm)",
            yaxis_title="Average Force (g)",
            yaxis=dict(range=[0, None])
        )
        st.plotly_chart(combined_fig, use_container_width=True)
