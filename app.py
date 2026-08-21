import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime
import re
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="StockFlow Retail",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------------------------
# CSS
# -------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(rgba(15, 23, 42, 0.78), rgba(15, 23, 42, 0.85)),
                    url('https://images.unsplash.com/photo-1556911220-bff31c812dba?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    #MainMenu, footer, header {visibility: hidden;}
   
    .login-card {
        background: rgba(255, 255, 255, 0.96);
        border-radius: 20px;
        padding: 2.2rem 2.5rem;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.4);
        border-top: 6px solid #dc2626;
        max-width: 440px;
        margin: 0 auto;
        backdrop-filter: blur(8px);
    }
   
    .module-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 18px;
        padding: 1.9rem 1.5rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.25);
        border: 1px solid rgba(255,255,255,0.3);
        transition: all 0.28s ease;
        height: 100%;
        text-align: center;
        backdrop-filter: blur(6px);
    }
    .module-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 25px 35px -5px rgba(220, 38, 38, 0.3);
        border-color: #f87171;
        background: rgba(255, 245, 245, 0.97);
    }
   
    .logo-circle {
        width: 80px; height: 80px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.9rem; margin: 0 auto 1.1rem auto;
    }
   
    .transfer { background: #fee2e2; color: #dc2626; }
    .health   { background: #dcfce7; color: #16a34a; }
    .lpo      { background: #ffedd5; color: #ea580c; }
   
    .stButton > button {
        background: #dc2626 !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover {
        background: #b91c1c !important;
    }
   
    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: #f3f4f6 !important;
    }
    
    .login-card h1, .login-card h2, .login-card h3, 
    .login-card h4, .login-card h5, .login-card p,
    .login-card label, .login-card span, .login-card div {
        color: #1f2937 !important;
    }
    
    .module-card h1, .module-card h2, .module-card h3, 
    .module-card h4, .module-card p, .module-card span {
        color: #1f2937 !important;
    }
    
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        color: #111827 !important;
        border: 1.5px solid #d1d5db !important;
        border-radius: 8px !important;
    }
    
    button[data-baseweb="tab"] {
        color: #e5e7eb !important;
    }
    
    .user-badge {
        background: #fee2e2;
        color: #dc2626;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .footer-text {
        text-align: center;
        color: #d1d5db !important;
        font-size: 0.95rem;
        margin-top: 2.5rem;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# Auth State
# -------------------------------------------------
if "users" not in st.session_state:
    st.session_state.users = {}

st.session_state.users["Administrator"] = "Jose2024"

if "demo" not in st.session_state.users:
    st.session_state.users["demo"] = "demo123"
if "manager" not in st.session_state.users:
    st.session_state.users["manager"] = "branch123"

if "pending_resets" not in st.session_state:
    st.session_state.pending_resets = []

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "module" not in st.session_state:
    st.session_state.module = None

def is_strong_password(pw: str) -> bool:
    if len(pw) < 6:
        return False
    has_letter = bool(re.search(r"[a-zA-Z]", pw))
    has_number = bool(re.search(r"[0-9]", pw))
    return has_letter and has_number

# -------------------------------------------------
# Login Page
# -------------------------------------------------
def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])
   
    with col2:
        st.markdown("""
        <div style="text-align:center; margin-bottom: 1.5rem;">
            <div style="font-size: 3.5rem;">🏠📺🍳📦</div>
            <h1 style="margin:0; font-size: 2.5rem; font-weight: 800; color: #ffffff !important;">StockFlow</h1>
            <p style="color: #e5e7eb !important; font-size: 1.1rem;">Retail Inventory Intelligence Platform</p>
        </div>
        """, unsafe_allow_html=True)
       
        tab_login, tab_create, tab_forgot = st.tabs(["Sign In", "Create Account", "Forgot Password"])
        
        with tab_login:
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Sign In", use_container_width=True):
                    if username in st.session_state.users and st.session_state.users[username] == password:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tab_create:
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.markdown("##### Create a new account")
            with st.form("create_form"):
                new_user = st.text_input("Choose Username")
                new_pw = st.text_input("Password", type="password", help="Must contain letters and numbers (min 6 characters)")
                confirm_pw = st.text_input("Confirm Password", type="password")
                
                if st.form_submit_button("Create Account", use_container_width=True):
                    if not new_user or not new_pw:
                        st.error("Please fill all fields")
                    elif new_user in st.session_state.users:
                        st.error("Username already exists")
                    elif new_pw != confirm_pw:
                        st.error("Passwords do not match")
                    elif not is_strong_password(new_pw):
                        st.error("Password must contain both letters and numbers (min 6 characters)")
                    else:
                        st.session_state.users[new_user] = new_pw
                        st.success("Account created successfully! You can now sign in.")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tab_forgot:
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.markdown("##### Forgot Password")
            st.caption("A request will be sent to the Admin.")
            
            with st.form("forgot_form"):
                forgot_user = st.text_input("Enter your Username")
                if st.form_submit_button("Request Password Reset", use_container_width=True):
                    if forgot_user not in st.session_state.users:
                        st.error("Username not found")
                    elif forgot_user in st.session_state.pending_resets:
                        st.warning("A reset request is already pending.")
                    else:
                        st.session_state.pending_resets.append(forgot_user)
                        st.success("Request sent to Admin.")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="footer-text">Created by Joseph in 2026</div>', unsafe_allow_html=True)

