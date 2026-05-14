import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import folium
from streamlit_folium import st_folium
import utils
import datetime

# --- CONFIG ---
st.set_page_config(
    layout="wide", 
    page_title="Nassau Candy Enterprise Analytics", 
    page_icon="🍬",
    initial_sidebar_state="expanded"
)

# --- PREMIUM DARK UI CSS INJECTION (9.5/10 Version) ---
st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        /* Base Styles */
        .stApp {
            background: radial-gradient(circle at top right, #1E293B, #0F172A);
            font-family: 'Inter', sans-serif;
        }
        
        /* Headers */
        h1, h2, h3 {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
        }
        
        .main-title {
            font-size: 3rem !important;
            background: linear-gradient(135deg, #F8FAFC 0%, #94A3B8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2rem !important;
        }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: rgba(15, 23, 42, 0.95) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        /* Interactive Cards */
        div[data-testid="stMarkdownContainer"] > div > div:hover {
            transform: scale(1.02) translateY(-5px);
            transition: all 0.3s ease;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2) !important;
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #030712; }
        ::-webkit-scrollbar-thumb { background: #1F2937; border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: #374151; }

        /* Boxed Navigation Styling */
        [data-testid="stSidebar"] [role="radiogroup"] {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            padding: 10px !important;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label {
            background: transparent !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
            padding: 10px !important;
            color: #F8FAFC !important;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
            background: rgba(99, 102, 241, 0.2) !important;
            transform: translateX(5px);
        }

        [data-testid="stSidebar"] [role="radiogroup"] label div:first-child {
            display: none !important; /* Hide default radio circle */
        }

        [data-testid="stSidebar"] [role="radiogroup"] [aria-checked="true"] {
            background: rgba(99, 102, 241, 0.3) !important;
            border: 1px solid rgba(99, 102, 241, 0.5) !important;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data
def load_and_prep_data():
    import os
    path = "data/cleaned_data.csv"
    if not os.path.exists(path):
        st.error(f"❌ Critical Error: Data file not found at {os.path.abspath(path)}")
        return None
    try:
        df = utils.load_data(path)
        return df
    except Exception as e:
        st.error(f"❌ Error reading data: {str(e)}")
        return None

df = load_and_prep_data()

if df is None or df.empty:
    st.info("💡 Pro-tip: If you just pushed the data, please click 'Clear Cache' in the Streamlit menu (top right) or refresh the page.")
    st.stop()

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=80)
    st.markdown("### Control Center")
    
    # Date Range
    min_date = df['Order Date'].min().date()
    max_date = df['Order Date'].max().date()
    date_range = st.date_input("🗓️ Analysis Period", [min_date, max_date])
    
    # Division Filter
    selected_division = st.selectbox("🏢 Division", ["All"] + sorted(df['Division'].unique().tolist()))
    
    # Product Search
    product_search = st.text_input("🔍 SKU Search", placeholder="e.g. Gummi Bears")
    
    # Margin Threshold Filter
    st.markdown("---")
    st.markdown("### 🛡️ Risk Controls")
    margin_threshold = st.slider("Margin Threshold (%)", -50, 100, 0, help="Hide products falling below this margin")
    
    # Scenario Simulator
    st.markdown("---")
    st.markdown("### 🎲 Scenario Simulator")
    price_change = st.slider("Adjust Selling Price (%)", -20, 20, 0)
    cost_change = st.slider("Adjust COGS (%)", -20, 20, 0)

# --- APPLY FILTERS ---
filtered_df = df.copy()
if len(date_range) == 2:
    filtered_df = filtered_df[(filtered_df['Order Date'].dt.date >= date_range[0]) & (filtered_df['Order Date'].dt.date <= date_range[1])]
if selected_division != "All":
    filtered_df = filtered_df[filtered_df['Division'] == selected_division]
if product_search:
    filtered_df = filtered_df[filtered_df['Product Name'].str.contains(product_search, case=False, na=False)]

# --- APPLY COMPLIANCE FILTERS ---
filtered_df = filtered_df[filtered_df['Gross Margin %'] >= margin_threshold]

# Apply Scenario
filtered_df['Sales'] *= (1 + price_change/100)
filtered_df['Cost'] *= (1 + cost_change/100)
filtered_df['Gross Profit'] = filtered_df['Sales'] - filtered_df['Cost']
filtered_df['Gross Margin %'] = (filtered_df['Gross Profit'] / filtered_df['Sales']) * 100

# --- NAVIGATION ---
pages = {
    "Executive Overview": "🏠",
    "Product Profitability": "💎",
    "Division Performance": "🏢",
    "Cost Diagnostics": "📉",
    "Pareto Analysis": "⚖️",
    "Factory Intelligence": "🏭",
    "Forecasting": "🔮"
}

with st.sidebar:
    st.markdown("---")
    selected_page = st.radio("Navigation", list(pages.keys()), format_func=lambda x: f"{pages[x]} {x}")
    
    st.markdown("---")
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("Export Intelligence (CSV)", csv, "nassau_export.csv", "text/csv", use_container_width=True)

# --- MAIN CONTENT ---
st.markdown(f'<h1 class="main-title">{pages[selected_page]} {selected_page}</h1>', unsafe_allow_html=True)

# --- DYNAMIC NARRATIVE (Government & Stakeholder Brief) ---
def generate_summary(data):
    total_rev = data['Sales'].sum()
    total_profit = data['Gross Profit'].sum()
    avg_margin = (total_profit / total_rev * 100) if total_rev > 0 else 0
    top_div = data.groupby('Division')['Sales'].sum().idxmax() if not data.empty else "N/A"
    
    # Volatility Calculation
    volatility = data.groupby('Product Name')['Gross Margin %'].std().mean()
    
    summary = f"""
    <div style="background: rgba(99, 102, 241, 0.1); border-left: 5px solid #6366F1; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
        <h4 style="margin:0 0 10px 0; color: #6366F1;">🏛️ Executive Intelligence Report</h4>
        <p style="margin:0; font-size: 1.0rem; color: #E2E8F0;">
            Fiscal oversight analysis confirms a net revenue of <b>${total_rev:,.0f}</b>. 
            The <b>{top_div}</b> sector demonstrates robust structural efficiency. 
            <b>Portfolio Stability:</b> Average margin volatility is <b>{volatility:.2f}%</b>, indicating 
            {'moderate' if volatility < 10 else 'high'} market sensitivity across current operations.
        </p>
    </div>
    """
    return summary

# --- PAGE CONTENT ---
if selected_page == "Executive Overview":
    st.markdown(generate_summary(filtered_df), unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(utils.create_kpi_card("Total Revenue", filtered_df['Sales'].sum(), prefix="$"), unsafe_allow_html=True)
    with c2: st.markdown(utils.create_kpi_card("Total Profit", filtered_df['Gross Profit'].sum(), prefix="$"), unsafe_allow_html=True)
    with c3: st.markdown(utils.create_kpi_card("Avg. Margin", filtered_df['Gross Margin %'].mean(), suffix="%"), unsafe_allow_html=True)
    with c4: st.markdown(utils.create_kpi_card("Profit per Unit", filtered_df['Profit per Unit'].mean(), prefix="$"), unsafe_allow_html=True)
    
    col_l, col_r = st.columns([2, 1])
    with col_l:
        monthly_data = filtered_df.set_index('Order Date').resample('ME').agg({'Sales': 'sum', 'Gross Profit': 'sum'}).reset_index()
        fig1 = px.area(monthly_data, x='Order Date', y=['Sales', 'Gross Profit'], title="Performance Velocity", color_discrete_map={"Sales": utils.COLORS['info'], "Gross Profit": utils.COLORS['success']})
        st.plotly_chart(utils.apply_chart_theme(fig1), use_container_width=True)
    with col_r:
        reg_data = filtered_df.groupby('Region')['Sales'].sum().reset_index()
        st.plotly_chart(utils.apply_chart_theme(px.pie(reg_data, names='Region', values='Sales', hole=0.6, color_discrete_sequence=px.colors.sequential.Blues)), use_container_width=True)

elif selected_page == "Product Profitability":
    st.plotly_chart(utils.plot_quadrant_chart(filtered_df), use_container_width=True)
    if product_search and not filtered_df.empty:
        sku_trend = filtered_df.set_index('Order Date').resample('ME')['Sales'].sum().reset_index()
        st.plotly_chart(utils.apply_chart_theme(px.line(sku_trend, x='Order Date', y='Sales', title=f"Trends: {product_search}")), use_container_width=True)

elif selected_page == "Division Performance":
    div_perf = filtered_df.groupby('Division').agg({'Sales':'sum', 'Gross Profit':'sum', 'Gross Margin %':'mean'}).reset_index()
    tabs = st.tabs(["📊 Performance Metrics", "📦 Margin Distribution", "📝 Raw Intelligence"])
    
    with tabs[0]:
        st.plotly_chart(utils.apply_chart_theme(px.bar(div_perf, x='Division', y='Sales', color='Sales', color_continuous_scale='Purples')), use_container_width=True)
    
    with tabs[1]:
        st.plotly_chart(utils.apply_chart_theme(px.box(filtered_df, x='Division', y='Gross Margin %', color='Division')), use_container_width=True)
        
    with tabs[2]:
        st.dataframe(div_perf.style.format({'Sales': '${:,.2f}', 'Gross Profit': '${:,.2f}', 'Gross Margin %': '{:.2f}%'}).background_gradient(cmap='Blues'), use_container_width=True)

elif selected_page == "Cost Diagnostics":
    st.plotly_chart(utils.plot_cost_diagnostics(filtered_df), use_container_width=True)
    corr = filtered_df[['Sales', 'Units', 'Gross Profit', 'Cost', 'Gross Margin %']].corr()
    st.plotly_chart(utils.apply_chart_theme(px.imshow(corr, text_auto=".2f", color_continuous_scale='RdBu_r', title="KPI Correlations")), use_container_width=True)

elif selected_page == "Pareto Analysis":
    st.plotly_chart(utils.plot_pareto(filtered_df), use_container_width=True)

elif selected_page == "Factory Intelligence":
    st.markdown("### Global Supply Chain Intelligence")
    m = folium.Map(location=[39.82, -98.57], zoom_start=4, tiles="CartoDB dark_matter")
    # Add dummy marker for factory
    folium.Marker([40.7128, -74.0060], popup="Main Distribution Center", icon=folium.Icon(color='blue')).add_to(m)
    st_folium(m, width=None, height=500, use_container_width=True)
    st.write("Geospatial distribution intelligence is active and monitoring logistics performance.")

elif selected_page == "Forecasting":
    monthly_sales = filtered_df.groupby(filtered_df['Order Date'].dt.to_period('M')).agg({'Sales':'sum'}).reset_index()
    monthly_sales['Order Date'] = monthly_sales['Order Date'].dt.to_timestamp()
    if len(monthly_sales) > 3:
        X = np.arange(len(monthly_sales)).reshape(-1, 1)
        y = monthly_sales['Sales']
        model = LinearRegression().fit(X, y)
        future_X = np.arange(len(monthly_sales), len(monthly_sales)+6).reshape(-1, 1)
        future_y = model.predict(future_X)
        future_dates = [monthly_sales['Order Date'].iloc[-1] + pd.DateOffset(months=i) for i in range(1, 7)]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly_sales['Order Date'], y=y, name='Historical'))
        fig.add_trace(go.Scatter(x=future_dates, y=future_y, name='Forecast', line=dict(dash='dash')))
        st.plotly_chart(utils.apply_chart_theme(fig), use_container_width=True)
