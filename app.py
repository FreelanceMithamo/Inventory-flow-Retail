import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="StockFlow Retail",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------------------------
# Enhanced CSS - Red / White / Grey Theme
# -------------------------------------------------
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Login Card */
    .login-card {
        background: white;
        border-radius: 20px;
        padding: 2.5rem 2.8rem;
        box-shadow: 0 25px 50px -12px rgba(220, 38, 38, 0.15);
        border-top: 6px solid #dc2626;
        max-width: 420px;
        margin: 0 auto;
    }
    
    /* Module cards */
    .module-card {
        background: white;
        border-radius: 18px;
        padding: 1.8rem 1.5rem;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.07);
        border: 1px solid #e5e7eb;
        transition: all 0.25s ease;
        height: 100%;
        text-align: center;
    }
    .module-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 20px 25px -5px rgba(220, 38, 38, 0.12);
        border-color: #fca5a5;
    }
    
    .logo-circle {
        width: 74px;
        height: 74px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.1rem;
        margin: 0 auto 1.1rem auto;
    }
    
    .transfer { background: #fee2e2; color: #dc2626; }
    .health   { background: #dcfce7; color: #16a34a; }
    .lpo      { background: #ffedd5; color: #ea580c; }
    
    /* Buttons */
    .stButton > button {
        background: #dc2626 !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: #b91c1c !important;
        box-shadow: 0 4px 12px rgba(220, 38, 38, 0.35);
    }
    
    /* Secondary button */
    .stButton > button[kind="secondary"] {
        background: #f3f4f6 !important;
        color: #374151 !important;
    }
    
    h1, h2, h3 {
        color: #1f2937 !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        border-radius: 10px !important;
        border: 1.5px solid #d1d5db !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #dc2626 !important;
        box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.15) !important;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# Auth
# -------------------------------------------------
USERS = {
    "admin": "stockflow2025",
    "demo": "demo123",
    "manager": "branch123"
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "module" not in st.session_state:
    st.session_state.module = None

def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.3, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align:center; margin-bottom: 1.8rem;">
            <div style="font-size: 3.8rem; margin-bottom: 0.3rem;">📦</div>
            <h1 style="margin:0; font-size: 2.6rem; font-weight: 800; color: #dc2626;">
                StockFlow
            </h1>
            <p style="color: #6b7280; font-size: 1.15rem; margin-top: 0.3rem;">
                Retail Inventory Intelligence Platform
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Login Card
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        st.markdown("### Sign in to your account")
        st.markdown("<p style='color:#6b7280; margin-bottom:1.5rem;'>Enter your credentials below</p>", unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            
            if submitted:
                if username in USERS and USERS[username] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align:center; margin-top: 2rem; color: #9ca3af; font-size: 0.9rem;">
            Demo accounts:<br>
            <b>admin</b> / stockflow2025 &nbsp;&nbsp;|&nbsp;&nbsp; <b>demo</b> / demo123
        </div>
        """, unsafe_allow_html=True)

def home_page():
    # Top bar
    col_left, col_right = st.columns([4, 1])
    with col_left:
        st.markdown(f"""
        <h2 style="margin-bottom:0;">Welcome back, <span style="color:#dc2626;">{st.session_state.username}</span></h2>
        <p style="color:#6b7280;">Select a module to continue</p>
        """, unsafe_allow_html=True)
    with col_right:
        if st.button("Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.markdown("---")
    
    c1, c2, c3 = st.columns(3, gap="large")
    
    with c1:
        st.markdown("""
        <div class="module-card">
            <div class="logo-circle transfer">🔄</div>
            <h3 style="margin:0.5rem 0;">Transfer Hub</h3>
            <p style="color:#6b7280; font-size:0.95rem; line-height:1.5;">
                Smart inter-branch stock transfers.<br>
                Move excess inventory to high-demand locations.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Open Transfer Hub →", key="btn_transfer", use_container_width=True):
            st.session_state.module = "transfer"
            st.rerun()
    
    with c2:
        st.markdown("""
        <div class="module-card">
            <div class="logo-circle health">❤️</div>
            <h3 style="margin:0.5rem 0;">Stock Health</h3>
            <p style="color:#6b7280; font-size:0.95rem; line-height:1.5;">
                Detect overstock, dead stock,<br>
                aged inventory and stockouts.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Open Stock Health →", key="btn_health", use_container_width=True):
            st.session_state.module = "health"
            st.rerun()
    
    with c3:
        st.markdown("""
        <div class="module-card">
            <div class="logo-circle lpo">📋</div>
            <h3 style="margin:0.5rem 0;">Smart LPO</h3>
            <p style="color:#6b7280; font-size:0.95rem; line-height:1.5;">
                Automated purchase order<br>
                suggestions for every branch.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Open Smart LPO →", key="btn_lpo", use_container_width=True):
            st.session_state.module = "lpo"
            st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; color:#9ca3af; font-size:0.9rem;">
        StockFlow Retail • Built for multi-branch pharmacies, kiosks, restaurants & retail stores
    </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------
# Transfer Hub (same solid logic as before)
# -------------------------------------------------
def transfer_hub():
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown("## 🔄 Transfer Hub")
        st.caption("General inter-branch transfer recommendations")
    with col2:
        if st.button("← Back", use_container_width=True):
            st.session_state.module = None
            st.rerun()
    
    st.markdown("---")
    
    uploaded = st.file_uploader(
        "Upload Excel file (must contain Sales + Stocks sheets in wide format)",
        type=["xlsx", "xls"]
    )
    
    if uploaded is None:
        st.info("Please upload your Sales + Stocks Excel file to generate recommendations.")
        return
    
    try:
        xlsx = pd.ExcelFile(uploaded)
        st.success(f"Sheets detected: {', '.join(xlsx.sheet_names)}")
        
        sales_sheet = next((s for s in xlsx.sheet_names if "sales" in s.lower()), None)
        stock_sheet = next((s for s in xlsx.sheet_names if "stock" in s.lower()), None)
        
        if not sales_sheet or not stock_sheet:
            st.error("Could not find both Sales and Stocks sheets.")
            return
        
        df_sales = pd.read_excel(xlsx, sheet_name=sales_sheet)
        df_stock = pd.read_excel(xlsx, sheet_name=stock_sheet)
        
        def make_key(df):
            brand = next((c for c in df.columns if "brand" in str(c).lower()), None)
            group = next((c for c in df.columns if "group" in str(c).lower()), None)
            model = next((c for c in df.columns if "model" in str(c).lower()), None)
            parts = []
            if brand: parts.append(df[brand].astype(str).str.strip())
            if group: parts.append(df[group].astype(str).str.strip())
            if model: parts.append(df[model].astype(str).str.strip())
            key = parts[0]
            for p in parts[1:]:
                key = key + " | " + p
            return key, brand, group, model
        
        # Sales
        df_s = df_sales.copy()
        df_s["Product_Key"], brand_col, group_col, model_col = make_key(df_s)
        fixed = ["Product_Key"]
        if brand_col: fixed.append(brand_col)
        if group_col: fixed.append(group_col)
        if model_col: fixed.append(model_col)
        branches = [c for c in df_s.columns if c not in fixed and "total" not in str(c).lower() and not str(c).startswith("Unnamed")]
        sales_long = df_s.melt(id_vars=fixed, value_vars=branches, var_name="Branch", value_name="Qty_Sold")
        sales_long["Qty_Sold"] = pd.to_numeric(sales_long["Qty_Sold"], errors="coerce").fillna(0)
        sales_long["Branch"] = sales_long["Branch"].astype(str).str.strip()
        sales_agg = sales_long.groupby(["Product_Key", "Branch"], as_index=False).agg(
            Total_Sold=("Qty_Sold", "sum"),
            **{c: (c, "first") for c in [brand_col, group_col, model_col] if c}
        )
        sales_agg["Monthly_Avg"] = (sales_agg["Total_Sold"] / 8).round(2)
        
        # Stocks
        df_st = df_stock.copy()
        df_st["Product_Key"], _, _, _ = make_key(df_st)
        fixed2 = ["Product_Key"]
        branches2 = [c for c in df_st.columns if c not in fixed2 and "total" not in str(c).lower() and not str(c).startswith("Unnamed")]
        stock_long = df_st.melt(id_vars=fixed2, value_vars=branches2, var_name="Branch", value_name="Current_Stock")
        stock_long["Current_Stock"] = pd.to_numeric(stock_long["Current_Stock"], errors="coerce").fillna(0)
        stock_long["Branch"] = stock_long["Branch"].astype(str).str.strip()
        stock_agg = stock_long.groupby(["Product_Key", "Branch"], as_index=False)["Current_Stock"].sum()
        
        df = pd.merge(stock_agg, sales_agg, on=["Product_Key", "Branch"], how="outer")
        df["Current_Stock"] = df["Current_Stock"].fillna(0)
        df["Total_Sold"] = df["Total_Sold"].fillna(0)
        df["Monthly_Avg"] = df["Monthly_Avg"].fillna(0)
        
        if brand_col: df = df.rename(columns={brand_col: "Brand"})
        if group_col: df = df.rename(columns={group_col: "ItemGroup1"})
        if model_col: df = df.rename(columns={model_col: "Model No"})
        
        # Generate transfers
        MIN_KEEP = 1
        transfers = []
        
        for product, group in df.groupby("Product_Key"):
            receivers = group[
                (group["Monthly_Avg"] >= 0.5) &
                (group["Current_Stock"] <= 3)
            ].sort_values("Total_Sold", ascending=False)
            
            if len(receivers) == 0:
                continue
            
            receiver_branches = set(receivers["Branch"])
            
            donors = group[
                (group["Current_Stock"] >= 2) &
                (~group["Branch"].isin(receiver_branches))
            ].sort_values(["Monthly_Avg", "Current_Stock"], ascending=[True, False])
            
            if len(donors) == 0:
                continue
            
            donors = donors.copy()
            donors["Available"] = (donors["Current_Stock"] - MIN_KEEP).clip(lower=0)
            
            for _, rec in receivers.iterrows():
                target = max(2, int(round(rec["Monthly_Avg"] * 2)))
                needed = max(0, target - int(rec["Current_Stock"]))
                if needed <= 0:
                    continue
                
                remaining = needed
                
                for idx, don in donors.iterrows():
                    if remaining <= 0:
                        break
                    if don["Monthly_Avg"] >= rec["Monthly_Avg"] * 0.75:
                        continue
                    
                    can_give = donors.at[idx, "Available"]
                    if can_give <= 0:
                        continue
                    
                    give = min(remaining, can_give)
                    if give > 0:
                        transfers.append({
                            "Receiver Showroom": rec["Branch"],
                            "Brand": rec.get("Brand", ""),
                            "ItemGroup1": rec.get("ItemGroup1", ""),
                            "Model No": rec.get("Model No", ""),
                            "Receiver current stocks": int(rec["Current_Stock"]) if rec["Current_Stock"] > 0 else "-",
                            "Receiver qty sold period": int(rec["Total_Sold"]),
                            "Donor showroom": don["Branch"],
                            "Donor transfer Qty": int(give)
                        })
                        donors.at[idx, "Available"] -= give
                        remaining -= give
        
        report = pd.DataFrame(transfers)
        
        if len(report) == 0:
            st.warning("No transfer available with current rules.")
        else:
            report = report.sort_values(
                by=["Receiver qty sold period", "Donor transfer Qty"],
                ascending=[False, False]
            ).reset_index(drop=True)
            
            st.success(f"**{len(report)}** recommendations • Total units to move: **{report['Donor transfer Qty'].sum()}**")
            st.dataframe(report, use_container_width=True, height=480)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                report.to_excel(writer, sheet_name="transfers", index=False)
            
            st.download_button(
                "⬇️ Download Transfer Report",
                data=output.getvalue(),
                file_name=f"Inter_Branch_Transfers_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
    except Exception as e:
        st.error(f"Error processing file: {e}")

def stock_health():
    st.markdown("## ❤️ Stock Health")
    st.info("This module is next. We will build it together.")
    if st.button("← Back to Modules"):
        st.session_state.module = None
        st.rerun()

def smart_lpo():
    st.markdown("## 📋 Smart LPO")
    st.info("This module is next. We will build it together.")
    if st.button("← Back to Modules"):
        st.session_state.module = None
        st.rerun()

# -------------------------------------------------
# Router
# -------------------------------------------------
if not st.session_state.authenticated:
    login_page()
else:
    if st.session_state.module is None:
        home_page()
    elif st.session_state.module == "transfer":
        transfer_hub()
    elif st.session_state.module == "health":
        stock_health()
    elif st.session_state.module == "lpo":
        smart_lpo()
