import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Fourth Partner Energy", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
.stApp,.main{background-color:#080d18!important;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0c1220 0%,#0a101e 100%)!important;border-right:1px solid #1c2a42!important;}
.top-bar{background:linear-gradient(90deg,#0c1628,#112040,#0c1628);border-bottom:2px solid #f59e0b;padding:14px 24px;margin:-1rem -1rem 1.5rem -1rem;display:flex;align-items:center;gap:16px;}
.top-bar-logo{width:38px;height:38px;background:#f59e0b;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:900;color:#000;font-family:'Syne',sans-serif;}
.top-bar-title{font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;color:#fff;letter-spacing:-0.3px;}
.top-bar-sub{font-size:0.72rem;color:#3a4e6a;letter-spacing:2px;text-transform:uppercase;}
.top-bar-page{margin-left:auto;font-family:'Syne',sans-serif;font-size:0.78rem;font-weight:700;color:#f59e0b;letter-spacing:2.5px;text-transform:uppercase;}
.sec{font-family:'Syne',sans-serif;font-size:0.72rem;font-weight:700;color:#3a5070;text-transform:uppercase;letter-spacing:2.5px;border-left:3px solid #f59e0b;padding-left:10px;margin:18px 0 10px 0;}
div[data-testid="metric-container"]{background:linear-gradient(145deg,#0f1a2e,#142040)!important;border:1px solid #1c2e4a!important;border-top:3px solid #f59e0b!important;border-radius:10px!important;padding:12px 14px!important;}
div[data-testid="metric-container"] label{font-size:0.65rem!important;color:#3a5070!important;text-transform:uppercase!important;letter-spacing:1.5px!important;}
div[data-testid="metric-container"] [data-testid="stMetricValue"]{font-family:'Syne',sans-serif!important;font-size:1.45rem!important;color:#fff!important;font-weight:700!important;}
.stTabs [data-baseweb="tab-list"]{background:#0a101e!important;border-radius:8px!important;padding:4px!important;}
.stTabs [data-baseweb="tab"]{font-family:'Syne',sans-serif!important;font-size:0.76rem!important;color:#3a5070!important;font-weight:700!important;border-radius:6px!important;}
.stTabs [aria-selected="true"]{background:#142040!important;color:#f59e0b!important;border-bottom:2px solid #f59e0b!important;}
.stSelectbox>div>div,.stMultiSelect>div>div{background:#0f1a2e!important;border-color:#1c2e4a!important;color:#8a9bbf!important;}
.stSelectbox label,.stMultiSelect label,.stNumberInput label,.stSlider label{font-size:0.68rem!important;color:#3a5070!important;text-transform:uppercase!important;letter-spacing:1px!important;}
.upload-box{background:linear-gradient(145deg,#0c1220,#0f1a2e);border:2px dashed #1c2e4a;border-radius:14px;padding:3rem 2rem;text-align:center;}
.spv-tag{display:inline-block;background:#0f1a2e;border:1px solid #1c2e4a;border-radius:20px;padding:3px 12px;font-size:0.7rem;color:#3a5070;margin:2px;font-weight:500;}
</style>
""", unsafe_allow_html=True)

COLORS = ["#f59e0b","#3b82f6","#22c55e","#ef4444","#a78bfa","#38bdf8","#fb923c","#34d399","#f472b6","#facc15","#e879f9","#4ade80"]
def apply_layout(fig, height=300, legend_h=False, barmode=None, showlegend=True, coloraxis=False):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(10,16,30,0.5)",
        font=dict(color="#6a7e9c", family="DM Sans", size=11),
        margin=dict(t=30,b=30,l=10,r=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10),
                    orientation="h" if legend_h else "v",
                    y=1.05 if legend_h else 1),
        height=height,
        showlegend=showlegend,
        xaxis=dict(gridcolor="#14213a", linecolor="#14213a"),
        yaxis=dict(gridcolor="#14213a", linecolor="#14213a"),
    )
    if barmode:
        fig.update_layout(barmode=barmode)
    if coloraxis:
        fig.update_layout(coloraxis_showscale=False)
    return fig

@st.cache_data
def find_mis_sheet(xl):
    for s in xl.sheet_names:
        su = s.upper().replace(' ','')
        if 'MIS' in su and 'ERP' in su:
            return s
    for s in xl.sheet_names:
        if 'MIS' in s.upper():
            return s
    return xl.sheet_names[0]

@st.cache_data
def find_col(df, keywords_list):
    """Find column by trying multiple keyword combos"""
    for keywords in keywords_list:
        for col in df.columns:
            cl = col.lower().replace('\n',' ')
            if all(k.lower() in cl for k in keywords):
                return col
    return None

@st.cache_data
def load_all(file):
    xl = pd.ExcelFile(file)

    # ── Find MIS sheet ──
    mis_sheet = find_mis_sheet(xl)

    # ── Find header row ──
    raw = pd.read_excel(file, sheet_name=mis_sheet, header=None)
    header_row = 0
    for i in range(10):
        row_vals = [str(v).strip().lower() for v in raw.iloc[i,:].tolist()]
        if 'company' in row_vals and any('billed' in v for v in row_vals):
            header_row = i
            break

    df = pd.read_excel(file, sheet_name=mis_sheet, header=header_row)
    df.columns = [str(c).strip().replace('\n',' ') for c in df.columns]

    # ── Smart column mapping ──
    spv_col    = find_col(df, [['company name']]) or find_col(df, [['spv identification']]) or find_col(df, [['spv']])
    month_col  = find_col(df, [['invoice month2']]) or find_col(df, [['month2']])
    units_col  = find_col(df, [['billed units']])
    yield_col  = find_col(df, [['yield']])
    billed_col = find_col(df, [['billed amount']])
    real_col   = find_col(df, [['realized amount']])
    bal_col    = find_col(df, [['balance amount']]) or find_col(df, [['balance']])
    cap_col    = find_col(df, [['plant capacity']])
    oft_col    = find_col(df, [['offtaker name']]) or find_col(df, [['offtaker']]) or find_col(df, [['customer name']])

    # ── Build clean MIS dataframe ──
    mis = pd.DataFrame()
    mis['SPV']             = df[spv_col].astype(str) if spv_col else 'Unknown'
    mis['Invoice_Month2']  = pd.to_datetime(df[month_col], errors='coerce') if month_col else pd.NaT
    mis['Billed_Units']    = pd.to_numeric(df[units_col], errors='coerce') if units_col else 0
    mis['Yield']           = pd.to_numeric(df[yield_col], errors='coerce') if yield_col else 0
    mis['Billed_Amount']   = pd.to_numeric(df[billed_col], errors='coerce') if billed_col else 0
    mis['Realized_Amount'] = pd.to_numeric(df[real_col], errors='coerce') if real_col else 0
    mis['Balance_Amount']  = pd.to_numeric(df[bal_col], errors='coerce') if bal_col else 0
    mis['Plant_Capacity']  = pd.to_numeric(df[cap_col], errors='coerce') if cap_col else 0
    mis['Offtaker']        = df[oft_col].astype(str) if oft_col else ''

    # ── Clean rows ──
    mis = mis[mis['SPV'].str.len() > 3]
    mis = mis[~mis['SPV'].str.contains('Company|SPV Ident|company name|identification', case=False, na=False)]
    mis = mis.dropna(subset=['Invoice_Month2'])
    mis = mis[mis['Billed_Units'].notna() & (mis['Billed_Units'] > 0)].copy()

    # ── Derived columns ──
    mis['PLF'] = (mis['Yield'] / 24 * 100).clip(0, 40)
    mis['Days'] = mis['Invoice_Month2'].dt.days_in_month.fillna(30)

    def fy(dt):
        if pd.isnull(dt): return None
        return f'FY {dt.year}-{str(dt.year+1)[-2:]}' if dt.month >= 4 else f'FY {dt.year-1}-{str(dt.year)[-2:]}'
    mis['FY'] = mis['Invoice_Month2'].apply(fy)

    # ── Portfolio Details ──
    port = pd.DataFrame({'SPV':[], 'DC_Capacity_KWp':[], 'Region':[], 'State':[],
                         'Tariff':[], 'Rating_Category':[], 'COD':[], 'Balance_PPA_Tenor':[]})

    if 'Portfolio Details' in xl.sheet_names:
        try:
            pr = pd.read_excel(file, sheet_name='Portfolio Details', header=None)
            # Find header row
            ph = 0
            for i in range(10):
                rv = [str(v).strip().lower() for v in pr.iloc[i,:].tolist()]
                if 'spv' in rv and any('capacity' in v for v in rv):
                    ph = i; break
            port_raw = pd.read_excel(file, sheet_name='Portfolio Details', header=ph)
            port_raw.columns = [str(c).strip().replace('\n',' ') for c in port_raw.columns]

            p_spv  = find_col(port_raw, [['spv']]) or find_col(port_raw, [['generation mis sheet']])
            p_cap  = find_col(port_raw, [['dc','capacity']]) or find_col(port_raw, [['capacity']])
            p_reg  = find_col(port_raw, [['region']])
            p_st   = find_col(port_raw, [['state']])
            p_tar  = find_col(port_raw, [['tariff']])
            p_rat  = find_col(port_raw, [['rating category']]) or find_col(port_raw, [['rating']])
            p_cod  = find_col(port_raw, [['cod']])
            p_ten  = find_col(port_raw, [['balance ppa']]) or find_col(port_raw, [['balance']])

            port = pd.DataFrame()
            port['SPV']              = port_raw[p_spv].astype(str) if p_spv else ''
            port['DC_Capacity_KWp']  = pd.to_numeric(port_raw[p_cap], errors='coerce') if p_cap else 0
            port['Region']           = port_raw[p_reg] if p_reg else ''
            port['State']            = port_raw[p_st] if p_st else ''
            port['Tariff']           = pd.to_numeric(port_raw[p_tar], errors='coerce') if p_tar else 0
            port['Rating_Category']  = port_raw[p_rat] if p_rat else ''
            port['COD']              = pd.to_datetime(port_raw[p_cod], errors='coerce') if p_cod else pd.NaT
            port['Balance_PPA_Tenor']= pd.to_numeric(port_raw[p_ten], errors='coerce') if p_ten else 0

            port = port[port['SPV'].str.len() > 3]
            port = port[~port['SPV'].str.contains('SPV|Generation MIS|nan', case=False, na=False)]
            port = port.dropna(subset=['DC_Capacity_KWp'])
            port = port[port['DC_Capacity_KWp'] > 0]
        except Exception as e:
            st.warning(f"Portfolio Details sheet could not be fully loaded: {e}")

    return mis, port


# ── SIDEBAR ──
with st.sidebar:
    st.markdown("<div style='text-align:center;padding:1rem 0 0.5rem;'><div style='font-family:Syne,sans-serif;font-size:1rem;font-weight:800;color:#f59e0b;'>⚡ Fourth Partner Energy</div><div style='font-size:0.65rem;color:#1c2e4a;letter-spacing:2px;text-transform:uppercase;margin-top:2px;'>Portfolio Intelligence</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div style='font-size:0.65rem;color:#2a3a52;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>📁 Upload Excel</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=["xlsx","xls"], label_visibility="collapsed")
    if uploaded_file:
        st.markdown(f"<div style='background:#081a0e;border:1px solid #22c55e;border-radius:6px;padding:6px 10px;margin-top:4px;font-size:0.72rem;color:#22c55e;'>✓ {uploaded_file.name}</div>", unsafe_allow_html=True)
        st.markdown("---")
        page = st.radio("", ["Portfolio Details","BaseCase PLF","Portfolio Dashboard","SPV Dashboard"], label_visibility="collapsed")
    else:
        page = "Portfolio Dashboard"
    st.markdown("---")
    st.markdown("<div style='font-size:0.62rem;color:#14213a;text-align:center;'>Fourth Partner Energy India<br>Automation · v2.0</div>", unsafe_allow_html=True)

# ── HEADER ──
pages_map = {"Portfolio Details":"PORTFOLIO DETAILS","BaseCase PLF":"BASECASE PLF","Portfolio Dashboard":"PORTFOLIO DASHBOARD","SPV Dashboard":"SPV DASHBOARD"}
st.markdown(f"""
<div class='top-bar'>
  <div class='top-bar-logo'>FP</div>
  <div>
    <div class='top-bar-title'>Fourth Partner Energy</div>
    <div class='top-bar-sub'>All SPV Dashboard</div>
  </div>
  <div class='top-bar-page'>{pages_map.get(page,'')}</div>
</div>
""", unsafe_allow_html=True)

if not uploaded_file:
    st.markdown("""<div class='upload-box'>
    <div style='font-size:3rem;margin-bottom:1rem;'>⚡</div>
    <div style='font-family:Syne,sans-serif;font-size:1.4rem;font-weight:700;color:#c8d6f0;'>Upload Your SPV Excel File</div>
    <div style='color:#2a3a52;font-size:0.85rem;margin-top:6px;'>Use the sidebar uploader → then navigate the pages</div>
    <div style='margin-top:1.2rem;'>
      <span class='spv-tag' style='border-color:#f59e0b;color:#f59e0b;'>Portfolio Details</span>
      <span class='spv-tag'>MIS-ERP</span><span class='spv-tag'>PLF Data</span><span class='spv-tag'>Billed Units</span>
    </div></div>""", unsafe_allow_html=True)
    st.stop()

with st.spinner("Loading..."):
    mis, port = load_all(uploaded_file)

ALL_FY   = sorted(mis['FY'].dropna().unique())
CUR_FY   = ALL_FY[-1]
ALL_SPVS = sorted(mis['SPV'].dropna().unique())

def fy_filter(df, sel):
    return df if sel=="All" else df[df['FY']==sel]

def get_ttm(df):
    mx = df['Invoice_Month2'].max()
    return df[df['Invoice_Month2'] > mx - pd.DateOffset(months=12)]

def quarterly_plf(df):
    def gq(r):
        if pd.isnull(r['Invoice_Month2']): return None,None
        m=r['Invoice_Month2'].month
        if m>=4: fy_yr=r['Invoice_Month2'].year; q=(m-4)//3+1
        else: fy_yr=r['Invoice_Month2'].year-1; q=(m+8)//3
        return f'FY {fy_yr}-{str(fy_yr+1)[-2:]}',f'Q{q}'
    d=df.copy()
    d[['FY_Q','Q']]=d.apply(lambda r:pd.Series(gq(r)),axis=1)
    qp=d.groupby(['FY_Q','Q'])['PLF'].mean().reset_index().sort_values(['FY_Q','Q'])
    last2=sorted(qp['FY_Q'].unique())[-2:]
    qc=qp[qp['FY_Q']==last2[-1]] if len(last2)>0 else pd.DataFrame()
    qp2=qp[qp['FY_Q']==last2[-2]] if len(last2)>1 else pd.DataFrame()
    return qc, qp2

# ══════════════════════════════════════════════════════════════
# PAGE 1 — PORTFOLIO DASHBOARD
# ══════════════════════════════════════════════════════════════
if page == "Portfolio Dashboard":
    _, fc = st.columns([3,1])
    with fc:
        sel_fy = st.selectbox("Financial Year", ["All"]+ALL_FY, index=ALL_FY.index(CUR_FY)+1, key="pfy")

    df = mis.copy()
    ttm  = get_ttm(df)
    df_fy = fy_filter(df, sel_fy)
    overall = df.copy()

    # TTM
    st.markdown("<div class='sec'>TTM Performance</div>", unsafe_allow_html=True)
    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("TTM Billed Units",   f"{ttm['Billed_Units'].sum()/1e6:.2f}M")
    k2.metric("TTM Weighted PLF",   f"{ttm['PLF'].mean():.2f}%")
    k3.metric("TTM Billed Amount",  f"₹{ttm['Billed_Amount'].sum()/1e7:.2f}Cr")
    k4.metric("TTM Receivables",    f"₹{ttm['Balance_Amount'].sum()/1e7:.2f}Cr")
    k5.metric("TTM Realized",       f"₹{ttm['Realized_Amount'].sum()/1e7:.2f}Cr")

    # Current FY (reacts to slicer)
    st.markdown("<div class='sec'>Current Financial Year</div>", unsafe_allow_html=True)
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("FY Billed Units",   f"{df_fy['Billed_Units'].sum()/1e6:.2f}M")
    k2.metric("FY Weighted PLF",   f"{df_fy['PLF'].mean():.2f}%")
    k3.metric("FY Billed Amount",  f"₹{df_fy['Billed_Amount'].sum()/1e7:.2f}Cr")
    k4.metric("FY Receivables",    f"₹{df_fy['Balance_Amount'].sum()/1e7:.2f}Cr")

    # Overall
    st.markdown("<div class='sec'>Overall Performance</div>", unsafe_allow_html=True)
    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("Overall Billed Units", f"{overall['Billed_Units'].sum()/1e6:.2f}M")
    k2.metric("Overall PLF",          f"{overall['PLF'].mean():.2f}%")
    k3.metric("Overall Billed Amt",   f"₹{overall['Billed_Amount'].sum()/1e7:.2f}Cr")
    k4.metric("Overall Receivables",  f"₹{overall['Balance_Amount'].sum()/1e7:.2f}Cr")
    k5.metric("Total Realized",       f"₹{overall['Realized_Amount'].sum()/1e7:.2f}Cr")

    st.markdown("---")
    c1,c2 = st.columns(2)

    with c1:
        st.markdown("<div class='sec'>Billed Units — YoY Comparison (Year-Month)</div>", unsafe_allow_html=True)
        m = df.groupby('Invoice_Month2')['Billed_Units'].sum().reset_index().sort_values('Invoice_Month2')
        m = m[m['Invoice_Month2'].dt.year>=2023]
        m['Lbl'] = m['Invoice_Month2'].dt.strftime('%b %Y')
        m['Prev'] = m['Billed_Units'].shift(12)
        fig=go.Figure()
        fig.add_trace(go.Bar(x=m['Lbl'],y=m['Billed_Units']/1e6,name='Billed Units',marker_color='#3b82f6',opacity=0.85))
        fig.add_trace(go.Scatter(x=m['Lbl'],y=m['Prev']/1e6,name='Prev Year',line=dict(color='#f59e0b',width=2),mode='lines+markers',marker=dict(size=4)))
        apply_layout(fig, height=290, legend_h=True)
        fig.update_yaxes(title_text="Million Units")
        st.plotly_chart(fig,use_container_width=True)

    with c2:
        st.markdown("<div class='sec'>PLF — YoY Comparison (Year-Month)</div>", unsafe_allow_html=True)
        p = df.groupby('Invoice_Month2')['PLF'].mean().reset_index().sort_values('Invoice_Month2')
        p = p[p['Invoice_Month2'].dt.year>=2023]
        p['Lbl'] = p['Invoice_Month2'].dt.strftime('%b %Y')
        p['Prev'] = p['PLF'].shift(12)
        fig2=go.Figure()
        fig2.add_trace(go.Bar(x=p['Lbl'],y=p['PLF'],name='PLF %',marker_color='#22c55e',opacity=0.85))
        fig2.add_trace(go.Scatter(x=p['Lbl'],y=p['Prev'],name='Prev Year PLF',line=dict(color='#f59e0b',width=2),mode='lines+markers',marker=dict(size=4)))
        apply_layout(fig2, height=290, legend_h=True)
        fig2.update_yaxes(title_text="PLF %")
        st.plotly_chart(fig2,use_container_width=True)

    c3,c4 = st.columns(2)

    with c3:
        st.markdown("<div class='sec'>Last 3 Years — Financial Comparison</div>", unsafe_allow_html=True)
        fy3 = df.groupby('FY').agg(Billed=('Billed_Amount','sum'),Realized=('Realized_Amount','sum'),Recv=('Balance_Amount','sum')).reset_index().sort_values('FY').tail(3)
        fig3=go.Figure()
        fig3.add_trace(go.Bar(x=fy3['FY'],y=fy3['Billed']/1e7,name='Total Billed',marker_color='#3b82f6'))
        fig3.add_trace(go.Bar(x=fy3['FY'],y=fy3['Realized']/1e7,name='Total Realized',marker_color='#22c55e'))
        fig3.add_trace(go.Bar(x=fy3['FY'],y=fy3['Recv']/1e7,name='Receivables',marker_color='#ef4444'))
        apply_layout(fig3, height=280, legend_h=True, barmode="group")
        fig3.update_yaxes(title_text="₹ Crore")
        st.plotly_chart(fig3,use_container_width=True)

    with c4:
        st.markdown("<div class='sec'>Calculated PLF and Previous Year PLF by Quarter</div>", unsafe_allow_html=True)
        qc,qp = quarterly_plf(df)
        fig4=go.Figure()
        if not qc.empty: fig4.add_trace(go.Bar(x=qc['Q'],y=qc['PLF'],name='Current PLF',marker_color='#3b82f6'))
        if not qp.empty: fig4.add_trace(go.Scatter(x=qp['Q'],y=qp['PLF'],name='Prev Year PLF',line=dict(color='#f59e0b',width=2.5),mode='lines+markers',marker=dict(size=6)))
        apply_layout(fig4, height=280, legend_h=True)
        fig4.update_yaxes(title_text="PLF %")
        st.plotly_chart(fig4,use_container_width=True)


    # ── CSV Download ──
    st.markdown("---")
    st.markdown("<div class='sec'>Download Data</div>", unsafe_allow_html=True)
    dl1, dl2, dl3 = st.columns(3)
    with dl1:
        csv1 = df_fy.groupby('FY').agg(
            Billed_Units=('Billed_Units','sum'),
            PLF=('PLF','mean'),
            Billed_Amount=('Billed_Amount','sum'),
            Realized_Amount=('Realized_Amount','sum'),
            Balance_Amount=('Balance_Amount','sum')
        ).reset_index().round(2)
        st.download_button("⬇️ FY Summary CSV", csv1.to_csv(index=False).encode('utf-8'), "fy_summary.csv", "text/csv", use_container_width=True)
    with dl2:
        csv2 = df.groupby(['FY','Invoice_Month2']).agg(
            Billed_Units=('Billed_Units','sum'),
            PLF=('PLF','mean'),
            Billed_Amount=('Billed_Amount','sum')
        ).reset_index().round(2)
        csv2['Invoice_Month2'] = csv2['Invoice_Month2'].dt.strftime('%b-%Y')
        st.download_button("⬇️ Monthly Data CSV", csv2.to_csv(index=False).encode('utf-8'), "monthly_data.csv", "text/csv", use_container_width=True)
    with dl3:
        csv3 = df.groupby('SPV').agg(
            Billed_Units=('Billed_Units','sum'),
            PLF=('PLF','mean'),
            Billed_Amount=('Billed_Amount','sum'),
            Realized_Amount=('Realized_Amount','sum'),
            Balance_Amount=('Balance_Amount','sum')
        ).reset_index().round(2)
        st.download_button("⬇️ SPV Summary CSV", csv3.to_csv(index=False).encode('utf-8'), "spv_summary.csv", "text/csv", use_container_width=True)

# ══════════════════════════════════════════════════════════════
# PAGE 2 — BASECASE PLF
# ══════════════════════════════════════════════════════════════
elif page == "BaseCase PLF":

    cf1,cf2 = st.columns([2,2])
    with cf1:
        spv_sel = st.selectbox("SPV Filter", ["All SPVs"]+ALL_SPVS, key="bcspv")
    with cf2:
        fy_sel  = st.selectbox("Financial Year", ["All"]+ALL_FY, index=len(ALL_FY), key="bcfy")

    st.markdown("<div class='sec'>Degradation Parameters</div>", unsafe_allow_html=True)
    pc1,pc2,pc3,pc4,pc5 = st.columns(5)
    with pc1: base_plf = st.number_input("Base PLF (%)", 5.0, 30.0, 15.0, 0.1, key="bplf")
    with pc2: deg1     = st.number_input("Degradation 1 (%/yr)", 0.0, 5.0, 0.5, 0.05, key="d1")
    with pc3: deg1_yrs = st.number_input("Deg 1 Years", 1, 25, 10, 1, key="d1y")
    with pc4: deg2     = st.number_input("Degradation 2 (%/yr)", 0.0, 5.0, 0.3, 0.05, key="d2")
    with pc5: deg2_yrs = st.number_input("Deg 2 Years", 1, 25, 3, 1, key="d2y")

    # Projected curve
    total_yrs = int(deg1_yrs + deg2_yrs)
    proj_years = list(range(2022, 2022+total_yrs+1))
    proj_plf_vals=[]; cp=base_plf
    for i in range(len(proj_years)):
        if i==0: proj_plf_vals.append(cp)
        elif i<=deg1_yrs: cp=cp*(1-deg1/100); proj_plf_vals.append(cp)
        else: cp=cp*(1-deg2/100); proj_plf_vals.append(cp)
    proj_df = pd.DataFrame({'Year':proj_years,'Projected_PLF':proj_plf_vals})
    proj_df['FY'] = proj_df['Year'].apply(lambda y: f'FY {y}-{str(y+1)[-2:]}')

    # Actual PLF
    df_bc = mis.copy()
    if spv_sel!="All SPVs": df_bc=df_bc[df_bc['SPV']==spv_sel]
    df_bc_filt = fy_filter(df_bc, fy_sel)
    actual_fy = df_bc.groupby('FY')['PLF'].mean().reset_index()

    variance = actual_fy['PLF'].mean()-base_plf if not actual_fy.empty else 0
    var_pct   = (variance/base_plf*100) if base_plf>0 else 0

    # Variance KPI
    k1,k2,k3 = st.columns(3)
    k1.metric("Actual Avg PLF", f"{actual_fy['PLF'].mean():.2f}%" if not actual_fy.empty else "N/A")
    k2.metric("Base PLF", f"{base_plf:.2f}%")
    k3.metric("PLF Variance", f"{var_pct:.2f}%", delta=f"{variance:.2f}% vs Base", delta_color="normal" if var_pct>=0 else "inverse")

    st.markdown("---")

    # Main chart
    st.markdown("<div class='sec'>Actual PLF (SPV BaseCase) and Projected PLF by Financial Year</div>", unsafe_allow_html=True)
    fig_bc=go.Figure()
    fig_bc.add_trace(go.Scatter(x=proj_df['FY'],y=proj_df['Projected_PLF'],name='Projected PLF',
        mode='lines+markers',line=dict(color='#1e3060',width=2,dash='dash'),
        marker=dict(size=5,color='#1e3060'),fill='tozeroy',fillcolor='rgba(30,48,96,0.12)'))
    if not actual_fy.empty:
        fig_bc.add_trace(go.Scatter(x=actual_fy['FY'],y=actual_fy['PLF'],name='Actual PLF (SPV BaseCase)',
            mode='lines+markers',line=dict(color='#3b82f6',width=2.5),marker=dict(size=7,color='#3b82f6')))
    apply_layout(fig_bc, height=380, legend_h=True)
    fig_bc.update_yaxes(title_text='PLF %',range=[0,base_plf*1.5])
    st.plotly_chart(fig_bc,use_container_width=True)

    # Monthly bar
    st.markdown("<div class='sec'>Monthly Actual PLF</div>", unsafe_allow_html=True)
    mp = df_bc_filt.groupby('Invoice_Month2')['PLF'].mean().reset_index().dropna().sort_values('Invoice_Month2')
    mp['Lbl'] = mp['Invoice_Month2'].dt.strftime('%b %Y')
    figm=go.Figure()
    figm.add_trace(go.Bar(x=mp['Lbl'],y=mp['PLF'],marker_color='#22c55e',opacity=0.8,name='Actual PLF'))
    figm.add_hline(y=base_plf,line_dash='dot',line_color='#f59e0b',
        annotation_text=f'Base PLF: {base_plf:.1f}%',annotation_font_color='#f59e0b')
    apply_layout(figm, height=260, legend_h=True)
    figm.update_yaxes(title_text='PLF %')
    st.plotly_chart(figm,use_container_width=True)

    with st.expander("📋 Projected PLF Table"):
        st.dataframe(proj_df[['FY','Projected_PLF']].rename(columns={'Projected_PLF':'Projected PLF (%)'}).assign(**{'Projected PLF (%)': proj_df['Projected_PLF'].round(3)})[['FY','Projected PLF (%)']],use_container_width=True)


    # ── CSV Download ──
    st.markdown("---")
    st.markdown("<div class='sec'>Download Data</div>", unsafe_allow_html=True)
    dl1, dl2 = st.columns(2)
    with dl1:
        proj_csv = proj_df[['FY','Projected_PLF']].round(3)
        proj_csv.columns = ['Financial Year', 'Projected PLF (%)']
        st.download_button("⬇️ Projected PLF CSV", proj_csv.to_csv(index=False).encode('utf-8'), "projected_plf.csv", "text/csv", use_container_width=True)
    with dl2:
        act_csv = actual_fy.copy().round(3)
        act_csv.columns = ['Financial Year', 'Actual PLF (%)']
        st.download_button("⬇️ Actual PLF CSV", act_csv.to_csv(index=False).encode('utf-8'), "actual_plf.csv", "text/csv", use_container_width=True)

# ══════════════════════════════════════════════════════════════
# PAGE 3 — SPV DASHBOARD
# ══════════════════════════════════════════════════════════════
elif page == "SPV Dashboard":
    sf1,sf2 = st.columns([2,2])
    with sf1: spv_sel = st.selectbox("Select SPV", ALL_SPVS, key="sspv")
    with sf2: fy_sel  = st.selectbox("Financial Year", ["All"]+ALL_FY, index=ALL_FY.index(CUR_FY)+1, key="sfy")

    spv_df  = mis[mis['SPV']==spv_sel].copy()
    ttm_s   = get_ttm(spv_df)
    spv_fy  = fy_filter(spv_df, fy_sel)
    overall = spv_df.copy()

    cap  = spv_df['Plant_Capacity'].dropna().max()
    offs = spv_df['Offtaker'].dropna().unique()
    st.markdown(f"<div style='margin-bottom:12px;'><span class='spv-tag' style='border-color:#f59e0b;color:#f59e0b;'>{spv_sel}</span> "+" ".join([f"<span class='spv-tag'>{o}</span>" for o in offs[:2]])+f"<span class='spv-tag' style='border-color:#3b82f6;color:#3b82f6;'>Capacity: {cap:,.0f} KWp</span></div>", unsafe_allow_html=True)

    # TTM
    st.markdown("<div class='sec'>TTM Performance</div>", unsafe_allow_html=True)
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("TTM Billed Units",  f"{ttm_s['Billed_Units'].sum()/1e6:.2f}M")
    k2.metric("TTM Weighted PLF",  f"{ttm_s['PLF'].mean():.2f}%")
    k3.metric("TTM Billed Amount", f"₹{ttm_s['Billed_Amount'].sum()/1e7:.2f}Cr")
    k4.metric("TTM Receivables",   f"₹{ttm_s['Balance_Amount'].sum()/1e7:.2f}Cr")

    # FY (reacts to slicer)
    st.markdown("<div class='sec'>Selected FY Performance</div>", unsafe_allow_html=True)
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("FY Billed Units",  f"{spv_fy['Billed_Units'].sum()/1e6:.2f}M")
    k2.metric("FY PLF",           f"{spv_fy['PLF'].mean():.2f}%")
    k3.metric("FY Billed Amount", f"₹{spv_fy['Billed_Amount'].sum()/1e7:.2f}Cr")
    k4.metric("FY Receivables",   f"₹{spv_fy['Balance_Amount'].sum()/1e7:.2f}Cr")

    # Overall
    st.markdown("<div class='sec'>Overall Performance</div>", unsafe_allow_html=True)
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Overall Billed Units", f"{overall['Billed_Units'].sum()/1e6:.2f}M")
    k2.metric("Overall PLF",          f"{overall['PLF'].mean():.2f}%")
    k3.metric("Overall Billed Amt",   f"₹{overall['Billed_Amount'].sum()/1e7:.2f}Cr")
    k4.metric("Overall Receivables",  f"₹{overall['Balance_Amount'].sum()/1e7:.2f}Cr")

    st.markdown("---")
    c1,c2 = st.columns(2)

    with c1:
        st.markdown("<div class='sec'>Monthly Billed Units — YoY Comparison</div>", unsafe_allow_html=True)
        sm=spv_df.groupby('Invoice_Month2')['Billed_Units'].sum().reset_index().sort_values('Invoice_Month2')
        sm['Lbl']=sm['Invoice_Month2'].dt.strftime('%b %Y')
        sm['Prev']=sm['Billed_Units'].shift(12)
        fig=go.Figure()
        fig.add_trace(go.Bar(x=sm['Lbl'],y=sm['Billed_Units']/1e6,name='Billed Units',marker_color='#3b82f6',opacity=0.85))
        fig.add_trace(go.Scatter(x=sm['Lbl'],y=sm['Prev']/1e6,name='Prev Year',line=dict(color='#f59e0b',width=2),mode='lines+markers',marker=dict(size=4)))
        apply_layout(fig, height=280, legend_h=True)
        fig.update_yaxes(title_text="Million Units")
        st.plotly_chart(fig,use_container_width=True)

    with c2:
        st.markdown("<div class='sec'>Monthly PLF — YoY Comparison</div>", unsafe_allow_html=True)
        sp=spv_df.groupby('Invoice_Month2')['PLF'].mean().reset_index().sort_values('Invoice_Month2')
        sp['Lbl']=sp['Invoice_Month2'].dt.strftime('%b %Y')
        sp['Prev']=sp['PLF'].shift(12)
        fig2=go.Figure()
        fig2.add_trace(go.Bar(x=sp['Lbl'],y=sp['PLF'],name='PLF %',marker_color='#22c55e',opacity=0.85))
        fig2.add_trace(go.Scatter(x=sp['Lbl'],y=sp['Prev'],name='Prev Year PLF',line=dict(color='#f59e0b',width=2),mode='lines+markers',marker=dict(size=4)))
        apply_layout(fig2, height=280, legend_h=True)
        fig2.update_yaxes(title_text="PLF %")
        st.plotly_chart(fig2,use_container_width=True)

    c3,c4 = st.columns(2)

    with c3:
        st.markdown("<div class='sec'>Last 3 Years — Financial Comparison</div>", unsafe_allow_html=True)
        fy3=spv_df.groupby('FY').agg(Billed=('Billed_Amount','sum'),Realized=('Realized_Amount','sum'),Recv=('Balance_Amount','sum')).reset_index().sort_values('FY').tail(3)
        fig3=go.Figure()
        fig3.add_trace(go.Bar(x=fy3['FY'],y=fy3['Billed']/1e7,name='Total Billed',marker_color='#3b82f6'))
        fig3.add_trace(go.Bar(x=fy3['FY'],y=fy3['Realized']/1e7,name='Total Realized',marker_color='#22c55e'))
        fig3.add_trace(go.Bar(x=fy3['FY'],y=fy3['Recv']/1e7,name='Receivables',marker_color='#ef4444'))
        apply_layout(fig3, height=280, legend_h=True, barmode="group")
        fig3.update_yaxes(title_text="₹ Crore")
        st.plotly_chart(fig3,use_container_width=True)

    with c4:
        st.markdown("<div class='sec'>Calculated PLF and Previous Year by Quarter</div>", unsafe_allow_html=True)
        qc,qp=quarterly_plf(spv_df)
        fig4=go.Figure()
        if not qc.empty: fig4.add_trace(go.Bar(x=qc['Q'],y=qc['PLF'],name='Current PLF',marker_color='#3b82f6'))
        if not qp.empty: fig4.add_trace(go.Scatter(x=qp['Q'],y=qp['PLF'],name='Prev Year PLF',line=dict(color='#f59e0b',width=2.5),mode='lines+markers',marker=dict(size=6)))
        apply_layout(fig4, height=280, legend_h=True)
        fig4.update_yaxes(title_text="PLF %")
        st.plotly_chart(fig4,use_container_width=True)


    # ── CSV Download ──
    st.markdown("---")
    st.markdown("<div class='sec'>Download Data</div>", unsafe_allow_html=True)
    dl1, dl2 = st.columns(2)
    with dl1:
        spv_fy_csv = spv_fy[['Invoice_Month2','Billed_Units','PLF','Billed_Amount','Realized_Amount','Balance_Amount']].copy()
        spv_fy_csv['Invoice_Month2'] = spv_fy_csv['Invoice_Month2'].dt.strftime('%b-%Y')
        spv_fy_csv.columns = ['Month','Billed Units','PLF (%)','Billed Amount','Realized Amount','Balance Amount']
        st.download_button("⬇️ SPV FY Data CSV", spv_fy_csv.to_csv(index=False).encode('utf-8'), f"{spv_sel}_fy_data.csv", "text/csv", use_container_width=True)
    with dl2:
        spv_all_csv = spv_df[['Invoice_Month2','FY','Billed_Units','PLF','Billed_Amount','Realized_Amount','Balance_Amount']].copy()
        spv_all_csv['Invoice_Month2'] = spv_all_csv['Invoice_Month2'].dt.strftime('%b-%Y')
        spv_all_csv.columns = ['Month','FY','Billed Units','PLF (%)','Billed Amount','Realized Amount','Balance Amount']
        st.download_button("⬇️ SPV All Time CSV", spv_all_csv.to_csv(index=False).encode('utf-8'), f"{spv_sel}_all_data.csv", "text/csv", use_container_width=True)

# ══════════════════════════════════════════════════════════════
# PAGE 4 — PORTFOLIO DETAILS
# ══════════════════════════════════════════════════════════════
elif page == "Portfolio Details":

    c1,c2 = st.columns([1.2,1])

    with c1:
        st.markdown("<div class='sec'>SPV Details</div>", unsafe_allow_html=True)
        tbl = port[['SPV','DC_Capacity_KWp','Tariff']].dropna(subset=['SPV']).copy()
        tbl['DC_Capacity_KWp'] = tbl['DC_Capacity_KWp'].round(0)
        tbl['Tariff'] = tbl['Tariff'].round(2)
        total = pd.DataFrame([{'SPV':'Total','DC_Capacity_KWp':tbl['DC_Capacity_KWp'].sum(),'Tariff':tbl['Tariff'].mean().round(2)}])
        disp = pd.concat([tbl,total],ignore_index=True)
        disp.columns = ['SPV','DC Capacity (KWp)','Tariff']
        st.dataframe(disp, use_container_width=True, height=340)

    with c2:
        st.markdown("<div class='sec'>Sum of DC Capacity (KWp) by SPV</div>", unsafe_allow_html=True)
        pie = port.dropna(subset=['SPV','DC_Capacity_KWp']).groupby('SPV')['DC_Capacity_KWp'].sum().reset_index()
        pie = pie[pie['DC_Capacity_KWp']>0]
        figp=px.pie(pie,values='DC_Capacity_KWp',names='SPV',color_discrete_sequence=COLORS,hole=0.28)
        figp.update_traces(textposition='outside',textfont_size=8,texttemplate='%{label}<br>%{value:,.0f} (%{percent:.1%})')
        apply_layout(figp, height=380, legend_h=True)
        st.plotly_chart(figp,use_container_width=True)

    st.markdown("---")
    c3,c4 = st.columns(2)

    with c3:
        st.markdown("<div class='sec'>Capacity by Region</div>", unsafe_allow_html=True)
        reg=port.dropna(subset=['Region']).groupby('Region')['DC_Capacity_KWp'].sum().reset_index().sort_values('DC_Capacity_KWp')
        figr=px.bar(reg,x='DC_Capacity_KWp',y='Region',orientation='h',color='DC_Capacity_KWp',color_continuous_scale=[[0,'#0f2040'],[1,'#f59e0b']])
        apply_layout(figr, height=260, showlegend=True, coloraxis=True)
        figr.update_xaxes(title_text="Capacity (KWp)")
        st.plotly_chart(figr,use_container_width=True)

    with c4:
        st.markdown("<div class='sec'>Capacity by State</div>", unsafe_allow_html=True)
        st_df=port.dropna(subset=['State']).groupby('State')['DC_Capacity_KWp'].sum().reset_index().sort_values('DC_Capacity_KWp')
        figs=px.bar(st_df,x='DC_Capacity_KWp',y='State',orientation='h',color='DC_Capacity_KWp',color_continuous_scale=[[0,'#0f2040'],[1,'#3b82f6']])
        apply_layout(figs, height=260, showlegend=True, coloraxis=True)
        figs.update_xaxes(title_text="Capacity (KWp)")
        st.plotly_chart(figs,use_container_width=True)

    c5,c6 = st.columns(2)
    with c5:
        st.markdown("<div class='sec'>Tariff Distribution (₹/kWh)</div>", unsafe_allow_html=True)
        figt=px.histogram(port.dropna(subset=['Tariff']),x='Tariff',nbins=20,color_discrete_sequence=['#f59e0b'])
        apply_layout(figt, height=250, legend_h=True)
        figt.update_xaxes(title_text="Tariff (₹/kWh)")
        st.plotly_chart(figt,use_container_width=True)

    with c6:
        st.markdown("<div class='sec'>Credit Rating Breakdown</div>", unsafe_allow_html=True)
        if 'Rating_Category' in port.columns:
            rat=port.dropna(subset=['Rating_Category']).groupby('Rating_Category')['DC_Capacity_KWp'].sum().reset_index()
            figrc=px.bar(rat,x='Rating_Category',y='DC_Capacity_KWp',color='Rating_Category',color_discrete_sequence=COLORS)
            apply_layout(figrc, height=250, legend_h=True)
            figrc.update_yaxes(title_text="Capacity (KWp)")
            st.plotly_chart(figrc,use_container_width=True)

    with st.expander("📋 Full Portfolio Table"):
        full=port[['SPV','DC_Capacity_KWp','Region','State','Tariff','Balance_PPA_Tenor','Rating_Category','COD']].copy()
        full.columns=['SPV','DC Capacity (KWp)','Region','State','Tariff (₹)','Balance PPA Tenor','Credit Rating','COD']
        st.dataframe(full,use_container_width=True)

    # ── CSV Download ──
    st.markdown("---")
    st.markdown("<div class='sec'>Download Data</div>", unsafe_allow_html=True)
    dl1, dl2 = st.columns(2)
    with dl1:
        port_csv = port[['SPV','DC_Capacity_KWp','Region','State','Tariff','Balance_PPA_Tenor','Rating_Category']].copy().round(2)
        port_csv.columns = ['SPV','DC Capacity (KWp)','Region','State','Tariff','Balance PPA Tenor','Credit Rating']
        st.download_button("⬇️ Portfolio Details CSV", port_csv.to_csv(index=False).encode('utf-8'), "portfolio_details.csv", "text/csv", use_container_width=True)
    with dl2:
        cap_csv = port.groupby('State')['DC_Capacity_KWp'].sum().reset_index().round(2)
        cap_csv.columns = ['State','Total DC Capacity (KWp)']
        st.download_button("⬇️ Capacity by State CSV", cap_csv.to_csv(index=False).encode('utf-8'), "capacity_by_state.csv", "text/csv", use_container_width=True)

