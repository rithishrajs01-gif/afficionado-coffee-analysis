import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import warnings, os
warnings.filterwarnings('ignore')

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Afficionado Coffee Roasters — Sales Analytics",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Theme colors ─────────────────────────────────────────────────────────────
BG     = '#FDF6EC'
DARK   = '#3E2006'
ACCENT = '#6F4E37'
C2     = '#C8A97E'
C3     = '#A0522D'
LOC_COLORS = ['#6F4E37', '#C8A97E', '#A0522D']
LOCS   = ['Lower Manhattan', "Hell's Kitchen", 'Astoria']
DOW_ORDER = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
BUCKET_ORDER = ['Morning (6-11)', 'Afternoon (12-16)', 'Evening (17-21)', 'Late/Early (22-5)']

plt.rcParams.update({
    'figure.facecolor': BG, 'axes.facecolor': BG,
    'axes.edgecolor': '#C8A97E', 'axes.labelcolor': DARK,
    'xtick.color': DARK, 'ytick.color': DARK,
    'text.color': DARK, 'font.family': 'DejaVu Sans',
    'grid.color': '#E8D5B7', 'grid.linestyle': '--', 'grid.alpha': 0.5,
    'axes.spines.top': False, 'axes.spines.right': False
})

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #FDF6EC; }
    .stApp { background-color: #FDF6EC; }
    .metric-card {
        background: linear-gradient(135deg, #6F4E37, #A0522D);
        border-radius: 12px; padding: 20px 24px; color: white;
        text-align: center; box-shadow: 0 4px 12px rgba(111,78,55,0.25);
        margin-bottom: 8px;
    }
    .metric-card h2 { margin: 0; font-size: 2rem; font-weight: 700; }
    .metric-card p  { margin: 4px 0 0; font-size: 0.85rem; opacity: 0.85; }
    h1, h2, h3 { color: #3E2006 !important; }
    .sidebar .sidebar-content { background-color: #F5ECD7; }
    .stSelectbox label, .stMultiSelect label, .stSlider label { color: #3E2006 !important; font-weight: 600; }
    div[data-testid="metric-container"] { background: #F5ECD7; border-radius: 8px; padding: 12px; border-left: 4px solid #6F4E37; }
</style>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    # Try pickle first, fall back to xlsx
    pkl_path  = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed.pkl')
    xlsx_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'Afficionado_Coffee_Roasters.xlsx')
    if os.path.exists(pkl_path):
        df = pd.read_pickle(pkl_path)
    else:
        df = pd.read_excel(xlsx_path)
        df['revenue'] = df['transaction_qty'] * df['unit_price']
        df['hour']    = df['transaction_time'].apply(lambda t: t.hour)
        df = df.sort_values('transaction_id').reset_index(drop=True)
        n = len(df)
        day_nums = np.clip((np.arange(n) / (n / 182)).astype(int), 0, 181)
        df['day_num']     = day_nums
        df['date']        = pd.Timestamp('2025-01-01') + pd.to_timedelta(df['day_num'], unit='D')
        df['month']       = df['date'].dt.month
        df['month_name']  = df['date'].dt.strftime('%b')
        df['week']        = df['date'].dt.isocalendar().week.astype(int)
        df['day_of_week'] = df['date'].dt.day_name()
        df['dow_num']     = df['date'].dt.dayofweek
        def tb(h):
            if 6<=h<=11:    return 'Morning (6-11)'
            elif 12<=h<=16: return 'Afternoon (12-16)'
            elif 17<=h<=21: return 'Evening (17-21)'
            else:           return 'Late/Early (22-5)'
        df['time_bucket'] = df['hour'].apply(tb)
    return df

df_full = load_data()

# ── Sidebar Filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/emoji/96/000000/hot-beverage.png", width=60)
    st.title("☕ Filters")
    st.markdown("---")

    all_locs = df_full['store_location'].unique().tolist()
    sel_locs = st.multiselect("🏪 Store Location", options=all_locs, default=all_locs)

    dow_opts = DOW_ORDER
    sel_days = st.multiselect("📅 Day of Week", options=dow_opts, default=dow_opts)

    hour_range = st.slider("🕐 Hour Range", min_value=6, max_value=20, value=(6, 20))

    metric = st.radio("📊 Metric", options=["Revenue ($)", "Transaction Count"], index=0)

    st.markdown("---")
    st.caption("Afficionado Coffee Roasters\nSales Analytics Dashboard v1.0")

# ── Apply filters ─────────────────────────────────────────────────────────────
df = df_full.copy()
if sel_locs: df = df[df['store_location'].isin(sel_locs)]
if sel_days:  df = df[df['day_of_week'].isin(sel_days)]
df = df[(df['hour'] >= hour_range[0]) & (df['hour'] <= hour_range[1])]

metric_col   = 'revenue' if 'Revenue' in metric else 'transaction_id'
metric_label = 'Revenue ($)' if 'Revenue' in metric else 'Transaction Count'
agg_fn       = 'sum'

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# ☕ Afficionado Coffee Roasters")
st.markdown("### Sales Trend & Time-Based Performance Dashboard — 2025")
st.markdown("---")

# ── KPI Cards ─────────────────────────────────────────────────────────────────
total_rev  = df['revenue'].sum()
total_txn  = len(df)
avg_order  = df['revenue'].mean() if len(df) else 0
peak_h     = df.groupby('hour')['transaction_id'].count().idxmax() if len(df) else 0
peak_day   = df.groupby('day_of_week')['revenue'].sum().idxmax() if len(df) else 'N/A'
top_loc    = df.groupby('store_location')['revenue'].sum().idxmax() if len(df) else 'N/A'

k1, k2, k3, k4, k5, k6 = st.columns(6)
kpis = [
    (k1, f"${total_rev:,.0f}",   "Total Revenue"),
    (k2, f"{total_txn:,}",       "Transactions"),
    (k3, f"${avg_order:.2f}",    "Avg Order Value"),
    (k4, f"{peak_h}:00",         "Peak Hour"),
    (k5, peak_day,               "Busiest Day"),
    (k6, top_loc,                "Top Location"),
]
for col, val, label in kpis:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <h2>{val}</h2>
            <p>{label}</p>
        </div>""", unsafe_allow_html=True)

st.markdown("---")

# ── TAB LAYOUT ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📈 Sales Trends", "📅 Day-of-Week", "🕐 Hourly Demand", "🗺️ Location Comparison"])

# ────────────────────────────────────────────────────────────────────────────
# TAB 1: Sales Trends
# ────────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Weekly Sales Trend")
    weekly = df.groupby('week').agg(
        revenue=('revenue','sum'),
        transactions=('transaction_id','count')
    ).reset_index()
    y_col = 'revenue' if 'Revenue' in metric else 'transactions'

    fig, ax = plt.subplots(figsize=(12, 4.5))
    fig.patch.set_facecolor(BG)
    ax.plot(weekly['week'], weekly[y_col], color=ACCENT, lw=2.5, marker='o', markersize=4)
    ax.fill_between(weekly['week'], weekly[y_col], alpha=0.12, color=ACCENT)
    if len(weekly) > 1:
        z = np.polyfit(weekly['week'], weekly[y_col], 1)
        ax.plot(weekly['week'], np.poly1d(z)(weekly['week']), '--', color=C3, lw=1.5, alpha=0.7, label='Trend')
        ax.legend(fontsize=10)
    if 'Revenue' in metric:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f'${x:,.0f}'))
    ax.set_xlabel('Week of Year', fontsize=11); ax.set_ylabel(metric_label, fontsize=11)
    ax.set_title('Weekly Revenue Trend (Jan – Jul 2025)', fontsize=13, fontweight='bold', color=DARK)
    ax.grid(True, axis='y')
    plt.tight_layout()
    st.pyplot(fig); plt.close()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Monthly Revenue by Location")
        monthly_loc = df.groupby(['month','month_name','store_location'])['revenue'].sum().reset_index()
        fig, ax = plt.subplots(figsize=(7, 4))
        fig.patch.set_facecolor(BG)
        for loc, color in zip(sel_locs or LOCS, LOC_COLORS[:len(sel_locs or LOCS)]):
            d = monthly_loc[monthly_loc['store_location']==loc].sort_values('month')
            ax.plot(d['month'], d['revenue'], marker='o', label=loc, color=color, lw=2, markersize=5)
        ax.set_xticks(sorted(monthly_loc['month'].unique()))
        ax.set_xticklabels(['Jan','Feb','Mar','Apr','May','Jun','Jul'][:len(monthly_loc['month'].unique())])
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f'${x:,.0f}'))
        ax.set_title('Monthly Revenue by Location', fontsize=11, fontweight='bold', color=DARK)
        ax.legend(fontsize=9); ax.grid(True, axis='y')
        plt.tight_layout(); st.pyplot(fig); plt.close()

    with col2:
        st.subheader("Revenue by Product Category")
        cat_rev = df.groupby('product_category')['revenue'].sum().sort_values(ascending=True)
        fig, ax = plt.subplots(figsize=(7, 4))
        fig.patch.set_facecolor(BG)
        bars = ax.barh(cat_rev.index, cat_rev.values, color=ACCENT, edgecolor=BG)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f'${x:,.0f}'))
        ax.set_title('Revenue by Product Category', fontsize=11, fontweight='bold', color=DARK)
        ax.grid(True, axis='x')
        plt.tight_layout(); st.pyplot(fig); plt.close()

# ────────────────────────────────────────────────────────────────────────────
# TAB 2: Day-of-Week
# ────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Day-of-Week Performance")
    dow = df.groupby('day_of_week').agg(
        avg_revenue=('revenue','mean'),
        total_revenue=('revenue','sum'),
        total_txn=('transaction_id','count')
    ).reset_index()
    dow['day_of_week'] = pd.Categorical(dow['day_of_week'], categories=DOW_ORDER, ordered=True)
    dow = dow.sort_values('day_of_week')

    colors = [ACCENT if d in ['Saturday','Sunday'] else C2 for d in dow['day_of_week']]
    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        fig.patch.set_facecolor(BG)
        ax.bar(dow['day_of_week'], dow['total_revenue'], color=colors, edgecolor=BG)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f'${x:,.0f}'))
        ax.set_title('Total Revenue by Day', fontsize=12, fontweight='bold', color=DARK)
        ax.tick_params(axis='x', rotation=30)
        ax.grid(True, axis='y')
        patches = [mpatches.Patch(color=ACCENT, label='Weekend'), mpatches.Patch(color=C2, label='Weekday')]
        ax.legend(handles=patches, fontsize=9)
        plt.tight_layout(); st.pyplot(fig); plt.close()

    with col2:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        fig.patch.set_facecolor(BG)
        ax.bar(dow['day_of_week'], dow['total_txn'], color=colors, edgecolor=BG)
        ax.set_title('Total Transactions by Day', fontsize=12, fontweight='bold', color=DARK)
        ax.tick_params(axis='x', rotation=30)
        ax.grid(True, axis='y')
        patches = [mpatches.Patch(color=ACCENT, label='Weekend'), mpatches.Patch(color=C2, label='Weekday')]
        ax.legend(handles=patches, fontsize=9)
        plt.tight_layout(); st.pyplot(fig); plt.close()

    st.subheader("📌 Weekday vs Weekend Summary")
    df['is_weekend'] = df['day_of_week'].isin(['Saturday','Sunday'])
    wk_comp = df.groupby('is_weekend').agg(
        avg_rev=('revenue','mean'),
        total_rev=('revenue','sum'),
        txn_count=('transaction_id','count')
    ).reset_index()
    wk_comp['Period'] = wk_comp['is_weekend'].map({True:'Weekend', False:'Weekday'})
    wk_comp = wk_comp.drop(columns='is_weekend').set_index('Period')
    wk_comp.columns = ['Avg Revenue ($)', 'Total Revenue ($)', 'Transactions']
    wk_comp['Avg Revenue ($)'] = wk_comp['Avg Revenue ($)'].map('${:.2f}'.format)
    wk_comp['Total Revenue ($)'] = wk_comp['Total Revenue ($)'].map('${:,.0f}'.format)
    wk_comp['Transactions'] = wk_comp['Transactions'].map('{:,}'.format)
    st.dataframe(wk_comp, use_container_width=True)

# ────────────────────────────────────────────────────────────────────────────
# TAB 3: Hourly Demand
# ────────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Hourly Demand Analysis")
    hourly = df.groupby('hour').agg(
        transactions=('transaction_id','count'),
        revenue=('revenue','sum')
    ).reset_index()

    fig, ax1 = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor(BG)
    ax2 = ax1.twinx()
    bars = ax1.bar(hourly['hour'], hourly['transactions'], color=C2, alpha=0.75, label='Transactions', zorder=2, width=0.6)
    line, = ax2.plot(hourly['hour'], hourly['revenue'], color=ACCENT, lw=2.5, marker='o', markersize=6, label='Revenue', zorder=3)
    ax1.set_xlabel('Hour of Day (24h)', fontsize=11)
    ax1.set_ylabel('Transaction Count', fontsize=11, color=C2)
    ax2.set_ylabel('Revenue ($)', fontsize=11, color=ACCENT)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f'${x:,.0f}'))
    ax1.set_xticks(hourly['hour'])
    ax1.set_xticklabels([f'{h:02d}:00' for h in hourly['hour']], rotation=45)
    ax1.set_title('Hourly Transaction Volume & Revenue', fontsize=13, fontweight='bold', color=DARK)
    ax1.legend([bars, line], ['Transactions','Revenue'], loc='upper right', fontsize=10)
    ax1.grid(True, axis='y', zorder=0)
    plt.tight_layout(); st.pyplot(fig); plt.close()

    st.subheader("Time Bucket Distribution")
    bucket = df.groupby(['store_location','time_bucket'])['revenue'].sum().reset_index()
    bucket['time_bucket'] = pd.Categorical(bucket['time_bucket'], categories=BUCKET_ORDER, ordered=True)
    bucket = bucket.sort_values(['store_location','time_bucket'])

    fig, ax = plt.subplots(figsize=(11, 4.5))
    fig.patch.set_facecolor(BG)
    width = 0.22
    x = np.arange(len(BUCKET_ORDER))
    avail_locs = sel_locs if sel_locs else LOCS
    for i, (loc, color) in enumerate(zip(avail_locs, LOC_COLORS)):
        vals = bucket[bucket['store_location']==loc].set_index('time_bucket')['revenue'].reindex(BUCKET_ORDER, fill_value=0)
        ax.bar(x + i*width - width, vals, width, label=loc, color=color, edgecolor=BG)
    ax.set_xticks(x - width/2)
    ax.set_xticklabels(BUCKET_ORDER, fontsize=10)
    ax.set_title('Revenue by Time Bucket & Store Location', fontsize=13, fontweight='bold', color=DARK)
    ax.set_ylabel('Total Revenue ($)', fontsize=11)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f'${x:,.0f}'))
    ax.legend(title='Store Location', fontsize=10); ax.grid(True, axis='y')
    plt.tight_layout(); st.pyplot(fig); plt.close()

# ────────────────────────────────────────────────────────────────────────────
# TAB 4: Location Comparison
# ────────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Cross-Location Temporal Analysis")

    # Revenue Heatmap
    pivot = df.groupby(['store_location','hour'])['revenue'].sum().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(13, 3.5))
    fig.patch.set_facecolor(BG)
    sns.heatmap(pivot, ax=ax, cmap='YlOrBr', linewidths=0.3, linecolor=BG,
                annot=True, fmt='.0f',
                cbar_kws={'label': 'Revenue ($)', 'shrink': 0.8})
    ax.set_title('Revenue Heatmap: Location × Hour of Day', fontsize=12, fontweight='bold', color=DARK)
    ax.set_xlabel('Hour of Day'); ax.set_ylabel('')
    hrs = sorted(df['hour'].unique())
    ax.set_xticklabels([f'{h:02d}:00' for h in hrs], rotation=45)
    plt.tight_layout(); st.pyplot(fig); plt.close()

    col1, col2 = st.columns(2)
    with col1:
        # Peak hour per location
        st.subheader("Peak Hour by Location")
        peak_loc = df.groupby(['store_location','hour'])['transaction_id'].count().reset_index()
        peak_loc.columns = ['Location','Hour','Transactions']
        peak_idx = peak_loc.groupby('Location')['Transactions'].idxmax()
        peak_summary = peak_loc.loc[peak_idx][['Location','Hour','Transactions']]
        peak_summary['Hour'] = peak_summary['Hour'].apply(lambda h: f'{h:02d}:00')
        peak_summary['Transactions'] = peak_summary['Transactions'].map('{:,}'.format)
        st.dataframe(peak_summary.set_index('Location'), use_container_width=True)

    with col2:
        # Revenue share pie
        st.subheader("Revenue Share by Location")
        loc_rev = df.groupby('store_location')['revenue'].sum()
        fig, ax = plt.subplots(figsize=(5, 4))
        fig.patch.set_facecolor(BG)
        wedges, texts, autotexts = ax.pie(
            loc_rev.values,
            labels=loc_rev.index,
            autopct='%1.1f%%',
            colors=LOC_COLORS[:len(loc_rev)],
            startangle=90,
            wedgeprops={'edgecolor': BG, 'linewidth': 2}
        )
        for t in autotexts: t.set_color('white'); t.set_fontweight('bold')
        ax.set_title('Revenue Share', fontsize=11, fontweight='bold', color=DARK)
        plt.tight_layout(); st.pyplot(fig); plt.close()

    # DOW heatmap per location
    st.subheader("Revenue Heatmap: Location × Day of Week")
    pivot2 = df.groupby(['store_location','day_of_week'])['revenue'].sum().unstack(fill_value=0)
    pivot2 = pivot2.reindex(columns=[d for d in DOW_ORDER if d in pivot2.columns])
    fig, ax = plt.subplots(figsize=(11, 3))
    fig.patch.set_facecolor(BG)
    sns.heatmap(pivot2, ax=ax, cmap='YlOrBr', linewidths=0.3, linecolor=BG,
                annot=True, fmt='.0f', cbar_kws={'label': 'Revenue ($)', 'shrink': 0.8})
    ax.set_title('Revenue by Location × Day of Week', fontsize=12, fontweight='bold', color=DARK)
    ax.set_xlabel('Day of Week'); ax.set_ylabel('')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=30)
    plt.tight_layout(); st.pyplot(fig); plt.close()

st.markdown("---")
st.caption("☕ Afficionado Coffee Roasters | Sales Analytics Dashboard | Data: Jan–Jul 2025 | Built with Streamlit")