# -------------------------------------------------
# Home Page
# -------------------------------------------------
def home_page():
    col_left, col_right = st.columns([5, 1])
    with col_left:
        st.markdown(f"""
        <h2 style="margin-bottom:0; color:#ffffff !important;">Welcome back,
        <span style="color:#fca5a5;">{st.session_state.username}</span></h2>
        <p style="color:#e5e7eb !important;">Select a module or manage your account</p>
        """, unsafe_allow_html=True)
    with col_right:
        if st.button("Logout", use_container_width=True):
            for key in ["authenticated", "username", "module"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
   
    st.markdown("---")
   
    c1, c2, c3 = st.columns(3, gap="large")
   
    with c1:
        st.markdown("""
        <div class="module-card">
            <div class="logo-circle transfer">🚚📦🚚</div>
            <h3 style="margin:0.5rem 0;">Transfer Hub</h3>
            <p style="color:#6b7280; font-size:0.95rem;">Inter-branch stock transfers</p>
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
            <p style="color:#6b7280; font-size:0.95rem;">Overstock • Dead stock • Stockouts</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Open Stock Health →", key="btn_health", use_container_width=True):
            st.session_state.module = "health"
            st.rerun()
   
    with c3:
        st.markdown("""
        <div class="module-card">
            <div class="logo-circle lpo">📄📋</div>
            <h3 style="margin:0.5rem 0;">Smart LPO</h3>
            <p style="color:#6b7280; font-size:0.95rem;">Automated Local Purchase Orders</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Open Smart LPO →", key="btn_lpo", use_container_width=True):
            st.session_state.module = "lpo"
            st.rerun()
   
    st.markdown("<br>", unsafe_allow_html=True)
   
    st.markdown("### Account & Users")
    left, center, right = st.columns([1, 2.4, 1])
   
    with center:
        tab1, tab2, tab3 = st.tabs(["👤 My Account", "👥 Users", "🔑 Admin Panel"])
       
        with tab1:
            st.markdown("#### Update Username or Password")
            with st.form("update_account"):
                st.write(f"Current username: **{st.session_state.username}**")
                new_username = st.text_input("New Username (leave blank to keep current)")
                current_pw = st.text_input("Current Password", type="password")
                new_pw = st.text_input("New Password (leave blank to keep current)", type="password")
                confirm_pw = st.text_input("Confirm New Password", type="password")
                
                if st.form_submit_button("Save Changes", use_container_width=True):
                    user = st.session_state.username
                    if st.session_state.users.get(user) != current_pw:
                        st.error("Current password is incorrect")
                    else:
                        if new_pw:
                            if new_pw != confirm_pw:
                                st.error("New passwords do not match")
                            elif not is_strong_password(new_pw):
                                st.error("Password must contain letters and numbers (min 6 characters)")
                            else:
                                st.session_state.users[user] = new_pw
                                st.success("Password updated successfully!")
                        if new_username and new_username != user:
                            if new_username in st.session_state.users:
                                st.error("That username is already taken")
                            else:
                                st.session_state.users[new_username] = st.session_state.users.pop(user)
                                st.session_state.username = new_username
                                st.success(f"Username changed to **{new_username}**")
                                st.rerun()
        
        with tab2:
            st.markdown("#### Registered Users")
            for user in list(st.session_state.users.keys()):
                if user == st.session_state.username:
                    st.markdown(f"""
                    <div style="padding:10px 15px; background:#fee2e2; border-radius:10px; margin-bottom:8px; color:#1f2937 !important;">
                        <span class="user-badge">YOU</span> &nbsp; <b>{user}</b>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="padding:10px 15px; background:#f3f4f6; border-radius:10px; margin-bottom:8px; color:#1f2937 !important;">
                        <b>{user}</b>
                    </div>
                    """, unsafe_allow_html=True)
        
        with tab3:
            if st.session_state.username != "Administrator":
                st.warning("Only the Administrator can access this panel.")
            else:
                st.markdown("#### Admin Panel")
                
                st.markdown("##### Pending Password Reset Requests")
                if not st.session_state.pending_resets:
                    st.info("No pending reset requests.")
                else:
                    for user in st.session_state.pending_resets[:]:
                        col_a, col_b = st.columns([3, 1])
                        with col_a:
                            st.write(f"**{user}** requested a password reset")
                        with col_b:
                            if st.button("Clear", key=f"clear_{user}"):
                                st.session_state.pending_resets.remove(user)
                                st.rerun()
                
                st.markdown("---")
                st.markdown("##### Reset Any User Password")
                with st.form("admin_reset_form"):
                    target_user = st.selectbox("Select user", options=list(st.session_state.users.keys()))
                    new_password = st.text_input("New Password", type="password")
                    confirm_new = st.text_input("Confirm New Password", type="password")
                    if st.form_submit_button("Reset Password", use_container_width=True):
                        if not new_password:
                            st.error("Please enter a new password")
                        elif new_password != confirm_new:
                            st.error("Passwords do not match")
                        elif not is_strong_password(new_password):
                            st.error("Password must contain letters and numbers (min 6 characters)")
                        else:
                            st.session_state.users[target_user] = new_password
                            if target_user in st.session_state.pending_resets:
                                st.session_state.pending_resets.remove(target_user)
                            st.success(f"Password for **{target_user}** has been reset!")
                
                st.markdown("---")
                st.markdown("##### Remove User")
                with st.form("delete_user_form"):
                    users_to_delete = [u for u in st.session_state.users.keys() if u != "Administrator"]
                    if not users_to_delete:
                        st.info("No other users to delete.")
                    else:
                        user_to_delete = st.selectbox("Select user to remove", options=users_to_delete)
                        if st.form_submit_button("Delete User", use_container_width=True):
                            del st.session_state.users[user_to_delete]
                            if user_to_delete in st.session_state.pending_resets:
                                st.session_state.pending_resets.remove(user_to_delete)
                            st.success(f"User **{user_to_delete}** has been removed.")
                            st.rerun()

# -------------------------------------------------
# CORRECTED Data Loader (matches your actual file structure)
# -------------------------------------------------
def load_and_prepare(uploaded):
    xlsx = pd.ExcelFile(uploaded)
    
    sales_sheet = next((s for s in xlsx.sheet_names if "sales" in s.lower()), None)
    stock_sheet = next((s for s in xlsx.sheet_names if "stock" in s.lower()), None)
    
    if not sales_sheet or not stock_sheet:
        return None, "Could not find both Sales and Stocks sheets."
    
    df_sales = pd.read_excel(xlsx, sheet_name=sales_sheet)
    df_stock = pd.read_excel(xlsx, sheet_name=stock_sheet)
    
    # ---------- SALES (Long format: Branch | Brand | ItemGroup | ModelNo | Total sales) ----------
    sales_cols = {str(c).lower().strip(): c for c in df_sales.columns}
    
    branch_col = next((sales_cols[k] for k in sales_cols if "branch" in k), None)
    brand_col  = next((sales_cols[k] for k in sales_cols if "brand" in k), None)
    group_col  = next((sales_cols[k] for k in sales_cols if "group" in k), None)
    model_col  = next((sales_cols[k] for k in sales_cols if "model" in k), None)
    sales_col  = next((sales_cols[k] for k in sales_cols if "sale" in k or "total" in k), None)
    
    if not all([branch_col, brand_col, model_col, sales_col]):
        return None, f"Sales sheet missing columns. Found: {list(df_sales.columns)}"
    
    sales_agg = df_sales[[branch_col, brand_col, group_col, model_col, sales_col]].copy()
    sales_agg.columns = ["Branch", "Brand", "ItemGroup1", "Model No", "Total_Sold"]
    
    sales_agg["Total_Sold"] = pd.to_numeric(sales_agg["Total_Sold"], errors="coerce").fillna(0)
    sales_agg["Branch"] = sales_agg["Branch"].astype(str).str.strip()
    sales_agg["Brand"] = sales_agg["Brand"].astype(str).str.strip()
    sales_agg["ItemGroup1"] = sales_agg["ItemGroup1"].astype(str).str.strip()
    sales_agg["Model No"] = sales_agg["Model No"].astype(str).str.strip()
    sales_agg["Monthly_Avg"] = (sales_agg["Total_Sold"] / 8).round(2)
    
    sales_agg["Product_Key"] = (
        sales_agg["Brand"] + " | " + 
        sales_agg["ItemGroup1"] + " | " + 
        sales_agg["Model No"]
    )
    
    # ---------- STOCKS (Wide format) ----------
    stock_cols = {str(c).lower().strip(): c for c in df_stock.columns}
    
    s_brand = next((stock_cols[k] for k in stock_cols if "brand" in k), None)
    s_group = next((stock_cols[k] for k in stock_cols if "group" in k), None)
    s_model = next((stock_cols[k] for k in stock_cols if "model" in k), None)
    
    if not all([s_brand, s_model]):
        return None, f"Stocks sheet missing columns. Found: {list(df_stock.columns)}"
    
    id_vars = [s_brand]
    if s_group: id_vars.append(s_group)
    if s_model: id_vars.append(s_model)
    
    branch_cols = [c for c in df_stock.columns if c not in id_vars]
    
    stock_long = df_stock.melt(
        id_vars=id_vars,
        value_vars=branch_cols,
        var_name="Branch",
        value_name="Current_Stock"
    )
    
    stock_long["Current_Stock"] = pd.to_numeric(stock_long["Current_Stock"], errors="coerce").fillna(0)
    stock_long["Branch"] = stock_long["Branch"].astype(str).str.strip()
    
    rename_map = {s_brand: "Brand", s_model: "Model No"}
    if s_group:
        rename_map[s_group] = "ItemGroup1"
    stock_long = stock_long.rename(columns=rename_map)
    
    if "ItemGroup1" not in stock_long.columns:
        stock_long["ItemGroup1"] = ""
    
    stock_long["Brand"] = stock_long["Brand"].astype(str).str.strip()
    stock_long["Model No"] = stock_long["Model No"].astype(str).str.strip()
    stock_long["ItemGroup1"] = stock_long["ItemGroup1"].astype(str).str.strip()
    
    stock_long["Product_Key"] = (
        stock_long["Brand"] + " | " + 
        stock_long["ItemGroup1"] + " | " + 
        stock_long["Model No"]
    )
    
    stock_agg = stock_long.groupby(["Product_Key", "Branch"], as_index=False)["Current_Stock"].sum()
    
    # ---------- Merge ----------
    df = pd.merge(
        stock_agg,
        sales_agg[["Product_Key", "Branch", "Brand", "ItemGroup1", "Model No", "Total_Sold", "Monthly_Avg"]],
        on=["Product_Key", "Branch"],
        how="outer"
    )
    
    df["Current_Stock"] = df["Current_Stock"].fillna(0)
    df["Total_Sold"] = df["Total_Sold"].fillna(0)
    df["Monthly_Avg"] = df["Monthly_Avg"].fillna(0)
    
    df["Brand"] = df["Brand"].fillna("")
    df["ItemGroup1"] = df["ItemGroup1"].fillna("")
    df["Model No"] = df["Model No"].fillna("")
    
    return df, None

# -------------------------------------------------
# MODULE 1: Transfer Hub
# -------------------------------------------------
def transfer_hub():
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown("## 🚚📦 Transfer Hub")
    with col2:
        if st.button("← Back", use_container_width=True):
            st.session_state.module = None
            st.rerun()
   
    st.markdown("---")
    uploaded = st.file_uploader("Upload Excel file (Sales + Stocks sheets)", type=["xlsx", "xls"], key="transfer_upload")
   
    if uploaded is None:
        st.info("Upload your Sales + Stocks Excel file.")
        return
   
    df, error = load_and_prepare(uploaded)
    if error:
        st.error(error)
        return
    
    st.success(f"Data loaded • {df['Product_Key'].nunique()} products • {df['Branch'].nunique()} branches")
    
    MIN_KEEP = 1
    transfers = []
    
    for product, group in df.groupby("Product_Key"):
        receivers = group[(group["Monthly_Avg"] >= 0.5) & (group["Current_Stock"] <= 3)].sort_values("Total_Sold", ascending=False)
        if len(receivers) == 0: continue
        
        receiver_branches = set(receivers["Branch"])
        donors = group[(group["Current_Stock"] >= 2) & (~group["Branch"].isin(receiver_branches))].sort_values(["Monthly_Avg", "Current_Stock"], ascending=[True, False])
        if len(donors) == 0: continue
        
        donors = donors.copy()
        donors["Available"] = (donors["Current_Stock"] - MIN_KEEP).clip(lower=0)
        
        for _, rec in receivers.iterrows():
            target = max(2, int(round(rec["Monthly_Avg"] * 2)))
            needed = max(0, target - int(rec["Current_Stock"]))
            if needed <= 0: continue
            remaining = needed
            
            for idx, don in donors.iterrows():
                if remaining <= 0: break
                if don["Monthly_Avg"] >= rec["Monthly_Avg"] * 0.75: continue
                can_give = donors.at[idx, "Available"]
                if can_give <= 0: continue
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
        report = report.sort_values(by=["Receiver qty sold period", "Donor transfer Qty"], ascending=[False, False]).reset_index(drop=True)
        st.success(f"**{len(report)}** recommendations • Total units: **{report['Donor transfer Qty'].sum()}**")
        st.dataframe(report, use_container_width=True, height=480)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            report.to_excel(writer, sheet_name="transfers", index=False)
        st.download_button("⬇️ Download Transfer Report", data=output.getvalue(),
                           file_name=f"Inter_Branch_Transfers_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

# -------------------------------------------------
# MODULE 2: Stock Health
# -------------------------------------------------
def stock_health():
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown("## ❤️ Stock Health Analyzer")
    with col2:
        if st.button("← Back", use_container_width=True, key="health_back"):
            st.session_state.module = None
            st.rerun()
    
    st.markdown("---")
    uploaded = st.file_uploader("Upload Excel file (Sales + Stocks sheets)", type=["xlsx", "xls"], key="health_upload")
    
    if uploaded is None:
        st.info("Upload your Sales + Stocks Excel file.")
        return
    
    df, error = load_and_prepare(uploaded)
    if error:
        st.error(error)
        return
    
    df["Status"] = "Healthy"
    df.loc[df["Current_Stock"] <= 0, "Status"] = "Stockout"
    df.loc[(df["Current_Stock"] > 0) & (df["Total_Sold"] == 0), "Status"] = "Dead Stock"
    df["Months_Cover"] = np.where(df["Monthly_Avg"] > 0, df["Current_Stock"] / df["Monthly_Avg"], 999)
    df.loc[(df["Status"] == "Healthy") & (df["Months_Cover"] > 4) & (df["Current_Stock"] > 5), "Status"] = "Overstock"
    df.loc[(df["Status"] == "Healthy") & (df["Months_Cover"] > 2.5) & (df["Current_Stock"] > 3), "Status"] = "Slow-moving"
    
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total SKU-Branch", f"{len(df):,}")
    k2.metric("Stockouts", f"{(df['Status']=='Stockout').sum():,}")
    k3.metric("Dead Stock", f"{(df['Status']=='Dead Stock').sum():,}")
    k4.metric("Overstock", f"{(df['Status']=='Overstock').sum():,}")
    k5.metric("Slow-moving", f"{(df['Status']=='Slow-moving').sum():,}")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🔴 Stockouts", "⚫ Dead Stock", "🟠 Overstock", "🟡 Slow-moving"])
    display_cols = ["Branch", "Brand", "ItemGroup1", "Model No", "Current_Stock", "Total_Sold", "Monthly_Avg", "Months_Cover", "Status"]
    
    with tab1:
        st.dataframe(df[df["Status"]=="Stockout"][display_cols].sort_values("Total_Sold", ascending=False), use_container_width=True, height=400)
    with tab2:
        st.dataframe(df[df["Status"]=="Dead Stock"][display_cols].sort_values("Current_Stock", ascending=False), use_container_width=True, height=400)
    with tab3:
        st.dataframe(df[df["Status"]=="Overstock"][display_cols].sort_values("Months_Cover", ascending=False), use_container_width=True, height=400)
    with tab4:
        st.dataframe(df[df["Status"]=="Slow-moving"][display_cols].sort_values("Months_Cover", ascending=False), use_container_width=True, height=400)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df[display_cols].to_excel(writer, sheet_name="Full_Health", index=False)
        df[df["Status"]=="Stockout"][display_cols].to_excel(writer, sheet_name="Stockouts", index=False)
        df[df["Status"]=="Dead Stock"][display_cols].to_excel(writer, sheet_name="Dead_Stock", index=False)
        df[df["Status"]=="Overstock"][display_cols].to_excel(writer, sheet_name="Overstock", index=False)
        df[df["Status"]=="Slow-moving"][display_cols].to_excel(writer, sheet_name="Slow_moving", index=False)
    
    st.download_button("⬇️ Download Full Stock Health Report", data=output.getvalue(),
                       file_name=f"Stock_Health_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

# -------------------------------------------------
# MODULE 3: Smart LPO
# -------------------------------------------------
def smart_lpo():
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown("## 📄📋 Smart LPO Generator")
        st.caption("LPO sheet = MIKA / SAMSUNG / ORYX / Bosch  |  Goods issue = Other brands")
    with col2:
        if st.button("← Back", use_container_width=True, key="lpo_back"):
            st.session_state.module = None
            st.rerun()
    
    st.markdown("---")
    
    uploaded = st.file_uploader("Upload Excel file (Sales + Stocks sheets)", type=["xlsx", "xls"], key="lpo_upload")
    
    if uploaded is None:
        st.info("Upload your Sales + Stocks Excel file.")
        return
    
    df, error = load_and_prepare(uploaded)
    if error:
        st.error(error)
        return
    
    # Diagnostic
    st.write("### Quick Check")
    st.write(f"Total records: **{len(df)}**")
    st.write(f"Unique Branches: **{df['Branch'].nunique()}** → {list(df['Branch'].unique())[:10]}")
    st.write(f"Unique Brands: **{df['Brand'].nunique()}** → {list(df['Brand'].dropna().unique())[:10]}")
    
    # Settings
    st.markdown("### Ordering Settings")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        target_months = st.slider("Target Months of Cover (normal items)", 0.5, 2.0, 1.0, 0.1)
    with col_b:
        min_sales_normal = st.number_input("Min Monthly Sales (normal)", 0.0, 20.0, 0.5, 0.1)
    with col_c:
        safety_days = st.number_input("Min Days of Cover (normal)", 10, 60, 30)
    
    df["Days_of_Cover"] = np.where(df["Monthly_Avg"] > 0, (df["Current_Stock"] / df["Monthly_Avg"] * 30).round(1), 999)
    
    item_group = df["ItemGroup1"].astype(str).str.upper()
    df["Is_MDA_SDA"] = item_group.str.contains("MDA|SDA", na=False)
    df["Is_Space_Consuming"] = item_group.str.contains("LDA|ELECTRONICS|BUILT-IN|BUILT IN|COMMERCIAL", na=False)
    
    brand_upper = df["Brand"].astype(str).str.upper().str.strip()
    lpo_brands = ["MIKA", "SAMSUNG", "ORYX", "BOSCH"]
    df["Is_LPO_Brand"] = brand_upper.isin(lpo_brands)
    
    st.write(f"Rows from LPO brands (MIKA/SAMSUNG/ORYX/Bosch): **{df['Is_LPO_Brand'].sum()}**")
    
    df["Target_Stock"] = (df["Monthly_Avg"] * target_months).round(0)
    
    suggested = []
    for idx, row in df.iterrows():
        order_qty = 0
        
        if row["Is_Space_Consuming"]:
            if row["Monthly_Avg"] >= 3.0 and row["Current_Stock"] <= 1:
                order_qty = 1
        elif row["Is_MDA_SDA"]:
            if row["Monthly_Avg"] >= 0.6 and row["Current_Stock"] <= 2:
                order_qty = max(1, int(round(row["Monthly_Avg"] * 1.4 - row["Current_Stock"])))
        else:
            if (row["Monthly_Avg"] >= min_sales_normal and 
                row["Days_of_Cover"] < safety_days and 
                row["Current_Stock"] < row["Target_Stock"]):
                order_qty = max(0, int(row["Target_Stock"] - row["Current_Stock"]))
        
        suggested.append(max(0, order_qty))
    
    df["Suggested_Order"] = suggested
    
    lpo = df[df["Suggested_Order"] > 0].copy()
    lpo = lpo.sort_values(["Brand", "Branch", "Suggested_Order"], ascending=[True, True, False])
    
    lpo_sheet = lpo[lpo["Is_LPO_Brand"]].copy()
    goods_issue = lpo[~lpo["Is_LPO_Brand"]].copy()
    
    st.success(f"Total recommendations: **{len(lpo)}**  |  LPO sheet: {len(lpo_sheet)}  |  Goods issue: {len(goods_issue)}")
    
    display_cols = ["Branch", "Brand", "ItemGroup1", "Model No", "Current_Stock", "Monthly_Avg", "Days_of_Cover", "Suggested_Order"]
    
    tab1, tab2 = st.tabs(["LPO (MIKA / SAMSUNG / ORYX / Bosch)", "Goods issue (Other brands)"])
    
    with tab1:
        if len(lpo_sheet) == 0:
            st.warning("No items currently qualify for the LPO sheet.")
        else:
            st.dataframe(lpo_sheet[display_cols], use_container_width=True, height=420)
    
    with tab2:
        if len(goods_issue) == 0:
            st.info("No items for Goods issue sheet.")
        else:
            st.dataframe(goods_issue[display_cols], use_container_width=True, height=420)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if len(lpo_sheet) > 0:
            lpo_sheet[display_cols].to_excel(writer, sheet_name="LPO", index=False)
        else:
            pd.DataFrame({"Message": ["No recommendations"]}).to_excel(writer, sheet_name="LPO", index=False)
        
        if len(goods_issue) > 0:
            goods_issue[display_cols].to_excel(writer, sheet_name="Goods issue", index=False)
        else:
            pd.DataFrame({"Message": ["No recommendations"]}).to_excel(writer, sheet_name="Goods issue", index=False)
    
    st.download_button(
        "⬇️ Download Smart LPO Report",
        data=output.getvalue(),
        file_name=f"Smart_LPO_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

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
