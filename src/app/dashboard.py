"""Interactive Analytics Dashboard: The FIFA World Cup Effect on Brazil's Power Grid."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.config import SILVER_DIR, GOLD_DIR, BRAZIL_MATCHES, SUBSYSTEMS

st.set_page_config(
    page_title="Brazil Power Grid: FIFA World Cup 2022 Analytics",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .info-box {
        background-color: #0d1117;
        border-left: 4px solid #58a6ff;
        padding: 12px 16px;
        border-radius: 4px;
        font-size: 14px;
        color: #c9d1d9;
        margin-top: 10px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    silver_file = SILVER_DIR / "grid_silver.parquet"
    hourly_file = GOLD_DIR / "gold_match_hourly_comparison.parquet"
    summary_file = GOLD_DIR / "gold_match_impact_summary.parquet"
    
    silver_df = pd.read_parquet(silver_file) if silver_file.exists() else None
    hourly_df = pd.read_parquet(hourly_file) if hourly_file.exists() else None
    summary_df = pd.read_parquet(summary_file) if summary_file.exists() else None
    
    return silver_df, hourly_df, summary_df

silver_df, hourly_df, summary_df = load_data()

st.title("Brazil Power Grid: FIFA World Cup 2022 Operational Analytics")
st.caption("Analyzing the massive electrical load drop and generation ramping during Brazil World Cup matches | Source: ONS Open Data")

if hourly_df is None or summary_df is None:
    st.error("Pipeline layers not found. Please run the ingestion & transformation pipeline first.")
    st.stop()

# Key metrics across all matches
max_drop_record = summary_df.loc[summary_df["max_load_drop_mw"].idxmax()]
avg_drop = summary_df["max_load_drop_mw"].mean()
total_ramp_avg = summary_df["post_match_ramp_2h_mw"].mean()

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Peak Load Drop Recorded", f"-{max_drop_record['max_load_drop_mw']:,.0f} MW", delta=f"{max_drop_record['opponent']} ({max_drop_record['max_load_drop_pct']}%)")
with c2:
    st.metric("Average Load Drop per Match", f"-{avg_drop:,.0f} MW")
with c3:
    st.metric("Post-Match Ramp (2h average)", f"+{total_ramp_avg:,.0f} MW")
with c4:
    st.metric("Matches Analyzed", f"{len(summary_df)} matches")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs([
    "The World Cup Match Effect",
    "Generation Dispatch & Grid Flexibility",
    "Regional Subsystem Breakdown",
    "Lakehouse Architecture & Data"
])

with tab1:
    st.subheader("1. National Hourly Demand: Match Day vs. Baseline Day")
    
    selected_match_id = st.selectbox(
        "Select Brazil Match to analyze:",
        options=summary_df["match_id"].tolist(),
        format_func=lambda x: f"{x} - {summary_df[summary_df['match_id'] == x]['stage'].values[0]}: {summary_df[summary_df['match_id'] == x]['result'].values[0]} ({summary_df[summary_df['match_id'] == x]['match_date'].values[0]})"
    )
    
    match_info = summary_df[summary_df["match_id"] == selected_match_id].iloc[0]
    sin_match_data = hourly_df[(hourly_df["id_subsistema"] == "SIN") & (hourly_df["match_id"] == selected_match_id)].sort_values("hour")
    
    fig_curve = go.Figure()
    
    # Baseline load
    fig_curve.add_trace(go.Scatter(
        x=sin_match_data["hour"],
        y=sin_match_data["load_mw_baseline"],
        mode="lines+markers",
        name=f"Baseline Day ({match_info['baseline_date']})",
        line=dict(color="#8b949e", width=2, dash="dash")
    ))
    
    # Match day load
    fig_curve.add_trace(go.Scatter(
        x=sin_match_data["hour"],
        y=sin_match_data["load_mw"],
        mode="lines+markers",
        name=f"Match Day ({match_info['match_date']} - {match_info['opponent']})",
        line=dict(color="#58a6ff", width=3.5)
    ))
    
    # Highlight match window
    k_hour = int(match_info["kickoff_time"].split(":")[0])
    fig_curve.add_vrect(
        x0=k_hour - 0.2, x1=k_hour + 2.2,
        fillcolor="#f85149", opacity=0.15,
        annotation_text="Match Window (Game in progress)",
        annotation_position="top left"
    )
    
    fig_curve.update_layout(
        template="plotly_dark",
        height=420,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Hour of Day (BRT)",
        yaxis_title="Grid Load (MW)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_curve, use_container_width=True)
    
    st.markdown(f"""
    <div class="info-box">
        <b>Operational Takeaway:</b> During {match_info['result']}, national grid load dropped by 
        <b>{match_info['max_load_drop_mw']:,.0f} MW ({match_info['max_load_drop_pct']}%)</b> compared to typical non-match operations at {match_info['peak_drop_hour']}.<br>
        Commercial offices, schools, and industrial assembly lines stopped operations simultaneously as ~200 million people gathered around television screens.
        Within 2 hours after the match, demand surged back by <b>+{match_info['post_match_ramp_2h_mw']:,.0f} MW</b>.
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    st.subheader("All Matches Comparison Table")
    st.dataframe(
        summary_df[["match_id", "stage", "result", "match_date", "kickoff_time", "max_load_drop_mw", "max_load_drop_pct", "post_match_ramp_2h_mw"]],
        use_container_width=True
    )

