import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Veridi Logistics — Delivery Audit",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background-color: #0f1117; color: #e8e8e8; }
section[data-testid="stSidebar"] { background-color: #161b27; border-right: 1px solid #2a2f3e; }
[data-testid="metric-container"] { background: #161b27; border: 1px solid #2a2f3e; border-radius: 12px; padding: 16px !important; }
[data-testid="stMetricLabel"] { font-family: 'DM Mono', monospace !important; font-size: 11px !important; color: #6b7280 !important; text-transform: uppercase; letter-spacing: 0.08em; }
[data-testid="stMetricValue"] { font-family: 'DM Mono', monospace !important; font-size: 28px !important; color: #f0f0f0 !important; }
[data-testid="stMetricDelta"] { font-family: 'DM Mono', monospace !important; font-size: 12px !important; }
h1, h2, h3 { font-family: 'DM Sans', sans-serif !important; font-weight: 700 !important; color: #f0f0f0 !important; }
hr { border-color: #2a2f3e; }
.insight-box { background: linear-gradient(135deg, #1a1f2e, #161b27); border-left: 3px solid #3b82f6; border-radius: 0 12px 12px 0; padding: 16px 20px; margin: 12px 0; font-size: 14px; line-height: 1.6; color: #c8d0e0; }
.insight-box strong { color: #f0f0f0; }
.file-tag { display: inline-block; background: #1e2433; border: 1px solid #2a2f3e; border-radius: 8px; padding: 4px 12px; margin: 4px; font-family: 'DM Mono', monospace; font-size: 11px; color: #6b7280; }
</style>
""", unsafe_allow_html=True)

LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='DM Sans', color='#9ca3af', size=12),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#9ca3af')),
)
# Default axis style - applied per chart to avoid duplicate keyword errors
_AX = dict(gridcolor='#1e2433', linecolor='#2a2f3e', tickfont=dict(color='#6b7280'))
STATUS_COLORS = {'On Time': '#2ecc71', 'Late': '#f39c12', 'Super Late': '#e74c3c'}
ORDER_CATS = ['On Time', 'Late', 'Super Late']

REQUIRED_FILES = [
    "olist_orders_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_products_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "product_category_name_translation.csv",
]

def show_upload_screen():
    st.markdown("""
    <div style="padding: 20px 0 8px 0;">
      <h1 style="font-size:32px; margin:0; letter-spacing:-0.5px;">🚚 Veridi Logistics</h1>
      <p style="color:#6b7280; font-size:14px; margin:4px 0 0 0; font-family: DM Mono, monospace;">LAST MILE DELIVERY PERFORMANCE AUDIT</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.markdown("### Upload your Olist dataset files to begin")
    st.markdown("<p style='color:#6b7280;font-size:13px;'>Upload all 7 CSV files. They are never stored — processed in memory only.</p>", unsafe_allow_html=True)
    st.markdown(" ".join([f"<span class='file-tag'>{f}</span>" for f in REQUIRED_FILES]), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    uploaded = st.file_uploader("Drop all 7 CSV files here", type="csv",
                                  accept_multiple_files=True, label_visibility="collapsed")
    if uploaded:
        found = {f.name: f for f in uploaded}
        missing = [n for n in REQUIRED_FILES if n not in found]
        ready   = [n for n in REQUIRED_FILES if n in found]
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Uploaded**")
            for n in ready:
                st.markdown(f"<span class='file-tag' style='color:#2ecc71'>{n}</span>", unsafe_allow_html=True)
        with col2:
            if missing:
                st.markdown("**Still needed**")
                for n in missing:
                    st.markdown(f"<span class='file-tag' style='color:#e74c3c'>{n}</span>", unsafe_allow_html=True)
        if not missing:
            st.success("All files uploaded! Loading dashboard...")
            return found
    return None

@st.cache_data(show_spinner="Processing data...")
def process_data(file_bytes):
    def read(name):
        return pd.read_csv(io.BytesIO(file_bytes[name]))

    orders      = read("olist_orders_dataset.csv")
    reviews     = read("olist_order_reviews_dataset.csv")
    customers   = read("olist_customers_dataset.csv")
    products    = read("olist_products_dataset.csv")
    items       = read("olist_order_items_dataset.csv")
    payments    = read("olist_order_payments_dataset.csv")
    translation = read("product_category_name_translation.csv")

    for col in ['order_purchase_timestamp','order_approved_at',
                'order_delivered_carrier_date','order_delivered_customer_date',
                'order_estimated_delivery_date']:
        orders[col] = pd.to_datetime(orders[col])

    reviews_clean = (reviews.sort_values('review_answer_timestamp', ascending=False)
                     .drop_duplicates(subset='order_id', keep='first'))

    master = (orders
        .merge(reviews_clean[['order_id','review_score']], on='order_id', how='left')
        .merge(customers[['customer_id','customer_state','customer_city']], on='customer_id', how='left'))

    items_prod = (items[['order_id','product_id']].drop_duplicates('order_id')
        .merge(products[['product_id','product_category_name']], on='product_id', how='left')
        .merge(translation, on='product_category_name', how='left'))
    master = master.merge(items_prod[['order_id','product_category_name_english']], on='order_id', how='left')

    delivered = master[
        (master['order_status'] == 'delivered') &
        (master['order_delivered_customer_date'].notna())
    ].copy()

    delivered['days_difference'] = (
        delivered['order_delivered_customer_date'] -
        delivered['order_estimated_delivery_date']
    ).dt.days

    def classify(d):
        if d <= 0:    return 'On Time'
        elif d <= 5:  return 'Late'
        else:         return 'Super Late'

    delivered['delivery_status'] = delivered['days_difference'].apply(classify)

    order_value = payments.groupby('order_id')['payment_value'].sum().reset_index()
    order_value.columns = ['order_id','order_value']
    delivered = delivered.merge(order_value, on='order_id', how='left')
    delivered['order_month'] = delivered['order_purchase_timestamp'].dt.to_period('M').astype(str)
    return delivered

def show_dashboard(df):
    with st.sidebar:
        st.markdown("### 🚚 Veridi Logistics")
        st.markdown("<p style='color:#6b7280;font-size:11px;font-family:DM Mono,monospace'>DELIVERY PERFORMANCE AUDIT</p>", unsafe_allow_html=True)
        st.divider()
        st.markdown("**Filter by Status**")
        show_ontime    = st.checkbox("On Time",    value=True)
        show_late      = st.checkbox("Late",       value=True)
        show_superlate = st.checkbox("Super Late", value=True)
        st.divider()
        all_states = sorted(df['customer_state'].dropna().unique())
        sel_states = st.multiselect("Filter by State", all_states, default=all_states)
        st.divider()
        all_cats = sorted(df['product_category_name_english'].dropna().unique())
        sel_cats = st.multiselect("Filter by Category", all_cats, default=[])
        st.divider()
        if st.button("Upload new files", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        st.markdown("<p style='color:#4b5563;font-size:11px;font-family:DM Mono,monospace'>Data: Olist Brazilian E-Commerce<br>Orders: 2016-2018</p>", unsafe_allow_html=True)

    statuses = ((['On Time'] if show_ontime else []) +
                (['Late'] if show_late else []) +
                (['Super Late'] if show_superlate else []))
    filt = df[df['delivery_status'].isin(statuses)]
    if sel_states: filt = filt[filt['customer_state'].isin(sel_states)]
    if sel_cats:   filt = filt[filt['product_category_name_english'].isin(sel_cats)]

    st.markdown("""
    <div style="padding: 8px 0 20px 0;">
      <h1 style="font-size:32px; margin:0; letter-spacing:-0.5px;">Last Mile Delivery Audit</h1>
      <p style="color:#6b7280; font-size:14px; margin:4px 0 0 0; font-family: DM Mono, monospace;">Veridi Logistics · Brazil · Olist E-Commerce Dataset</p>
    </div>
    """, unsafe_allow_html=True)

    total   = len(filt)
    on_time = (filt['delivery_status'] == 'On Time').sum()
    late    = (filt['delivery_status'] == 'Late').sum()
    s_late  = (filt['delivery_status'] == 'Super Late').sum()
    at_risk = filt[filt['delivery_status'] != 'On Time']['order_value'].sum()

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total Orders",    f"{total:,}")
    c2.metric("On Time",         f"{on_time/total*100:.1f}%",  f"{on_time:,} orders")
    c3.metric("Late (1-5 days)", f"{late/total*100:.1f}%",     f"{late:,} orders")
    c4.metric("Super Late",      f"{s_late/total*100:.1f}%",   f"{s_late:,} orders")
    c5.metric("Revenue at Risk", f"R$ {at_risk/1e6:.2f}M",     "Late + Super Late")
    st.divider()

    col1,col2 = st.columns([1,2])
    with col1:
        st.markdown("#### Delivery Status")
        sc = filt['delivery_status'].value_counts().reset_index()
        sc.columns = ['status','count']
        fig = px.pie(sc, names='status', values='count', color='status',
                     color_discrete_map=STATUS_COLORS, hole=0.55)
        fig.update_traces(textposition='outside', textinfo='percent+label',
                          textfont=dict(color='#9ca3af', size=12))
        fig.update_layout(**LAYOUT, height=300, showlegend=False,
                          annotations=[dict(text=f"{on_time/total*100:.0f}%<br>On Time",
                                            x=0.5, y=0.5, font_size=18,
                                            font_color='#f0f0f0', showarrow=False)])
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("#### Delay Distribution")
        fig2 = px.histogram(filt, x='days_difference', nbins=80, color_discrete_sequence=['#3b82f6'])
        fig2.add_vline(x=0, line_color='#2ecc71', line_dash='dash',
                       annotation_text="Estimated date", annotation_font_color='#2ecc71')
        fig2.add_vline(x=5, line_color='#e74c3c', line_dash='dash',
                       annotation_text="Super Late threshold", annotation_font_color='#e74c3c')
        fig2.update_layout(**LAYOUT, height=300,
                            xaxis=dict(**_AX, title="Days (Actual - Estimated)"),
                            yaxis=dict(**_AX, title="Number of Orders"))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="insight-box">📌 <strong>93.2% of orders arrive on time.</strong> However the 6.8% that are late trigger a <strong>47% drop in review score</strong> — from 4.29 to 2.27 stars. Lateness, not volume, is the core problem.</div>', unsafe_allow_html=True)
    st.divider()

    st.markdown("#### Late Delivery Rate by State")
    geo = (filt.groupby('customer_state')
        .agg(total_orders=('order_id','count'),
             late_orders =('delivery_status', lambda x:(x!='On Time').sum()),
             avg_delay   =('days_difference','mean'),
             avg_review  =('review_score','mean'))
        .reset_index())
    geo['pct_late'] = (geo['late_orders']/geo['total_orders']*100).round(1)
    geo = geo.sort_values('pct_late', ascending=False)

    cg1,cg2 = st.columns([2,1])
    with cg1:
        fig3 = px.bar(geo, x='customer_state', y='pct_late', color='pct_late',
                      color_continuous_scale=[[0,'#2ecc71'],[0.3,'#f39c12'],[1,'#e74c3c']],
                      custom_data=['avg_delay','avg_review','total_orders'])
        fig3.update_traces(hovertemplate="<b>%{x}</b><br>Late: %{y:.1f}%<br>Avg Delay: %{customdata[0]:.1f}d<br>Avg Review: %{customdata[1]:.2f} star<br>Orders: %{customdata[2]:,}<extra></extra>")
        fig3.add_hline(y=geo['pct_late'].mean(), line_color='#9ca3af', line_dash='dot',
                       annotation_text=f"Avg {geo['pct_late'].mean():.1f}%", annotation_font_color='#9ca3af')
        fig3.update_layout(**LAYOUT, height=320, coloraxis_showscale=False,
                            xaxis=dict(**_AX, title="State"),
                            yaxis=dict(**_AX, title="% Late Orders"))
        st.plotly_chart(fig3, use_container_width=True)
    with cg2:
        st.markdown("**Top 8 Worst States**")
        worst = geo.head(8)[['customer_state','pct_late','avg_delay','avg_review']].copy()
        worst.columns = ['State','% Late','Avg Delay','Avg Review']
        worst['% Late']    = worst['% Late'].apply(lambda x: f"{x:.1f}%")
        worst['Avg Delay'] = worst['Avg Delay'].apply(lambda x: f"{x:.1f}d")
        worst['Avg Review']= worst['Avg Review'].apply(lambda x: f"{x:.2f} star")
        st.dataframe(worst, hide_index=True, use_container_width=True, height=285)

    st.markdown('<div class="insight-box">🗺️ <strong>This is a regional problem, not nationwide.</strong> Northern and northeastern states (AL, AM, RR, AP) have <strong>3-5x higher late rates</strong> than Sao Paulo — pointing to last-mile infrastructure gaps far from the distribution hub.</div>', unsafe_allow_html=True)
    st.divider()

    st.markdown("#### Sentiment Correlation — Does Late = Bad Reviews?")
    sent = (filt.dropna(subset=['review_score']).groupby('delivery_status')['review_score']
            .mean().reset_index())
    sent.columns = ['status','avg_score']
    sent['status'] = pd.Categorical(sent['status'], categories=ORDER_CATS, ordered=True)
    sent = sent.sort_values('status')

    bins  = sorted(set(list(range(-30,11)) + list(range(10,61,5))))
    filt2 = filt.copy()
    filt2['delay_bin'] = pd.cut(filt2['days_difference'], bins=bins, duplicates='drop')
    bin_rv = filt2.groupby('delay_bin', observed=True)['review_score'].mean().reset_index()
    bin_rv['bin_mid'] = bin_rv['delay_bin'].apply(lambda x: x.mid)
    bin_rv = bin_rv.dropna()

    cs1,cs2 = st.columns(2)
    with cs1:
        fig4 = px.bar(sent, x='status', y='avg_score', color='status',
                      color_discrete_map=STATUS_COLORS, text='avg_score')
        fig4.update_traces(texttemplate='%{text:.2f} star', textposition='outside',
                            textfont=dict(color='#f0f0f0'))
        fig4.update_layout(**LAYOUT, height=320, showlegend=False,
                            xaxis=dict(**_AX),
                            yaxis=dict(**_AX, range=[1,5.5]),
                            yaxis_title="Avg Review Score (1-5)")
        st.plotly_chart(fig4, use_container_width=True)
    with cs2:
        fig5 = go.Figure()
        fig5.add_trace(go.Scatter(x=bin_rv['bin_mid'], y=bin_rv['review_score'],
                                   mode='lines+markers', line=dict(color='#3b82f6', width=2),
                                   marker=dict(size=5, color='#3b82f6')))
        fig5.add_vline(x=0, line_color='#2ecc71', line_dash='dash')
        fig5.add_vline(x=5, line_color='#e74c3c', line_dash='dash')
        fig5.update_layout(**LAYOUT, height=320,
                            xaxis=dict(**_AX, title="Days Late"),
                            yaxis=dict(**_AX, range=[1,5.5], title="Avg Review Score"))
        st.plotly_chart(fig5, use_container_width=True)
    st.divider()

    st.markdown("#### Product Categories & Revenue at Risk")
    cat_df = (filt.dropna(subset=['product_category_name_english'])
        .groupby('product_category_name_english')
        .agg(total=('order_id','count'), late=('delivery_status', lambda x:(x!='On Time').sum()),
             avg_review=('review_score','mean'))
        .reset_index())
    cat_df['pct_late'] = (cat_df['late']/cat_df['total']*100).round(1)
    cat_df = cat_df[cat_df['total']>=100].sort_values('pct_late', ascending=False).head(15)

    rev_df = filt.groupby('delivery_status').agg(orders=('order_id','count'), revenue=('order_value','sum')).reset_index()
    rev_df['status'] = pd.Categorical(rev_df['delivery_status'], categories=ORDER_CATS, ordered=True)
    rev_df = rev_df.sort_values('status')

    cc1,cc2 = st.columns([3,2])
    with cc1:
        st.markdown("**Late Rate by Category (English)**")
        fig6 = px.bar(cat_df, x='pct_late', y='product_category_name_english', orientation='h',
                      color='pct_late', color_continuous_scale=[[0,'#2ecc71'],[0.3,'#f39c12'],[1,'#e74c3c']],
                      custom_data=['total','avg_review'])
        fig6.update_traces(hovertemplate="<b>%{y}</b><br>Late: %{x:.1f}%<br>Orders: %{customdata[0]:,}<br>Avg Review: %{customdata[1]:.2f} star<extra></extra>")
        fig6.update_layout(**LAYOUT, height=380, coloraxis_showscale=False,
                            xaxis=dict(**_AX, title="% Late Orders"),
                            yaxis=dict(**_AX, autorange="reversed"))
        st.plotly_chart(fig6, use_container_width=True)
    with cc2:
        st.markdown("**Revenue at Risk**")
        fig7 = px.bar(rev_df, x='delivery_status', y='revenue', color='delivery_status',
                      color_discrete_map=STATUS_COLORS, text='revenue')
        fig7.update_traces(texttemplate='R$%{text:,.0f}', textposition='outside',
                            textfont=dict(color='#9ca3af', size=10))
        fig7.update_layout(**LAYOUT, height=300, showlegend=False,
                            xaxis=dict(**_AX),
                            yaxis=dict(**_AX, title="Total Revenue (R$)"))
        st.plotly_chart(fig7, use_container_width=True)
        at_risk_val = filt[filt['delivery_status']!='On Time']['order_value'].sum()
        st.markdown(f'<div class="insight-box">💰 <strong>R$ {at_risk_val:,.0f}</strong> in revenue is tied to late deliveries — at direct risk of refunds and lost repeat purchases.</div>', unsafe_allow_html=True)
    st.divider()

    st.markdown("#### Candidate's Choice — Late Rate Trend Over Time")
    st.markdown("<p style='color:#6b7280;font-size:13px;margin-top:-8px'>Reveals whether the problem is worsening, seasonal, or improving.</p>", unsafe_allow_html=True)
    monthly = (filt.groupby('order_month')
        .agg(total=('order_id','count'), late=('delivery_status', lambda x:(x!='On Time').sum()))
        .reset_index())
    monthly['pct_late'] = (monthly['late']/monthly['total']*100).round(1)
    monthly = monthly[monthly['total']>=50].sort_values('order_month')

    fig8 = go.Figure()
    fig8.add_trace(go.Scatter(x=monthly['order_month'], y=monthly['pct_late'],
                               fill='tozeroy', fillcolor='rgba(59,130,246,0.08)',
                               line=dict(color='#3b82f6', width=2.5),
                               mode='lines+markers', marker=dict(size=6, color='#3b82f6')))
    fig8.update_layout(**LAYOUT, height=260,
                        xaxis=dict(**_AX, tickangle=-30, title="Month"),
                        yaxis=dict(**_AX, title="% Late Orders"))
    st.plotly_chart(fig8, use_container_width=True)

    st.divider()
    st.markdown("<p style='text-align:center;color:#4b5563;font-size:11px;font-family:DM Mono,monospace;'>Veridi Logistics Delivery Audit · Olist Brazilian E-Commerce (Kaggle) · Built with Streamlit + Plotly</p>", unsafe_allow_html=True)

def main():
    if 'file_bytes' not in st.session_state:
        uploaded_files = show_upload_screen()
        if uploaded_files is None:
            st.stop()
        st.session_state['file_bytes'] = {name: f.read() for name, f in uploaded_files.items()}
        st.rerun()
    df = process_data(st.session_state['file_bytes'])
    show_dashboard(df)

if __name__ == "__main__":
    main()
