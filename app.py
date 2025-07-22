import streamlit as st
import tempfile
import numpy as np
from force_plotter import load_raw_data, process_file, plot_individual
import plotly.graph_objects as go  # For combined plotting

st.set_page_config(page_title="Pad Friction with Range Selection", layout="wide")
st.title("Pad Friction – Force-vs-Cycle Analyzer")

# Predefined color bank with names
COLOR_BANK = [
    ("Red",     "#e6194b"),
    ("Green",   "#3cb44b"),
    ("Yellow",  "#ffe119"),
    ("Blue",    "#4363d8"),
    ("Orange",  "#f58231"),
    ("Purple",  "#911eb4"),
    ("Cyan",    "#46f0f0"),
    ("Magenta","#f032e6"),
    ("Lime",    "#bcf60c"),
    ("Pink",    "#fabebe")
]

# Upload files
uploaded_files = st.file_uploader("Upload .xlsx files", type="xlsx", accept_multiple_files=True)

if uploaded_files:
    dfs = {}
    for file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name
        df = load_raw_data(tmp_path)
        dfs[file.name] = (df, tmp_path)

    # Range selector
    max_cm = max(df["Position mm"].max() / 10.0 for df, _ in dfs.values())
    cm_lo, cm_hi = st.slider(
        "Select Centimeter Range", 0.0, float(round(max_cm, 1)),
        (0.0, float(round(max_cm, 1))), step=0.1
    )

    # Fixed buffer
    y_buffer = 5

    # Group prefixes
    prefixes = sorted({name.split('_')[0] for name in dfs.keys()})
    st.subheader("Assign Colors to Groups")
    color_map = {}
    for idx, prefix in enumerate(prefixes):
        # default assignment cycles through bank
        default_idx = idx % len(COLOR_BANK)
        # display radio buttons horizontally
        cols = st.columns(len(COLOR_BANK))
        st.write(f"**{prefix}**")
        for i, (name, hex_code) in enumerate(COLOR_BANK):
            with cols[i]:
                if st.button(name, key=f"btn_{prefix}_{i}"):
                    color_map[prefix] = hex_code
        # set default if not yet chosen
        if prefix not in color_map:
            color_map[prefix] = COLOR_BANK[default_idx][1]

    # Individual plots
    if st.button("Generate Individual Plots"):
        for label, (df, path) in dfs.items():
            results = process_file(path, cm_lo, cm_hi)
            if not results:
                st.warning(f"No usable data in {label}")
                continue
            avg_vals, peak_vals = zip(*[(r[0], r[1]) for r in results if not np.isnan(r[0])])
            y_max = max(avg_vals + peak_vals) + y_buffer
            fig = plot_individual(
                path, results,
                save_dir=None,
                cm_lo=cm_lo,
                cm_hi=cm_hi,
                y_max=y_max,
                suffix=""
            )
            st.subheader(label)
            st.pyplot(fig)

    # Combined average plot
    if st.button("Generate Combined Average Plot"):
        combined_fig = go.Figure()
        for label, (df, path) in dfs.items():
            results = process_file(path, cm_lo, cm_hi)
            if not results:
                continue
            positions = (df["Position mm"] / 10.0)[
                (df["Position mm"]/10.0 >= cm_lo) & (df["Position mm"]/10.0 <= cm_hi)
            ].unique().tolist()
            avgs = [r[0] for r in results]
            prefix = label.split('_')[0]
            clr = color_map[prefix]
            combined_fig.add_trace(
                go.Scatter(
                    x=positions,
                    y=avgs,
                    mode='lines+markers',
                    name=label,
                    line=dict(color=clr, width=2),  # slightly thicker
                    marker=dict(color=clr)
                )
            )
        combined_fig.update_layout(
            title="Combined Average Force vs Position",
            xaxis_title="Position (cm)",
            yaxis_title="Average Force (g)",
            yaxis=dict(range=[0, None])
        )
        st.plotly_chart(combined_fig, use_container_width=True)

# Ensure `plotly` in requirements.txt