with tab2:
    st.subheader("2. Generation Dispatch: How the Grid Absorbed the Plunge")
    st.markdown("""
    In Brazil, hydroelectric plants act as the primary dynamic buffer for grid frequency regulation.
    During World Cup matches, the system operator (ONS) throttles hydropower down by thousands of MW to absorb the demand collapse and ramps it back up instantly at the final whistle.
    """)
    
    col_view, col_dummy = st.columns([1, 2])
    with col_view:
        time_scope = st.radio(
            "Time Window:",
            ["Focused Match Window (3h Before to 3h After)", "Full 24-Hour Daily Profile"],
            horizontal=True
        )
    
    k_hour = int(match_info["kickoff_time"].split(":")[0])
    end_hour = k_hour + (3 if "Croatia" in match_info["opponent"] else 2)
    
    if "Focused" in time_scope:
        start_h = max(0, k_hour - 3)
        finish_h = min(23, end_hour + 3)
        plot_gen_data = sin_match_data[(sin_match_data["hour"] >= start_h) & (sin_match_data["hour"] <= finish_h)].copy()
    else:
        plot_gen_data = sin_match_data.copy()
        start_h, finish_h = 0, 23
        
    # Single unified Dual-Axis chart: Hydro on Left, Thermal/Wind/Solar on Right
    fig_gen = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Primary Y-axis (Left): Hydro Generation
    fig_gen.add_trace(
        go.Scatter(
            x=plot_gen_data["hour"], y=plot_gen_data["hydro_gen_mw"],
            mode="lines+markers", name="Hydro Generation (Left Axis)",
            line=dict(color="#58a6ff", width=3.5),
            marker=dict(size=7)
        ),
        secondary_y=False
    )
    
    # Secondary Y-axis (Right): Thermal, Wind, Solar
    fig_gen.add_trace(
        go.Scatter(
            x=plot_gen_data["hour"], y=plot_gen_data["thermal_gen_mw"],
            mode="lines+markers", name="Thermal Generation (Right Axis)",
            line=dict(color="#f0883e", width=2.5),
            marker=dict(size=6)
        ),
        secondary_y=True
    )
    fig_gen.add_trace(
        go.Scatter(
            x=plot_gen_data["hour"], y=plot_gen_data["wind_gen_mw"],
            mode="lines+markers", name="Wind Generation (Right Axis)",
            line=dict(color="#3fb950", width=2, dash="dot"),
            marker=dict(size=5)
        ),
        secondary_y=True
    )
    fig_gen.add_trace(
        go.Scatter(
            x=plot_gen_data["hour"], y=plot_gen_data["solar_gen_mw"],
            mode="lines+markers", name="Solar Generation (Right Axis)",
            line=dict(color="#e3b341", width=2, dash="dot"),
            marker=dict(size=5)
        ),
        secondary_y=True
    )
    
    # Highlight match window
    fig_gen.add_vrect(
        x0=k_hour - 0.1, x1=end_hour + 0.1,
        fillcolor="#f85149", opacity=0.15,
        annotation_text="Match in Progress",
        annotation_position="top left"
    )
    
    # Zoom Hydro Y-axis to cut off low baseline values
    min_hydro = plot_gen_data["hydro_gen_mw"].min()
    max_hydro = plot_gen_data["hydro_gen_mw"].max()
    fig_gen.update_yaxes(
        title_text="Hydro Generation (MW) [Left Axis]",
        range=[min_hydro - 1500, max_hydro + 1500],
        secondary_y=False
    )
    
    # Scale for secondary sources
    max_secondary = max(
        plot_gen_data["thermal_gen_mw"].max(),
        plot_gen_data["wind_gen_mw"].max(),
        plot_gen_data["solar_gen_mw"].max()
    )
    fig_gen.update_yaxes(
        title_text="Thermal, Wind & Solar (MW) [Right Axis]",
        range=[0, max_secondary + 1500],
        secondary_y=True
    )
    
    fig_gen.update_xaxes(
        title_text="Hour of Day (BRT)",
        tickmode="linear", dtick=1
    )
    
    fig_gen.update_layout(
        template="plotly_dark",
        height=480,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="right", x=1)
    )
    st.plotly_chart(fig_gen, use_container_width=True)
    
    # Summary calculation of hydro throttling
    hydro_start = plot_gen_data[plot_gen_data["hour"] == k_hour]["hydro_gen_mw"].values[0] if len(plot_gen_data[plot_gen_data["hour"] == k_hour]) else 0
    hydro_min = plot_gen_data[(plot_gen_data["hour"] >= k_hour) & (plot_gen_data["hour"] <= end_hour)]["hydro_gen_mw"].min()
    hydro_post = plot_gen_data[plot_gen_data["hour"] == min(23, end_hour + 2)]["hydro_gen_mw"].values[0] if len(plot_gen_data[plot_gen_data["hour"] == min(23, end_hour + 2)]) else 0
    
    st.markdown(f"""
    <div class="info-box">
        <b>Hydropower Flexibility Summary:</b><br>
        During this match, hydropower throttled down from <b>{hydro_start:,.0f} MW</b> to <b>{hydro_min:,.0f} MW</b> (absorbing a direct drop of <b>{hydro_start - hydro_min:,.0f} MW</b> on the left scale).<br>
        Following the final whistle, hydro dispatch surged to <b>{hydro_post:,.0f} MW</b> (+{hydro_post - hydro_min:,.0f} MW ramp) to meet the sudden reconnection of national load, while thermal and renewable sources (right scale) modulated smoothly.
    </div>
    """, unsafe_allow_html=True)

