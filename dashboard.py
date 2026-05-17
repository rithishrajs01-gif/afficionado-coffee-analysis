import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import warnings, os, json
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Afficionado Coffee Roasters", page_icon="☕", layout="wide")

BG='#FDF6EC'; DARK='#3E2006'; ACCENT='#6F4E37'; C2='#C8A97E'; C3='#A0522D'
LOC_COLORS=['#6F4E37','#C8A97E','#A0522D']
LOCS=["Lower Manhattan","Hell's Kitchen",'Astoria']
DOW_ORDER=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

plt.rcParams.update({
    'figure.facecolor':BG,'axes.facecolor':BG,'axes.edgecolor':'#C8A97E',
    'axes.labelcolor':DARK,'xtick.color':DARK,'ytick.color':DARK,'text.color':DARK,
    'grid.color':'#E8D5B7','grid.linestyle':'--','grid.alpha':0.5,
    'axes.spines.top':False,'axes.spines.right':False
})

st.markdown("""<style>
.metric-card{background:linear-gradient(135deg,#6F4E37,#A0522D);border-radius:12px;
padding:20px 24px;color:white;text-align:center;margin-bottom:8px;}
.metric-card h2{margin:0;font-size:2rem;font-weight:700;}
.metric-card p{margin:4px 0 0;font-size:0.85rem;opacity:0.85;}
</style>""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    d = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(d, 'coffee_data.json')) as f:
        return json.load(f)

data = load_data()
kpis = data['kpis']
weekly = pd.DataFrame(data['weekly'])
ml = pd.DataFrame(data['monthly_loc'])
cat = pd.DataFrame(data['category'])
dow = pd.DataFrame(data['dow'])
hourly = pd.DataFrame(data['hourly'])
heat_df = pd.DataFrame(data['heat'])
loc_rev = pd.DataFrame(data['loc_rev'])
ph = pd.DataFrame(data['peak_hour'])

st.sidebar.title("☕ Filters")
st.sidebar.markdown("---")
st.sidebar.info("ℹ️ This dashboard uses pre-aggregated data. Filters shown for display.")
metric = st.sidebar.radio("📊 Metric", options=["Revenue ($)","Transaction Count"], index=0)
st.sidebar.markdown("---")
st.sidebar.caption("Afficionado Coffee Roasters\nSales Analytics v1.0")

st.markdown("# ☕ Afficionado Coffee Roasters")
st.markdown("### Sales Trend & Time-Based Performance Dashboard — 2025")
st.markdown("---")

k1,k2,k3,k4,k5,k6 = st.columns(6)
for col,val,label in [
    (k1, f"${kpis['total_rev']:,.0f}", "Total Revenue"),
    (k2, f"{kpis['total_txn']:,}", "Transactions"),
    (k3, f"${kpis['avg_order']:.2f}", "Avg Order Value"),
    (k4, f"{kpis['peak_hour']}:00", "Peak Hour"),
    (k5, kpis['peak_day'], "Busiest Day"),
    (k6, kpis['top_loc'], "Top Location"),
]:
    with col:
        st.markdown(f'<div class="metric-card"><h2>{val}</h2><p>{label}</p></div>', unsafe_allow_html=True)

st.markdown("---")
tab1,tab2,tab3,tab4 = st.tabs(["📈 Sales Trends","📅 Day-of-Week","🕐 Hourly Demand","🗺️ Location Comparison"])

with tab1:
    st.subheader("Weekly Sales Trend")
    y_col = 'revenue' if 'Revenue' in metric else 'transactions'
    fig,ax = plt.subplots(figsize=(12,4.5)); fig.patch.set_facecolor(BG)
    ax.plot(weekly['week'], weekly[y_col], color=ACCENT, lw=2.5, marker='o', markersize=4)
    ax.fill_between(weekly['week'], weekly[y_col], alpha=0.12, color=ACCENT)
    if len(weekly)>1:
        z = np.polyfit(weekly['week'], weekly[y_col], 1)
        ax.plot(weekly['week'], np.poly1d(z)(weekly['week']), '--', color=C3, lw=1.5, alpha=0.7, label='Trend')
        ax.legend()
    if 'Revenue' in metric: ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_:f'${x:,.0f}'))
    ax.set_xlabel('Week'); ax.set_ylabel(metric)
    ax.set_title('Weekly Revenue Trend (Jan–Jul 2025)', fontsize=13, fontweight='bold', color=DARK)
    ax.grid(True,axis='y'); plt.tight_layout(); st.pyplot(fig); plt.close()

    c1,c2 = st.columns(2)
    with c1:
        st.subheader("Monthly Revenue by Location")
        fig,ax = plt.subplots(figsize=(7,4)); fig.patch.set_facecolor(BG)
        for loc,color in zip(LOCS, LOC_COLORS):
            d = ml[ml['store_location']==loc].sort_values('month')
            ax.plot(d['month'], d['revenue'], marker='o', label=loc, color=color, lw=2)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_:f'${x:,.0f}'))
        ax.set_title('Monthly Revenue by Location', fontsize=11, fontweight='bold', color=DARK)
        ax.legend(fontsize=9); ax.grid(True,axis='y'); plt.tight_layout(); st.pyplot(fig); plt.close()
    with c2:
        st.subheader("Revenue by Product Category")
        cat_s = cat.sort_values('revenue')
        fig,ax = plt.subplots(figsize=(7,4)); fig.patch.set_facecolor(BG)
        ax.barh(cat_s['product_category'], cat_s['revenue'], color=ACCENT)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x,_:f'${x:,.0f}'))
        ax.set_title('Revenue by Category', fontsize=11, fontweight='bold', color=DARK)
        ax.grid(True,axis='x'); plt.tight_layout(); st.pyplot(fig); plt.close()

with tab2:
    st.subheader("Day-of-Week Performance")
    dow['day_of_week'] = pd.Categorical(dow['day_of_week'], categories=DOW_ORDER, ordered=True)
    dow_s = dow.sort_values('day_of_week')
    colors = [ACCENT if d in ['Saturday','Sunday'] else C2 for d in dow_s['day_of_week']]
    c1,c2 = st.columns(2)
    with c1:
        fig,ax = plt.subplots(figsize=(7,4.5)); fig.patch.set_facecolor(BG)
        ax.bar(dow_s['day_of_week'], dow_s['total_revenue'], color=colors, edgecolor=BG)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_:f'${x:,.0f}'))
        ax.set_title('Total Revenue by Day', fontsize=12, fontweight='bold', color=DARK)
        ax.tick_params(axis='x',rotation=30); ax.grid(True,axis='y')
        ax.legend(handles=[mpatches.Patch(color=ACCENT,label='Weekend'),mpatches.Patch(color=C2,label='Weekday')])
        plt.tight_layout(); st.pyplot(fig); plt.close()
    with c2:
        fig,ax = plt.subplots(figsize=(7,4.5)); fig.patch.set_facecolor(BG)
        ax.bar(dow_s['day_of_week'], dow_s['total_txn'], color=colors, edgecolor=BG)
        ax.set_title('Total Transactions by Day', fontsize=12, fontweight='bold', color=DARK)
        ax.tick_params(axis='x',rotation=30); ax.grid(True,axis='y')
        ax.legend(handles=[mpatches.Patch(color=ACCENT,label='Weekend'),mpatches.Patch(color=C2,label='Weekday')])
        plt.tight_layout(); st.pyplot(fig); plt.close()

with tab3:
    st.subheader("Hourly Demand Analysis")
    fig,ax1 = plt.subplots(figsize=(12,5)); fig.patch.set_facecolor(BG); ax2=ax1.twinx()
    bars = ax1.bar(hourly['hour'], hourly['transactions'], color=C2, alpha=0.75, width=0.6, label='Transactions', zorder=2)
    line, = ax2.plot(hourly['hour'], hourly['revenue'], color=ACCENT, lw=2.5, marker='o', markersize=6, label='Revenue', zorder=3)
    ax1.set_xlabel('Hour of Day'); ax1.set_ylabel('Transactions',color=C2); ax2.set_ylabel('Revenue ($)',color=ACCENT)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_:f'${x:,.0f}'))
    ax1.set_xticks(hourly['hour']); ax1.set_xticklabels([f'{h:02d}:00' for h in hourly['hour']],rotation=45)
    ax1.set_title('Hourly Transaction Volume & Revenue', fontsize=13, fontweight='bold', color=DARK)
    ax1.legend([bars,line],['Transactions','Revenue'],loc='upper right')
    ax1.grid(True,axis='y',zorder=0); plt.tight_layout(); st.pyplot(fig); plt.close()

with tab4:
    st.subheader("Revenue Heatmap: Location × Hour")
    pivot = heat_df.pivot(index='store_location', columns='hour', values='revenue').fillna(0)
    fig,ax = plt.subplots(figsize=(13,3.5)); fig.patch.set_facecolor(BG)
    sns.heatmap(pivot,ax=ax,cmap='YlOrBr',linewidths=0.3,annot=True,fmt='.0f',cbar_kws={'label':'Revenue ($)','shrink':0.8})
    ax.set_title('Revenue Heatmap: Location × Hour', fontsize=12, fontweight='bold', color=DARK)
    ax.set_xticklabels([f'{int(h):02d}:00' for h in pivot.columns],rotation=45)
    plt.tight_layout(); st.pyplot(fig); plt.close()

    c1,c2 = st.columns(2)
    with c1:
        st.subheader("Revenue Share by Location")
        fig,ax = plt.subplots(figsize=(5,4)); fig.patch.set_facecolor(BG)
        ax.pie(loc_rev['revenue'], labels=loc_rev['store_location'], autopct='%1.1f%%',
               colors=LOC_COLORS[:len(loc_rev)], startangle=90, wedgeprops={'edgecolor':BG,'linewidth':2})
        ax.set_title('Revenue Share', fontsize=11, fontweight='bold', color=DARK)
        plt.tight_layout(); st.pyplot(fig); plt.close()
    with c2:
        st.subheader("Peak Hour by Location")
        ps = ph.loc[ph.groupby('store_location')['transaction_id'].idxmax()].copy()
        ps.columns = ['Location','Hour','Transactions']
        ps['Hour'] = ps['Hour'].apply(lambda h:f'{int(h):02d}:00')
        ps['Transactions'] = ps['Transactions'].map('{:,}'.format)
        st.dataframe(ps.set_index('Location'), use_container_width=True)

st.markdown("---")
st.caption("☕ Afficionado Coffee Roasters | Sales Analytics Dashboard | 2025")
