import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

# Premium Color Palette (9.5/10 Version)
COLORS = {
    'primary': '#6366F1',    # Indigo
    'secondary': '#EC4899',  # Pink
    'success': '#10B981',    # Emerald
    'warning': '#F59E0B',    # Amber
    'danger': '#EF4444',     # Red
    'info': '#3B82F6',       # Blue
    'bg_dark': '#0F172A',    # Slate 900
    'card_bg': 'rgba(30, 41, 59, 0.7)', # Slate 800 with transparency
    'text_main': '#F8FAFC',  # Slate 50
    'text_muted': '#94A3B8'  # Slate 400
}

def load_data(filepath="data/cleaned_data.csv"):
    try:
        df = pd.read_csv(filepath)
        # Re-parse dates
        if 'Order Date' in df.columns:
            df['Order Date'] = pd.to_datetime(df['Order Date'])
        if 'Ship Date' in df.columns:
            df['Ship Date'] = pd.to_datetime(df['Ship Date'])
        return df
    except FileNotFoundError:
        return None

def apply_chart_theme(fig):
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color=COLORS['text_main'],
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)'),
        yaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)'),
        hoverlabel=dict(bgcolor=COLORS['bg_dark'], font_size=13, font_family="Inter")
    )
    return fig

def create_kpi_card(title, value, prefix="", suffix="", delta=None):
    formatted_val = f"{prefix}{value:,.2f}{suffix}" if isinstance(value, (float, int)) else f"{prefix}{value}{suffix}"
    
    delta_html = ""
    if delta is not None:
        color = COLORS['success'] if delta >= 0 else COLORS['danger']
        icon = "↑" if delta >= 0 else "↓"
        delta_html = f'<div style="color: {color}; font-size: 0.8rem; font-weight: 600; margin-top: 4px;">{icon} {abs(delta):.1f}% vs last month</div>'

    card_html = f"""
    <div style="
        background: {COLORS['card_bg']};
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease-in-out;
        margin-bottom: 20px;
        height: 100%;
    ">
        <h4 style="color: {COLORS['text_muted']}; margin: 0; font-size: 0.85rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em;">{title}</h4>
        <h2 style="color: {COLORS['text_main']}; margin: 12px 0 0 0; font-size: 2rem; font-weight: 700; font-family: 'Inter', sans-serif;">{formatted_val}</h2>
        {delta_html}
    </div>
    """
    return card_html

def plot_quadrant_chart(df):
    prod_df = df.groupby('Product Name').agg({
        'Sales': 'sum',
        'Gross Margin %': 'mean'
    }).reset_index()
    med_sales = prod_df['Sales'].median()
    med_margin = prod_df['Gross Margin %'].median()
    
    def get_category(row):
        if row['Sales'] >= med_sales and row['Gross Margin %'] >= med_margin: return 'Star Products'
        elif row['Sales'] >= med_sales and row['Gross Margin %'] < med_margin: return 'Dangerous Products'
        elif row['Sales'] < med_sales and row['Gross Margin %'] >= med_margin: return 'Hidden Gems'
        else: return 'Remove Candidates'
            
    prod_df['Category'] = prod_df.apply(get_category, axis=1)
    color_map = {'Star Products': COLORS['success'], 'Dangerous Products': COLORS['danger'], 'Hidden Gems': COLORS['info'], 'Remove Candidates': COLORS['text_muted']}
    
    fig = px.scatter(prod_df, x='Sales', y='Gross Margin %', color='Category', hover_data=['Product Name'], color_discrete_map=color_map, title="Profitability Portfolio Matrix")
    fig.add_hline(y=med_margin, line_dash="dash", line_color=COLORS['text_muted'], opacity=0.5)
    fig.add_vline(x=med_sales, line_dash="dash", line_color=COLORS['text_muted'], opacity=0.5)
    return apply_chart_theme(fig)

def plot_cost_diagnostics(df):
    prod_df = df.groupby('Product Name').agg({'Sales': 'sum', 'Cost': 'sum', 'Gross Profit': 'sum'}).reset_index()
    fig = px.scatter(prod_df, x='Sales', y='Cost', size='Gross Profit', hover_name='Product Name', title="Cost-to-Sales Efficiency", color='Cost', color_continuous_scale="RdYlGn_r")
    return apply_chart_theme(fig)

def plot_pareto(df):
    prod_profit = df.groupby('Product Name')['Gross Profit'].sum().sort_values(ascending=False).reset_index()
    prod_profit = prod_profit[prod_profit['Gross Profit'] > 0]
    prod_profit['Cumulative %'] = 100 * prod_profit['Gross Profit'].cumsum() / prod_profit['Gross Profit'].sum()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=prod_profit['Product Name'], y=prod_profit['Gross Profit'], name='Profit', marker_color=COLORS['primary']))
    fig.add_trace(go.Scatter(x=prod_profit['Product Name'], y=prod_profit['Cumulative %'], name='Cumulative', yaxis='y2', marker_color=COLORS['secondary'], mode='lines+markers'))
    fig.update_layout(yaxis2=dict(overlaying='y', side='right', range=[0, 105]))
    return apply_chart_theme(fig)
