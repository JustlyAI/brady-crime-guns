#!/usr/bin/env python3
"""
Brady Gun Center - Crime Gun Supply Chain Dashboard
MVP Version - Delaware Focus

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from pathlib import Path
from typing import Optional

from brady.utils import get_project_root

# Page config
st.set_page_config(
    page_title="Brady Crime Gun Dashboard",
    page_icon="🔫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .risk-high { color: #ff4b4b; font-weight: bold; }
    .risk-medium { color: #ffa500; font-weight: bold; }
    .risk-low { color: #00cc00; font-weight: bold; }
    .header-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .subheader {
        color: #666;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load crime gun events and DL2 dealer data from SQLite (with CSV fallback)"""
    project_root = get_project_root()
    data_dir = project_root / "data"

    db_path = data_dir / "brady.db"
    events_path = data_dir / "processed" / "crime_gun_events.csv"
    dl2_path = data_dir / "processed" / "dl2_dealers.csv"

    # Try SQLite first, fall back to CSV
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        events_df = pd.read_sql_query("SELECT * FROM crime_gun_events", conn)
        conn.close()
    elif events_path.exists():
        events_df = pd.read_csv(events_path, encoding="utf-8")
    else:
        st.error(f"Data not found! Run ETL pipeline first: uv run python -m brady.etl.process_gunstat")
        st.stop()

    dl2_df = pd.read_csv(dl2_path, encoding="utf-8") if dl2_path.exists() else pd.DataFrame()

    return events_df, dl2_df

def calculate_dealer_risk_score(dealer_stats: pd.Series) -> float:
    """Calculate risk score for a dealer"""
    score = 0

    # Base score: crime gun count
    score += dealer_stats.get('crime_count', 0) * 10

    # Interstate trafficking multiplier
    interstate_pct = dealer_stats.get('interstate_pct', 0)
    if interstate_pct > 0.5:
        score *= 2.0
    elif interstate_pct > 0.25:
        score *= 1.5

    # DL2 program flag
    if dealer_stats.get('in_dl2', False):
        score += 25

    # Revoked flag
    if dealer_stats.get('is_revoked', False):
        score += 50

    # Charged/Sued flag
    if dealer_stats.get('is_charged', False):
        score += 35

    return score

def get_risk_level(score: float) -> str:
    """Convert risk score to level"""
    if score >= 100:
        return "HIGH"
    elif score >= 50:
        return "MEDIUM"
    else:
        return "LOW"

def get_risk_color(level: str) -> str:
    """Get color for risk level"""
    colors = {
        "HIGH": "#ff4b4b",
        "MEDIUM": "#ffa500",
        "LOW": "#00cc00"
    }
    return colors.get(level, "#666")

