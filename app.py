import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# -------------------------------------------------
# Page Config & Styling
# -------------------------------------------------
st.set_page_config(
    page_title="StockFlow Retail | Inventory Platform",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%); }
    .module-card {
        background: white;
        border-radius: 16px;
        padding: 1.8rem;
        box-shadow: 0 10px 25px -5px rgb(0 0 0 / 0.08);
        border: 1px solid #e2e8f0;
        height: 100%;
    }
    .logo-circle {
        width: 70px; height: 70px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 2rem; margin-bottom: 1rem;
    }
    .transfer { background: #dbeafe; color: #1d4ed8; }
    .health   { background: #dcfce7; color: #15803d; }
    .lpo      { background: #ffedd5; color: #c2410c; }
    h1, h2, h3 { color: #0f172a !important; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# Simple Auth
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
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; margin-bottom:2rem;">
            <div style="font-size:3.5rem;">📦</div>
            <h1 style="margin:0;">StockFlow Retail</h1>
            <p style="color:#64748b;">Inventory Intelligence for Multi-Branch Retail</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In", use_container_width=True):
                if username in USERS and USERS[username] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        st.caption("Demo: admin / stockflow2025  or  demo / demo123")

# -------------------------------------------------
# Home
# -------------------------------------------------
def home_page():
    st.markdown(f"### Welcome, **{st.session_state.username}**")
    st.markdown("Select a module")
    st.markdown("---")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
        <div class="module-card">
            <div class="logo-circle transfer">🔄</div>
            <h3>Transfer Hub</h3>
            <p style="color:#64748b;">Smart inter-branch stock transfers</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Transfer Hub", key="t", use_container_width=True):
            st.session_state.module = "transfer"
            st.rerun()
    
    with c2:
        st.markdown("""
        <div class="module-card">
            <div class="logo-circle health">❤️</div>
            <h3>Stock Health</h3>
            <p style="color:#64748b;">Overstock • Dead • Aged • Stockouts</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Stock Health", key="h", use_container_width=True):
            st.session_state.module = "health"
            st.rerun()
    
    with c3:
        st.markdown("""
        <div class="module-card">
            <div class="logo-circle lpo">📋</div>
            <h3>Smart LPO</h3>
            <p style="color:#64748b;">Automated order suggestions</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Smart LPO", key="l", use_container_width=True):
            st.session_state.module = "lpo"
            st.rerun()
    
    st.markdown("---")
    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# -------------------------------------------------
# MODULE 1: Transfer Hub (General Inter-Branch Logic)
# -------------------------------------------------
def transfer_hub():
    st.markdown("## 🔄 Transfer Hub")
    st.caption("General inter-branch transfer recommendations")
    
    if st.button("← Back to Modules"):
        st.session_state.module = None
        st.rerun()
    
    st.markdown("---")
    
    uploaded = st.file_uploader(
        "Upload Excel file containing **Sales** and **Stocks** sheets (wide format)",
        type=["xlsx", "xls"]
    )
    
    if uploaded is None:
        st.info("Please upload your Sales + Stocks Excel file.")
        return
    
    try:
        xlsx = pd.ExcelFile(uploaded)
        st.write("Sheets found:", xlsx.sheet_names)
        
        sales_sheet = next((s for s in xlsx.sheet_names if "sales" in s.lower()), None)
        stock_sheet = next((s for s in xlsx.sheet_names if "stock" in s.lower()), None)
        
        if not sales_sheet or not stock_sheet:
            st.error("Could not automatically detect Sales and Stocks sheets.")
            return
        
        df_sales = pd.read_excel(xlsx, sheet_name=sales_sheet)
        df_stock = pd.read_excel(xlsx, sheet_name=stock_sheet)
        
        # ---------- Helper ----------
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
        
        # ---------- Sales (wide → long) ----------
        df_s = df_sales.copy()
        df_s["Product_Key"], brand_col, group_col, model_col = make_key(df_s)
        
        fixed = ["Product_Key"]
        if brand_col: fixed.append(brand_col)
        if group_col: fixed.append(group_col)
        if model_col: fixed.append(model_col)
        
        branches = [c for c in df_s.columns 
                    if c not in fixed 
                    and "total" not in str(c).lower() 
                    and not str(c).startswith("Unnamed")]
        
        sales_long = df_s.melt(id_vars=fixed, value_vars=branches, 
                               var_name="Branch", value_name="Qty_Sold")
        sales_long["Qty_Sold"] = pd.to_numeric(sales_long["Qty_Sold"], errors="coerce").fillna(0)
        sales_long["Branch"] = sales_long["Branch"].astype(str).str.strip()
        
        sales_agg = sales_long.groupby(["Product_Key", "Branch"], as_index=False).agg(
            Total_Sold=("Qty_Sold", "sum"),
            **{c: (c, "first") for c in [brand_col, group_col, model_col] if c}
        )
        sales_agg["Monthly_Avg"] = (sales_agg["Total_Sold"] / 8).round(2)
        
        # ---------- Stocks (wide → long) ----------
        df_st = df_stock.copy()
        df_st["Product_Key"], _, _, _ = make_key(df_st)
        
        fixed2 = ["Product_Key"]
        branches2 = [c for c in df_st.columns 
                     if c not in fixed2 
                     and "total" not in str(c).lower() 
                     and not str(c).startswith("Unnamed")]
        
        stock_long = df_st.melt(id_vars=fixed2, value_vars=branches2,
                                var_name="Branch", value_name="Current_Stock")
        stock_long["Current_Stock"] = pd.to_numeric(stock_long["Current_Stock"], errors="coerce").fillna(0)
        stock_long["Branch"] = stock_long["Branch"].astype(str).str.strip()
        
        stock_agg = stock_long.groupby(["Product_Key", "Branch"], as_index=False)["Current_Stock"].sum()
        
        # ---------- Merge ----------
        df = pd.merge(stock_agg, sales_agg, on=["Product_Key", "Branch"], how="outer")
        df["Current_Stock"] = df["Current_Stock"].fillna(0)
        df["Total_Sold"] = df["Total_Sold"].fillna(0)
        df["Monthly_Avg"] = df["Monthly_Avg"].fillna(0)
        
        if brand_col: df = df.rename(columns={brand_col: "Brand"})
        if group_col: df = df.rename(columns={group_col: "ItemGroup1"})
        if model_col: df = df.rename(columns={model_col: "Model No"})
        
        st.success(f"Data loaded • {df['Product_Key'].nunique()} products • {df['Branch'].nunique()} branches")
        
        # ---------- Generate Transfers (General Logic) ----------
        MIN_KEEP = 1
        transfers = []
        
        for product, group in df.groupby("Product_Key"):
            
            # Receivers: good sales + low stock
            receivers = group[
                (group["Monthly_Avg"] >= 0.5) &
                (group["Current_Stock"] <= 3)
            ].sort_values("Total_Sold", ascending=False)
            
            if len(receivers) == 0:
                continue
            
            receiver_branches = set(receivers["Branch"])
            
            # Donors: excess stock AND not a receiver for this product
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
                    
                    # Extra safety: donor must have lower sales
                    if don["Monthly_Avg"] >= rec["Monthly_Avg"] * 0.75:
                        continue
                    
                    can_give = donors.at[idx, "Available"]
                    if can_give <= 0:
                        continue
                    
                    give = min(remaining, can_give)
                    give = int(give)
                    
                    if give > 0:
                        transfers.append({
                            "Receiver Showroom": rec["Branch"],
                            "Brand": rec.get("Brand", ""),
                            "ItemGroup1": rec.get("ItemGroup1", ""),
                            "Model No": rec.get("Model No", ""),
                            "Receiver current stocks": int(rec["Current_Stock"]) if rec["Current_Stock"] > 0 else "-",
                            "Receiver qty sold period": int(rec["Total_Sold"]),
                            "Donor showroom": don["Branch"],
                            "Donor transfer Qty": give
                        })
                        
                        donors.at[idx, "Available"] -= give
                        remaining -= give
        
        # ---------- Results ----------
        report = pd.DataFrame(transfers)
        
        if len(report) == 0:
            st.warning("No transfer available with the current rules.")
        else:
            report = report.sort_values(
                by=["Receiver qty sold period", "Donor transfer Qty"],
                ascending=[False, False]
            ).reset_index(drop=True)
            
            st.success(f"**{len(report)}** transfer recommendations generated • Total units: **{report['Donor transfer Qty'].sum()}**")
            
            st.dataframe(report, use_container_width=True, height=480)
            
            # Download
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                report.to_excel(writer, sheet_name="transfers", index=False)
            
            st.download_button(
                label="⬇️ Download Transfer Report",
                data=output.getvalue(),
                file_name=f"Inter_Branch_Transfers_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
    except Exception as e:
        st.error(f"Error: {e}")
        st.exception(e)

# -------------------------------------------------
# Placeholders
# -------------------------------------------------
def stock_health():
    st.markdown("## ❤️ Stock Health")
    st.info("Next module we will build together.")
    if st.button("← Back"):
        st.session_state.module = None
        st.rerun()

def smart_lpo():
    st.markdown("## 📋 Smart LPO")
    st.info("Next module we will build together.")
    if st.button("← Back"):
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