with tab3:
    st.subheader("3. Regional Breakdown: Where Did the 11,000+ MW Disappear?")
    st.markdown("""
    While all regions experienced a relative ~10% to 15% drop, the **absolute volume of disconnected load** was overwhelmingly concentrated in the country's industrial core.
    """)
    
    # Filter for the selected match and get drop across subsystems at peak drop hour
    peak_h = int(match_info["peak_drop_hour"].split(":")[0])
    sub_data = hourly_df[(hourly_df["match_id"] == selected_match_id) & (hourly_df["hour"] == peak_h) & (hourly_df["id_subsistema"] != "SIN")].copy()
    sub_data["subsystem_name"] = sub_data["id_subsistema"].map(SUBSYSTEMS)
    sub_data["share_of_total_pct"] = (sub_data["load_drop_mw"] / sub_data["load_drop_mw"].sum() * 100).round(1)
    
    col_x, col_y = st.columns(2)
    with col_x:
        st.markdown("**Share of National Load Drop (Contribution to Disconnection)**")
        fig_donut = px.pie(
            sub_data,
            values="load_drop_mw",
            names="id_subsistema",
            hole=0.45,
            color="id_subsistema",
            color_discrete_map={
                "SE": "#58a6ff",
                "S": "#3fb950",
                "NE": "#f0883e",
                "N": "#a371f7"
            },
            labels={"load_drop_mw": "Load Drop (MW)", "id_subsistema": "Subsystem"},
            template="plotly_dark",
            height=370
        )
        fig_donut.update_traces(textinfo="label+percent+value", texttemplate="%{label}<br>%{percent:.1%}<br>(%{value:,.0f} MW)")
        fig_donut.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_donut, use_container_width=True)
        st.caption("**Concentration:** Over **55%** of the entire national collapse originated strictly in the Southeast/Central-West (SE) industrial corridor (São Paulo, Rio, Minas Gerais).")
        
    with col_y:
        st.markdown("**Regional Load Profiles (Hourly Match Trajectory)**")
        # Multi-line hourly load comparison by subsystem
        k_hour = int(match_info["kickoff_time"].split(":")[0])
        end_hour = k_hour + (3 if "Croatia" in match_info["opponent"] else 2)
        sub_hourly = hourly_df[(hourly_df["match_id"] == selected_match_id) & (hourly_df["id_subsistema"] != "SIN")].copy()
        sub_hourly_window = sub_hourly[(sub_hourly["hour"] >= max(0, k_hour - 3)) & (sub_hourly["hour"] <= min(23, end_hour + 3))]
        
        fig_sub_lines = px.line(
            sub_hourly_window,
            x="hour",
            y="load_mw",
            color="id_subsistema",
            markers=True,
            color_discrete_map={
                "SE": "#58a6ff",
                "S": "#3fb950",
                "NE": "#f0883e",
                "N": "#a371f7"
            },
            labels={"hour": "Hour of Day (BRT)", "load_mw": "Load (MW)", "id_subsistema": "Subsystem"},
            template="plotly_dark",
            height=370
        )
        fig_sub_lines.add_vrect(
            x0=k_hour - 0.1, x1=end_hour + 0.1,
            fillcolor="#f85149", opacity=0.15,
            annotation_text="Match",
            annotation_position="top left"
        )
        fig_sub_lines.update_layout(margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_sub_lines, use_container_width=True)
        st.caption("**Trajectory:** Notice the deep U-shape crater in the Southeast (SE) load line, dropping from 46,000 MW to under 40,000 MW during kickoff.")

    st.divider()
    
    # Subsystems reference table
    st.markdown("**Subsystem Details at Peak Drop Hour:**")
    sub_table = sub_data[["id_subsistema", "subsystem_name", "load_mw_baseline", "load_mw", "load_drop_mw", "share_of_total_pct"]].copy()
    sub_table.columns = ["Subsystem", "Region Description", "Baseline Load (MW)", "Match Load (MW)", "Drop Volume (MW)", "Share of National Drop (%)"]
    st.dataframe(sub_table, use_container_width=True)