def main():
    # Load data
    events_df, dl2_df = load_data()

    # Header
    st.markdown('<p class="header-title">🔫 Brady Crime Gun Supply Chain Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="subheader">Identifying manufacturers and dealers linked to crime guns by jurisdiction</p>', unsafe_allow_html=True)

    # Sidebar - Filters
    st.sidebar.header("🎯 Filters")

    # State filter
    available_states = sorted(events_df['jurisdiction_state'].dropna().unique())
    selected_state = st.sidebar.selectbox(
        "Select State (Crime Location)",
        options=available_states,
        index=available_states.index('DE') if 'DE' in available_states else 0,
        help="Filter by where the crime occurred"
    )

    # Filter data
    filtered_df = events_df[events_df['jurisdiction_state'] == selected_state].copy()

    # Data source filter
    data_sources = ['All'] + sorted(events_df['source_dataset'].dropna().unique().tolist())
    selected_source = st.sidebar.selectbox("Data Source", data_sources)
    if selected_source != 'All':
        filtered_df = filtered_df[filtered_df['source_dataset'] == selected_source]

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Records shown:** {len(filtered_df):,}")
    st.sidebar.markdown(f"**Total records:** {len(events_df):,}")

    # Main content
    if len(filtered_df) == 0:
        st.warning(f"No data available for {selected_state}")
        return

    # Key Metrics Row
    st.markdown("### 📊 Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)

    total_events = len(filtered_df)
    unique_dealers = filtered_df['dealer_name'].nunique()
    unique_manufacturers = filtered_df['manufacturer_name'].dropna().nunique()
    interstate_count = filtered_df['is_interstate'].sum()
    interstate_pct = (interstate_count / total_events * 100) if total_events > 0 else 0

    with col1:
        st.metric("Total Crime Guns", f"{total_events:,}")
    with col2:
        st.metric("Unique Dealers", f"{unique_dealers:,}")
    with col3:
        st.metric("Unique Manufacturers", f"{unique_manufacturers:,}")
    with col4:
        st.metric("Interstate Trafficking", f"{interstate_count:,}", f"{interstate_pct:.1f}%")
    with col5:
        # Calculate avg if we had TTC data
        pending_count = filtered_df[filtered_df['case_status'] == 'Pending'].shape[0] if 'case_status' in filtered_df.columns else 0
        st.metric("Pending Cases", f"{pending_count:,}")

    # Crime Location Coverage Section
    if 'crime_location_state' in filtered_df.columns:
        st.markdown("### 📍 Crime Location Classification Coverage")

        location_cols = ['crime_location_state', 'crime_location_city', 'crime_location_zip',
                        'crime_location_court', 'crime_location_pd']

        loc_col1, loc_col2, loc_col3, loc_col4, loc_col5 = st.columns(5)

        with loc_col1:
            state_count = filtered_df['crime_location_state'].notna().sum()
            state_pct = (state_count / total_events * 100) if total_events > 0 else 0
            st.metric("State Classified", f"{state_count}", f"{state_pct:.0f}%")

        with loc_col2:
            city_count = filtered_df['crime_location_city'].notna().sum() if 'crime_location_city' in filtered_df.columns else 0
            city_pct = (city_count / total_events * 100) if total_events > 0 else 0
            st.metric("City Classified", f"{city_count}", f"{city_pct:.0f}%")

        with loc_col3:
            zip_count = filtered_df['crime_location_zip'].notna().sum() if 'crime_location_zip' in filtered_df.columns else 0
            zip_pct = (zip_count / total_events * 100) if total_events > 0 else 0
            st.metric("ZIP Classified", f"{zip_count}", f"{zip_pct:.0f}%")

        with loc_col4:
            court_count = filtered_df['crime_location_court'].notna().sum() if 'crime_location_court' in filtered_df.columns else 0
            court_pct = (court_count / total_events * 100) if total_events > 0 else 0
            st.metric("Court Classified", f"{court_count}", f"{court_pct:.0f}%")

        with loc_col5:
            pd_count = filtered_df['crime_location_pd'].notna().sum() if 'crime_location_pd' in filtered_df.columns else 0
            pd_pct = (pd_count / total_events * 100) if total_events > 0 else 0
            st.metric("PD Classified", f"{pd_count}", f"{pd_pct:.0f}%")

    st.markdown("---")

    # Two column layout for main visualizations
    left_col, right_col = st.columns(2)

    # LEFT: Dealer Risk Ranking
    with left_col:
        st.markdown("### 🏪 Dealer Risk Ranking")
        st.caption(f"Dealers supplying crime guns recovered in {selected_state}")

        # Aggregate by dealer
        dealer_stats = filtered_df.groupby('dealer_name').agg({
            'source_row': 'count',  # crime count
            'is_interstate': 'mean',
            'dealer_state': 'first',
            'dealer_city': 'first',
        }).reset_index()
        dealer_stats.columns = ['dealer_name', 'crime_count', 'interstate_pct', 'dealer_state', 'dealer_city']

        # Add risk indicators if available
        if 'in_dl2' in filtered_df.columns:
            dl2_status = filtered_df.groupby('dealer_name')['in_dl2'].max().reset_index()
            dealer_stats = dealer_stats.merge(dl2_status, on='dealer_name', how='left')
        else:
            dealer_stats['in_dl2'] = False

        if 'is_revoked' in filtered_df.columns:
            revoked_status = filtered_df.groupby('dealer_name')['is_revoked'].max().reset_index()
            dealer_stats = dealer_stats.merge(revoked_status, on='dealer_name', how='left')
        else:
            dealer_stats['is_revoked'] = False

        if 'is_charged' in filtered_df.columns:
            charged_status = filtered_df.groupby('dealer_name')['is_charged'].max().reset_index()
            dealer_stats = dealer_stats.merge(charged_status, on='dealer_name', how='left')
        else:
            dealer_stats['is_charged'] = False

        # Calculate risk scores
        dealer_stats['risk_score'] = dealer_stats.apply(calculate_dealer_risk_score, axis=1)
        dealer_stats['risk_level'] = dealer_stats['risk_score'].apply(get_risk_level)
        dealer_stats = dealer_stats.sort_values('risk_score', ascending=False)

        # Display table
        display_df = dealer_stats[['dealer_name', 'dealer_city', 'dealer_state', 'crime_count', 'risk_level', 'risk_score']].copy()
        display_df.columns = ['Dealer', 'City', 'State', 'Crime Guns', 'Risk', 'Score']

        # Add color coding
        def color_risk(val):
            colors = {'HIGH': 'background-color: #ffcccc', 'MEDIUM': 'background-color: #fff3cd', 'LOW': 'background-color: #d4edda'}
            return colors.get(val, '')

        styled_df = display_df.head(10).style.map(color_risk, subset=['Risk'])
        st.dataframe(styled_df, width="stretch", hide_index=True)

        # Dealer bar chart
        fig_dealers = px.bar(
            dealer_stats.head(10),
            x='crime_count',
            y='dealer_name',
            orientation='h',
            color='risk_level',
            color_discrete_map={'HIGH': '#ff4b4b', 'MEDIUM': '#ffa500', 'LOW': '#00cc00'},
            title=f"Top 10 Dealers by Crime Gun Count ({selected_state})"
        )
        fig_dealers.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            showlegend=True,
            height=400
        )
        st.plotly_chart(fig_dealers, width="stretch")

    # RIGHT: Manufacturer Analysis
    with right_col:
        st.markdown("### 🏭 Manufacturer Analysis")
        st.caption(f"Manufacturers of crime guns recovered in {selected_state}")

        # Manufacturer breakdown
        mfr_data = filtered_df[filtered_df['manufacturer_name'].notna()]

        if len(mfr_data) > 0:
            mfr_counts = mfr_data['manufacturer_name'].value_counts().reset_index()
            mfr_counts.columns = ['Manufacturer', 'Count']
            mfr_counts['Percentage'] = (mfr_counts['Count'] / mfr_counts['Count'].sum() * 100).round(1)

            # Pie chart
            fig_mfr_pie = px.pie(
                mfr_counts.head(8),
                values='Count',
                names='Manufacturer',
                title=f"Crime Guns by Manufacturer ({selected_state})",
                hole=0.4
            )
            fig_mfr_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_mfr_pie, width="stretch")

            # Table
            st.dataframe(
                mfr_counts.head(10).style.format({'Percentage': '{:.1f}%'}),
                width="stretch",
                hide_index=True
            )
        else:
            st.info("No manufacturer data available for selected filters")

    st.markdown("---")

    # Trafficking Flow Section
    st.markdown("### 🗺️ Interstate Trafficking Flow")
    st.caption(f"Source states for crime guns recovered in {selected_state}")

    # Group by dealer state
    flow_data = filtered_df[filtered_df['dealer_state'].notna()].copy()
    if len(flow_data) > 0:
        flow_counts = flow_data.groupby('dealer_state').size().reset_index(name='count')
        flow_counts = flow_counts.sort_values('count', ascending=False)
        flow_counts['percentage'] = (flow_counts['count'] / flow_counts['count'].sum() * 100).round(1)
        flow_counts['is_interstate'] = flow_counts['dealer_state'] != selected_state

        col1, col2 = st.columns([2, 1])

        with col1:
            # Bar chart
            fig_flow = px.bar(
                flow_counts,
                x='dealer_state',
                y='count',
                color='is_interstate',
                color_discrete_map={True: '#ff4b4b', False: '#1f77b4'},
                title=f"Crime Gun Sources by Dealer State (Crimes in {selected_state})",
                labels={'dealer_state': 'Dealer State', 'count': 'Crime Guns', 'is_interstate': 'Interstate'}
            )
            fig_flow.update_layout(showlegend=True)
            st.plotly_chart(fig_flow, width="stretch")

        with col2:
            st.markdown("#### Source State Breakdown")
            for _, row in flow_counts.iterrows():
                state = row['dealer_state']
                count = row['count']
                pct = row['percentage']
                is_inter = "🔴" if row['is_interstate'] else "🔵"
                st.markdown(f"{is_inter} **{state}**: {count} ({pct}%)")

    st.markdown("---")

    # Data Explorer Section
    with st.expander("📋 Raw Data Explorer", expanded=False):
        st.markdown("### Source Data with Traceability")
        st.caption("Each row links back to original source spreadsheet")

        # Column selector
        available_cols = filtered_df.columns.tolist()
        default_cols = ['source_dataset', 'source_sheet', 'source_row', 'jurisdiction_state',
                       'crime_location_state', 'crime_location_city', 'crime_location_pd',
                       'dealer_name', 'dealer_state', 'manufacturer_name', 'case_number']
        default_cols = [c for c in default_cols if c in available_cols]

        selected_cols = st.multiselect("Select columns", available_cols, default=default_cols)

        if selected_cols:
            st.dataframe(filtered_df[selected_cols], width="stretch", hide_index=True)

            # Download button
            csv = filtered_df[selected_cols].to_csv(index=False)
            st.download_button(
                label="📥 Download filtered data as CSV",
                data=csv,
                file_name=f"brady_crime_guns_{selected_state}.csv",
                mime="text/csv"
            )

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        <p><strong>Brady Gun Center - Crime Gun Supply Chain Analysis</strong></p>
        <p>Data sources: DE Gunstat, Crime Gun Dealer Database, Demand Letters (DL2), PA Trace Data</p>
        <p>MVP Dashboard v1.0</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == '__main__':
    main()