with tab4:
    st.subheader("Data Lakehouse End-to-End Architecture")
    
    import streamlit.components.v1 as components
    mermaid_code = """
    <div class="mermaid" style="display:flex; justify-content:center;">
    flowchart LR
        subgraph S1 ["1. Ingestion Sources"]
            direction TB
            RAW["ONS AWS Open Data<br>Hourly Energy Balance 2022 (CSV)"]
        end

        subgraph S2 ["2. Bronze Layer (Raw)"]
            direction TB
            BRONZE["bronze/<br>id_subsistema=*/<br>• Partitioned by Subsystem<br>• Audit timestamps & Batch UUID<br>• Snappy compression"]
        end

        subgraph S3 ["3. Silver Layer (Curated)"]
            direction TB
            SILVER["silver/grid_silver.parquet<br>• Cleaned column schema<br>• World Cup schedule enrichment<br>• Match & Stage identification"]
        end

        subgraph S4 ["4. Gold Layer (Business KPIs)"]
            direction TB
            G1["gold_match_hourly_comparison.parquet<br>Hourly Match vs Baseline Deltas"]
            G2["gold_match_impact_summary.parquet<br>Peak Drop MW, % & 2h Ramp Rate"]
        end

        subgraph S5 ["5. Analytics & Serving"]
            direction TB
            APP["Streamlit Interactive UI<br>Grid Impact & Dispatch Curves"]
            SQL["DuckDB Analytical Engine<br>Zero-copy Regional Aggregations"]
        end

        RAW -->|Batch Ingest| BRONZE
        BRONZE -->|Enrichment & Typing| SILVER
        SILVER -->|Baseline Comparison| G1
        SILVER -->|Impact Summaries| G2
        
        G1 --> APP
        G2 --> APP
        SILVER --> APP
        G1 --> SQL

        style BRONZE fill:#3d2714,stroke:#cd7f32,stroke-width:2px,color:#fff
        style SILVER fill:#1c2d3d,stroke:#a0b2c6,stroke-width:2px,color:#fff
        style G1 fill:#3d3414,stroke:#ffd700,stroke-width:2px,color:#fff
        style G2 fill:#3d3414,stroke:#ffd700,stroke-width:2px,color:#fff
        style APP fill:#163820,stroke:#3fb950,stroke-width:2px,color:#fff
    </div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({ startOnLoad: true, theme: 'dark' });
    </script>
    """
    components.html(mermaid_code, height=360, scrolling=True)
    
    st.divider()
    st.subheader("Interactive Parquet Data Browser")
    
    layer_sel = st.radio(
        "Select table to preview:",
        ["Gold (Match Impact Summary)", "Gold (Hourly Match Comparison)", "Silver (Enriched Grid Records)"],
        horizontal=True
    )
    if layer_sel == "Gold (Match Impact Summary)":
        st.dataframe(summary_df, use_container_width=True)
    elif layer_sel == "Gold (Hourly Match Comparison)":
        st.dataframe(hourly_df.head(50), use_container_width=True)
    else:
        st.dataframe(silver_df.head(50), use_container_width=True)
