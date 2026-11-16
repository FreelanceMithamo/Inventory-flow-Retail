import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
from datetime import datetime
import re
import math
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="StockFlow Retail",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------------------------
# CSS  (re-themed: deep teal / navy with amber accents)
# -------------------------------------------------
st.markdown("""
<style>
    :root {
        --primary: #0d9488;      /* teal */
        --primary-dark: #0f766e;
        --accent: #f59e0b;       /* amber */
        --danger: #dc2626;
        --success: #16a34a;
        --purple: #7c3aed;
    }

    .stApp {
        background: linear-gradient(rgba(8, 30, 38, 0.85), rgba(9, 40, 48, 0.90)),
                    url('https://images.unsplash.com/photo-1553413077-190083f2a6a5?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    #MainMenu, footer, header {visibility: hidden;}

    .login-card {
        background: rgba(255, 255, 255, 0.97);
        border-radius: 20px;
        padding: 2.2rem 2.5rem;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.45);
        border-top: 6px solid var(--primary);
        max-width: 440px;
        margin: 0 auto;
        backdrop-filter: blur(8px);
    }

    .module-card {
        background: rgba(255, 255, 255, 0.96);
        border-radius: 18px;
        padding: 1.9rem 1.5rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.28);
        border: 1px solid rgba(255,255,255,0.35);
        transition: all 0.28s ease;
        height: 100%;
        text-align: center;
        backdrop-filter: blur(6px);
    }
    .module-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 25px 35px -5px rgba(13, 148, 136, 0.35);
        border-color: #5eead4;
        background: rgba(240, 253, 250, 0.98);
    }

    .logo-circle {
        width: 80px; height: 80px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.9rem; margin: 0 auto 1.1rem auto;
    }

    .transfer  { background: #ccfbf1; color: #0d9488; }
    .health    { background: #dcfce7; color: #16a34a; }
    .lpo       { background: #ffedd5; color: #ea580c; }
    .analysis  { background: #ede9fe; color: #7c3aed; }
    .aged      { background: #fef3c7; color: #d97706; }

    .stButton > button {
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover {
        background: var(--primary-dark) !important;
    }

    /* metric cards */
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 14px;
        padding: 0.8rem 1rem;
    }
    div[data-testid="stMetricValue"] { color: #5eead4 !important; }

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
        background: #ccfbf1;
        color: #0d9488;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .insight-banner {
        background: rgba(13, 148, 136, 0.18);
        border-left: 4px solid var(--primary);
        border-radius: 10px;
        padding: 0.8rem 1.1rem;
        margin-bottom: 1rem;
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
# -------------------------------------------------
# Auth State
# -------------------------------------------------
if "users" not in st.session_state:
    st.session_state.users = {}

st.session_state.users["Administrator"] = "Jose2024"
st.session_state.users.setdefault("demo", "demo123")
st.session_state.users.setdefault("manager", "branch123")

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
            <p style="color: #99f6e4 !important; font-size: 1.1rem;">Retail Inventory Intelligence Platform</p>
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
        <span style="color:#5eead4;">{st.session_state.username}</span></h2>
        <p style="color:#e5e7eb !important;">Select a module or manage your account</p>
        """, unsafe_allow_html=True)
    with col_right:
        if st.button("Logout", use_container_width=True):
            for key in ["authenticated", "username", "module"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    st.markdown("---")

    # Row 1
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

    # Row 2
    c4, c5, c6 = st.columns(3, gap="large")

    with c4:
        st.markdown("""
        <div class="module-card">
            <div class="logo-circle analysis">📊🔍</div>
            <h3 style="margin:0.5rem 0;">Data Analysis & Insights</h3>
            <p style="color:#6b7280; font-size:0.95rem;">Visual inventory intelligence & reports</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Open Data Analysis →", key="btn_analysis", use_container_width=True):
            st.session_state.module = "analysis"
            st.rerun()

    with c5:
        st.markdown("""
        <div class="module-card">
            <div class="logo-circle aged">🕰️📦</div>
            <h3 style="margin:0.5rem 0;">Aged Stock Transfer</h3>
            <p style="color:#6b7280; font-size:0.95rem;">Redeploy aged stock to top-selling branches</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Open Aged Stock Transfer →", key="btn_aged", use_container_width=True):
            st.session_state.module = "aged"
            st.rerun()

    with c6:
        st.markdown("""
        <div class="module-card">
            <div class="logo-circle transfer">🔄🏬</div>
            <h3 style="margin:0.5rem 0;">Per Branch Transfer</h3>
            <p style="color:#6b7280; font-size:0.95rem;">Move non-sellers to branches with proven demand</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Open Per Branch Transfer →", key="btn_branch_transfer", use_container_width=True):
            st.session_state.module = "branch_transfer"
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
                    <div style="padding:10px 15px; background:#ccfbf1; border-radius:10px; margin-bottom:8px; color:#1f2937 !important;">
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
# Data Loader (excludes "Total" properly)
# -------------------------------------------------
def load_and_prepare(uploaded):
    xlsx = pd.ExcelFile(uploaded)

    sales_sheet = next((s for s in xlsx.sheet_names if "sales" in s.lower()), None)
    stock_sheet = next((s for s in xlsx.sheet_names if "stock" in s.lower()), None)

    if not sales_sheet or not stock_sheet:
        return None, "Could not find both Sales and Stocks sheets."

    df_sales = pd.read_excel(xlsx, sheet_name=sales_sheet)
    df_stock = pd.read_excel(xlsx, sheet_name=stock_sheet)

    # ---------- SALES (Long format) ----------
    sales_cols = {str(c).lower().strip(): c for c in df_sales.columns}

    # Tolerate common typos/variants for the branch column (e.g. "Banch" missing the "r").
    branch_aliases = ["branch", "banch", "brnach", "brnch", "showroom", "outlet", "store"]
    brand_col  = next((sales_cols[k] for k in sales_cols if "brand" in k), None)
    group_col  = next((sales_cols[k] for k in sales_cols if "group" in k), None)
    model_col  = next((sales_cols[k] for k in sales_cols if "model" in k), None)
    sales_col  = next((sales_cols[k] for k in sales_cols if "sale" in k or "total" in k), None)
    branch_col = next((sales_cols[k] for k in sales_cols if any(a in k for a in branch_aliases)), None)

    # Fallback: if no alias matched, use the one column that isn't Brand/Group/Model/Sales —
    # this handles unexpected spellings without giving up entirely.
    if not branch_col:
        used = {brand_col, group_col, model_col, sales_col}
        leftover = [sales_cols[k] for k in sales_cols if sales_cols[k] not in used]
        if len(leftover) == 1:
            branch_col = leftover[0]

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
    # "Supplier Product Status" (or similar) — e.g. Available / REG / New / Repl / Discontinued
    s_status = next((stock_cols[k] for k in stock_cols if "status" in k), None)
    # "WarehouseType" (or similar) — e.g. Sellable Display / Non-Sellable Display. This is a
    # product/row attribute, NOT a branch, so it must be excluded from the branch columns below.
    s_wtype = next((stock_cols[k] for k in stock_cols if "warehouse" in k or "display" in k), None)

    if not all([s_brand, s_model]):
        return None, f"Stocks sheet missing columns. Found: {list(df_stock.columns)}"

    id_vars = [s_brand]
    if s_group: id_vars.append(s_group)
    if s_model: id_vars.append(s_model)
    if s_status: id_vars.append(s_status)
    if s_wtype: id_vars.append(s_wtype)

    # CRITICAL FIX: Exclude any column that contains "total"
    branch_cols = [
        c for c in df_stock.columns
        if c not in id_vars
        and "total" not in str(c).lower()
        and not str(c).lower().startswith("unnamed")
    ]

    stock_long = df_stock.melt(
        id_vars=id_vars,
        value_vars=branch_cols,
        var_name="Branch",
        value_name="Current_Stock"
    )

    stock_long["Current_Stock"] = pd.to_numeric(stock_long["Current_Stock"], errors="coerce").fillna(0)
    stock_long["Branch"] = stock_long["Branch"].astype(str).str.strip()

    # Extra safety: remove any remaining "Total" rows
    stock_long = stock_long[~stock_long["Branch"].str.lower().str.contains("total", na=False)]

    rename_map = {s_brand: "Brand", s_model: "Model No"}
    if s_group:
        rename_map[s_group] = "ItemGroup1"
    if s_status:
        rename_map[s_status] = "Supplier_Status"
    stock_long = stock_long.rename(columns=rename_map)

    if "ItemGroup1" not in stock_long.columns:
        stock_long["ItemGroup1"] = ""
    if "Supplier_Status" not in stock_long.columns:
        stock_long["Supplier_Status"] = ""

    stock_long["Brand"] = stock_long["Brand"].astype(str).str.strip()
    stock_long["Model No"] = stock_long["Model No"].astype(str).str.strip()
    stock_long["ItemGroup1"] = stock_long["ItemGroup1"].astype(str).str.strip()
    stock_long["Supplier_Status"] = stock_long["Supplier_Status"].astype(str).str.strip()
    stock_long.loc[stock_long["Supplier_Status"].str.lower().isin(["nan", "none"]), "Supplier_Status"] = ""

    stock_long["Product_Key"] = (
        stock_long["Brand"] + " | " +
        stock_long["ItemGroup1"] + " | " +
        stock_long["Model No"]
    )

    # Supplier_Status is a product-level attribute (not branch-level), so it should be
    # constant per Product_Key — take the first non-blank value seen.
    stock_agg = stock_long.groupby(
        ["Product_Key", "Branch", "Brand", "ItemGroup1", "Model No"],
        as_index=False
    ).agg(
        Current_Stock=("Current_Stock", "sum"),
        Supplier_Status=("Supplier_Status", lambda s: next((v for v in s if v), ""))
    )

    # ---------- Merge ----------
    df = pd.merge(
        stock_agg,
        sales_agg[["Product_Key", "Branch", "Total_Sold", "Monthly_Avg"]],
        on=["Product_Key", "Branch"],
        how="outer"
    )

    df["Current_Stock"] = df["Current_Stock"].fillna(0)
    df["Total_Sold"] = df["Total_Sold"].fillna(0)
    df["Monthly_Avg"] = df["Monthly_Avg"].fillna(0)
    df["Supplier_Status"] = df["Supplier_Status"].fillna("").astype(str).str.strip()

    # Recover product info if missing
    mask = (df["Brand"].isna()) | (df["Brand"] == "")
    if mask.any():
        recovered = df.loc[mask, "Product_Key"].str.split(" \\| ", expand=True)
        if recovered.shape[1] >= 3:
            df.loc[mask, "Brand"] = recovered[0]
            df.loc[mask, "ItemGroup1"] = recovered[1]
            df.loc[mask, "Model No"] = recovered[2]

    df["Brand"] = df["Brand"].fillna("").astype(str)
    df["ItemGroup1"] = df["ItemGroup1"].fillna("").astype(str)
    df["Model No"] = df["Model No"].fillna("").astype(str)

    # Final safety: remove any "Total" branch
    df = df[~df["Branch"].str.lower().str.contains("total", na=False)]

    return df, None

# -------------------------------------------------
# Shared helper: stock health status + months of cover
# -------------------------------------------------
def compute_status(df):
    df = df.copy()
    df["Status"] = "Healthy"
    df.loc[df["Current_Stock"] <= 0, "Status"] = "Stockout"
    df.loc[(df["Current_Stock"] > 0) & (df["Total_Sold"] == 0), "Status"] = "Dead Stock"

    df["Months_Cover"] = np.where(df["Monthly_Avg"] > 0, df["Current_Stock"] / df["Monthly_Avg"], 999)
    df.loc[(df["Status"] == "Healthy") & (df["Months_Cover"] > 4) & (df["Current_Stock"] > 5), "Status"] = "Overstock"
    df.loc[(df["Status"] == "Healthy") & (df["Months_Cover"] > 2.5) & (df["Current_Stock"] > 3), "Status"] = "Slow-moving"
    return df

def to_excel_bytes(sheet_dict):
    """sheet_dict: {sheet_name: dataframe}"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, frame in sheet_dict.items():
            if frame is None or len(frame) == 0:
                pd.DataFrame({"Message": ["No records"]}).to_excel(writer, sheet_name=name[:31], index=False)
            else:
                frame.to_excel(writer, sheet_name=name[:31], index=False)
    return output.getvalue()

def module_header(title, caption, back_key):
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"## {title}")
        if caption:
            st.caption(caption)
    with col2:
        if st.button("← Back", use_container_width=True, key=back_key):
            st.session_state.module = None
            st.rerun()
    st.markdown("---")

# -------------------------------------------------
# MODULE 1: Transfer Hub
# -------------------------------------------------
def transfer_hub():
    module_header("🚚📦 Transfer Hub", "Inter-branch transfer recommendations", "transfer_back")

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

        st.success(f"**{len(report)}** recommendations • Total units: **{report['Donor transfer Qty'].sum()}**")
        st.dataframe(report, use_container_width=True, height=480)

        st.download_button(
            "⬇️ Download Transfer Report",
            data=to_excel_bytes({"transfers": report}),
            file_name=f"Inter_Branch_Transfers_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# -------------------------------------------------
# MODULE 2: Stock Health
# -------------------------------------------------
def stock_health():
    module_header("❤️ Stock Health Analyzer", None, "health_back")

    uploaded = st.file_uploader("Upload Excel file (Sales + Stocks sheets)", type=["xlsx", "xls"], key="health_upload")

    if uploaded is None:
        st.info("Upload your Sales + Stocks Excel file.")
        return

    df, error = load_and_prepare(uploaded)
    if error:
        st.error(error)
        return

    df = compute_status(df)

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total SKU-Branch", f"{len(df):,}")
    k2.metric("Stockouts", f"{(df['Status']=='Stockout').sum():,}")
    k3.metric("Dead Stock", f"{(df['Status']=='Dead Stock').sum():,}")
    k4.metric("Overstock", f"{(df['Status']=='Overstock').sum():,}")
    k5.metric("Slow-moving", f"{(df['Status']=='Slow-moving').sum():,}")

    display_cols = [
        "Branch", "Brand", "ItemGroup1", "Model No",
        "Current_Stock", "Total_Sold", "Monthly_Avg", "Months_Cover", "Status"
    ]

    tab1, tab2, tab3, tab4 = st.tabs(["🔴 Stockouts", "⚫ Dead Stock", "🟠 Overstock", "🟡 Slow-moving"])

    with tab1:
        st.dataframe(df[df["Status"]=="Stockout"][display_cols].sort_values("Total_Sold", ascending=False), use_container_width=True, height=400)
    with tab2:
        st.dataframe(df[df["Status"]=="Dead Stock"][display_cols].sort_values("Current_Stock", ascending=False), use_container_width=True, height=400)
    with tab3:
        st.dataframe(df[df["Status"]=="Overstock"][display_cols].sort_values("Months_Cover", ascending=False), use_container_width=True, height=400)
    with tab4:
        st.dataframe(df[df["Status"]=="Slow-moving"][display_cols].sort_values("Months_Cover", ascending=False), use_container_width=True, height=400)

    st.download_button(
        "⬇️ Download Full Stock Health Report",
        data=to_excel_bytes({
            "Full_Health": df[display_cols],
            "Stockouts": df[df["Status"]=="Stockout"][display_cols],
            "Dead_Stock": df[df["Status"]=="Dead Stock"][display_cols],
            "Overstock": df[df["Status"]=="Overstock"][display_cols],
            "Slow_moving": df[df["Status"]=="Slow-moving"][display_cols],
        }),
        file_name=f"Stock_Health_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

# -------------------------------------------------
# MODULE 3: Smart LPO  (now with Safety Stock + Reorder Level)
# -------------------------------------------------
def smart_lpo():
    module_header("📄📋 Smart LPO Generator", "3 Sheets: LPO | Goods issue | Space Consuming", "lpo_back")

    uploaded = st.file_uploader("Upload Excel file (Sales + Stocks sheets)", type=["xlsx", "xls"], key="lpo_upload")

    if uploaded is None:
        st.info("Upload your Sales + Stocks Excel file.")
        return

    df, error = load_and_prepare(uploaded)
    if error:
        st.error(error)
        return

    st.write("### Quick Check")
    st.write(f"Total records: **{len(df)}** | Branches: **{df['Branch'].nunique()}**")

    st.markdown("### Ordering Settings")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        target_months = st.slider("Target Months of Cover (normal)", 0.5, 2.0, 1.0, 0.1)
    with col_b:
        min_sales_normal = st.number_input("Min Monthly Sales (normal)", 0.0, 20.0, 0.5, 0.1)
    with col_c:
        safety_days = st.number_input("Min Days of Cover (normal)", 10, 60, 30)

    col_d, col_e = st.columns(2)
    with col_d:
        lead_time_days = st.number_input(
            "Supplier Lead Time (days)", min_value=1, max_value=120, value=21,
            help="Average time between placing an order and receiving stock. Used to compute the Reorder Level."
        )
    with col_e:
        service_buffer_days = st.number_input(
            "Extra Safety Buffer (days)", min_value=0, max_value=60, value=7,
            help="Extra cushion on top of lead time to protect against demand spikes or supplier delays."
        )

    df["Days_of_Cover"] = np.where(df["Monthly_Avg"] > 0, (df["Current_Stock"] / df["Monthly_Avg"] * 30).round(1), 999)

    item_group = df["ItemGroup1"].astype(str).str.upper()
    df["Is_MDA_SDA"] = item_group.str.contains("MDA|SDA", na=False)
    df["Is_Space_Consuming"] = item_group.str.contains("LDA|ELECTRONICS|BUILT-IN|BUILT IN|COMMERCIAL", na=False)

    brand_upper = df["Brand"].astype(str).str.upper().str.strip()
    lpo_brands = ["MIKA", "SAMSUNG", "ORYX", "BOSCH"]
    df["Is_LPO_Brand"] = brand_upper.isin(lpo_brands)

    df["Target_Stock"] = (df["Monthly_Avg"] * target_months).round(0)

    # ---- NEW: Safety Stock & Reorder Level ----
    # Safety Stock covers the "extra safety buffer" days of demand.
    daily_avg = df["Monthly_Avg"] / 30.0
    df["Safety_Stock"] = daily_avg.apply(lambda x: math.ceil(x * service_buffer_days) if x > 0 else 0)
    # Reorder Level = expected demand during lead time + safety stock.
    df["Reorder_Level"] = (daily_avg * lead_time_days).apply(lambda x: math.ceil(x)) + df["Safety_Stock"]
    # Also respect the existing "Min Days of Cover" floor used elsewhere in the sheet.
    min_cover_units = daily_avg.apply(lambda x: math.ceil(x * safety_days) if x > 0 else 0)
    df["Safety_Stock"] = np.maximum(df["Safety_Stock"], 0)
    df["Reorder_Level"] = np.maximum(df["Reorder_Level"], min_cover_units)

    suggested = []
    for idx, row in df.iterrows():
        order_qty = 0

        if row["Is_Space_Consuming"]:
            if row["Total_Sold"] >= 3 and row["Current_Stock"] <= 1:
                order_qty = 1
        elif row["Is_MDA_SDA"]:
            if row["Monthly_Avg"] >= 0.6 and row["Current_Stock"] <= 2:
                order_qty = max(1, int(round(row["Monthly_Avg"] * 1.4 - row["Current_Stock"])))
        else:
            if (row["Monthly_Avg"] >= min_sales_normal and
                row["Days_of_Cover"] < safety_days and
                row["Current_Stock"] < row["Target_Stock"]):
                order_qty = max(0, int(row["Target_Stock"] - row["Current_Stock"]))

        # If stock has fallen at/below the computed reorder level, make sure we order
        # at least enough to bring it back up to the reorder level.
        if row["Current_Stock"] <= row["Reorder_Level"] and row["Monthly_Avg"] > 0:
            top_up = max(0, int(row["Reorder_Level"] - row["Current_Stock"]))
            order_qty = max(order_qty, top_up)

        suggested.append(max(0, order_qty))

    df["Suggested_Order"] = suggested

    lpo = df[df["Suggested_Order"] > 0].copy()
    lpo = lpo.sort_values(["Brand", "Branch", "Suggested_Order"], ascending=[True, True, False])

    space_consuming = lpo[lpo["Is_Space_Consuming"]].copy()
    lpo_sheet = lpo[(lpo["Is_LPO_Brand"]) & (~lpo["Is_Space_Consuming"])].copy()
    goods_issue = lpo[(~lpo["Is_LPO_Brand"]) & (~lpo["Is_Space_Consuming"])].copy()

    st.success(f"Total: **{len(lpo)}** | LPO: {len(lpo_sheet)} | Goods issue: {len(goods_issue)} | Space Consuming: {len(space_consuming)}")

    display_cols = [
        "Branch", "Brand", "ItemGroup1", "Model No", "Current_Stock", "Monthly_Avg",
        "Days_of_Cover", "Safety_Stock", "Reorder_Level", "Suggested_Order"
    ]

    tab1, tab2, tab3 = st.tabs([
        "LPO (MIKA / SAMSUNG / ORYX / Bosch)",
        "Goods issue (Other brands)",
        "Space Consuming (LDA / Electronics / Built-in / Commercial)"
    ])

    with tab1:
        if len(lpo_sheet) == 0:
            st.info("No items for LPO sheet.")
        else:
            st.dataframe(lpo_sheet[display_cols], use_container_width=True, height=400)

    with tab2:
        if len(goods_issue) == 0:
            st.info("No items for Goods issue sheet.")
        else:
            st.dataframe(goods_issue[display_cols], use_container_width=True, height=400)

    with tab3:
        if len(space_consuming) == 0:
            st.info("No Space Consuming items need ordering.")
        else:
            st.dataframe(space_consuming[display_cols], use_container_width=True, height=400)

    st.download_button(
        "⬇️ Download Smart LPO Report (3 Sheets)",
        data=to_excel_bytes({
            "LPO": lpo_sheet[display_cols],
            "Goods issue": goods_issue[display_cols],
            "Space Consuming": space_consuming[display_cols],
        }),
        file_name=f"Smart_LPO_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
# ==========================================================================
#  DATA ANALYSIS & INSIGHTS - single-section replacement
#  Paste this whole block over your old data_analysis() function.
#  Keep your existing: st, px, datetime, module_header, to_excel_bytes.
#  Everything new is prefixed de_ / DE_ so it cannot clash with your other modules.
#  Your old load_and_prepare / compute_status stay untouched (other modules use them).
# ==========================================================================
import re
from io import BytesIO
import numpy as np
import pandas as pd

# ------------------------------ SETTINGS ----------------------------------
DE_ALIVE_RATIO = 0.5          # other branches must sell >= 50% of their normal for a quiet month to count as a stockout
DE_LOW_FRACTION = 0.25        # a branch month below 25% of its own normal (while others are healthy) = partial stockout
DE_PROMO_RATIO = 1.5          # a network-wide month >= 1.5x normal AND statistically unusual = promo / event month
DE_BULK_SIGMA = 3.0           # one-off branch month above median + 3 robust sigmas = bulk / project sale (capped)
DE_MIN_BRANCHES_FOR_PROMO = 3 # need at least 3 branches selling the item to call a promo month
DE_MIN_MONTHS_FOR_SPIKES = 4  # need at least 4 months of history before promo / bulk detection switches on
DE_OVERSTOCK_MONTHS = 6       # stock cover above this = Overstock
DE_SLOW_UNITS_PER_MONTH = 0.5 # clean average below this = Slow-moving
DE_EOL_WORDS = ["EOL", "DISC", "OBSOLETE", "DELIST", "STOP", "DEAD", "PHASE", "NLA", "RUN DOWN", "RUN-DOWN",
             "END OF LIFE", "NO LONGER"]

DE_STATUS_COLORS = {
    "Healthy": "#16a34a", "Stockout": "#dc2626", "Dead Stock": "#374151", "Overstock": "#ea580c",
    "Slow-moving": "#f59e0b", "EOL / Run-down": "#6b7280", "No Stock / No Demand": "#cbd5e1",
}

# ------------------------------ COLUMN FINDING ----------------------------
DE_KEY_BRANCH = ["branch", "store", "outlet", "shop", "location", "site"]
DE_KEY_MODEL = ["model no", "modelno", "model number", "model", "item code", "sku", "product code", "material", "code"]
DE_KEY_BRAND = ["brand", "make", "manufacturer"]
DE_KEY_GROUP = ["itemgroup1", "item group 1", "item group", "itemgroup", "product group", "category", "group"]
DE_KEY_STATUS = ["supplier product status", "product status", "supplier status", "item status", "status"]
DE_STATUS_TOKENS = ["REG", "EOL", "DISC", "NEW", "REPL", "AVAIL", "SAMPLE", "OBSOLETE", "ACTIVE", "DELIST", "PHASE"]
DE_KEY_QTY = ["current stock", "stock on hand", "on hand", "soh", "quantity", "qty", "balance", "units", "stock"]
DE_AVG_STRICT = ["avg", "average", "mean", "per month", "grand"]      # always an average column
DE_AVG_SOFT = ["total", "sum", "monthly", "ytd"]                      # only if the header is not itself a month
DE_AVG_WORDS = DE_AVG_STRICT + DE_AVG_SOFT
DE_HEADER_WORDS = ["branch", "store", "model", "brand", "group", "stock", "status", "qty", "quantity", "item", "code", "sku"]


def de_clean(c):
    return re.sub(r"[^a-z0-9 ]", " ", str(c).lower()).strip()


def de_pick(cols, options, used=()):
    low = {c: de_clean(c) for c in cols if c not in used}
    for o in options:
        for c, l in low.items():
            if l == o:
                return c
    for o in options:
        for c, l in low.items():
            if o in l:
                return c
    return None


def de_label(c):
    if isinstance(c, (pd.Timestamp,)) or hasattr(c, "strftime"):
        return c.strftime("%b-%y")
    return str(c).strip()


def de_read(xl, sheet):
    raw = xl.parse(sheet, header=None, dtype=object)
    best, score = 0, -1
    for i in range(min(15, len(raw))):
        s = sum(isinstance(c, str) and any(w in c.lower() for w in DE_HEADER_WORDS) for c in raw.iloc[i])
        if s > score:
            best, score = i, s
    df = raw.iloc[best + 1:].copy()
    labels, seen = [], {}
    for c in raw.iloc[best]:
        l = de_label(c)
        seen[l] = seen.get(l, 0) + 1
        labels.append(l if seen[l] == 1 else f"{l}_{seen[l]}")
    df.columns = labels
    df = df.loc[:, [c for c in df.columns if c and c.lower() != "nan"]]
    return df.dropna(how="all")


def de_find_sheets(xl):
    names = xl.sheet_names
    sales = [n for n in names if "sale" in n.lower()]
    stock = [n for n in names if ("stock" in n.lower() or "inventory" in n.lower()) and "supplier" not in n.lower()]
    if sales and stock:
        return sales[0], stock[0]
    if len(names) >= 2:
        return names[0], names[1]
    raise ValueError("The workbook needs a Sales sheet and a Stocks sheet.")


DE_MONTH_RE = re.compile(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\b")
DE__BLANKS = ["", "-", "\u2013", "\u2014", "nan", "NaN", "None"]


def de_num_info(s):
    """Tolerant numeric read: '1,234' -> 1234; blank, '-' and None count as blank (= no sales), not as text."""
    if s.dtype == object:
        t = s.astype(str).str.replace(",", "", regex=False).str.strip()
        blank = t.isin(DE__BLANKS) | s.isna()
        v = pd.to_numeric(t.where(~blank), errors="coerce")
    else:
        blank = s.isna()
        v = pd.to_numeric(s, errors="coerce")
    nonblank = int((~blank).sum())
    return v, blank, (v.notna().sum() / nonblank if nonblank else 0.0), nonblank


def de_num(s):
    return de_num_info(s)[0]


def de_month_cols(df, id_cols, force=()):
    """Returns (month columns left-to-right, diagnostics table explaining every other column)."""
    cands, diag = [], []
    force = set(force)
    for c in df.columns:
        l = de_clean(c)
        if c in id_cols:
            diag.append((c, "no", "identifier column (branch / model / brand / group)")); continue
        if c in force:
            cands.append(c); diag.append((c, "yes", "forced by you")); continue
        looks_month = bool(DE_MONTH_RE.search(l))
        if any(w in l for w in DE_AVG_STRICT) or (any(w in l for w in DE_AVG_SOFT) and not looks_month):
            diag.append((c, "no", "looks like an average / total column")); continue
        _, blank, share, nonblank = de_num_info(df[c])
        if nonblank == 0:
            if looks_month:
                cands.append(c); diag.append((c, "yes", "month header, no sales in it (all blank = 0)"))
            else:
                diag.append((c, "no", "empty column"))
        elif share >= 0.9:
            cands.append(c); diag.append((c, "yes", "month column (blank / '-' cells counted as 0)"))
        else:
            diag.append((c, "no", f"mostly text ({share:.0%} numeric) - if this is a month, add it under 'force'"))
    # drop a trailing column that is just the old "monthly average" (row-mean of the others, mostly decimals)
    if len(cands) >= 3 and cands[-1] not in force:
        M = df[cands[:-1]].apply(de_num).fillna(0)
        last = de_num(df[cands[-1]]).fillna(0)
        active = (M.sum(axis=1) > 0) | (last > 0)
        if active.sum() >= 20:
            close = (np.abs(M.mean(axis=1) - last) <= 0.51)[active].mean()
            decimals = ((last % 1) != 0)[active].mean()
            if close >= 0.9 and decimals >= 0.2:
                diag = [(c, "no", "dropped: equals the average of the other months") if c == cands[-1] else (c, a, r) for c, a, r in diag]
                cands = cands[:-1]
    # drop a trailing "total" column that equals the sum of the other months
    if len(cands) >= 3 and cands[-1] not in force and any(w in de_clean(cands[-1]) for w in DE_AVG_SOFT):
        M = df[cands[:-1]].apply(de_num).fillna(0)
        last = de_num(df[cands[-1]]).fillna(0)
        active = (M.sum(axis=1) > 0) | (last > 0)
        if active.sum() >= 20 and (np.abs(M.sum(axis=1) - last) <= 0.51)[active].mean() >= 0.95:
            diag = [(c, "no", "dropped: equals the total of the other months") if c == cands[-1] else (c, a, r) for c, a, r in diag]
            cands = cands[:-1]
    return cands, pd.DataFrame(diag, columns=["Column", "Used as month?", "Reason"])


def de_status_by_content(df, exclude):
    """Fallback when no header says 'status': find a low-variety text column whose values look like product statuses."""
    best, best_score = None, 0.0
    for c in df.columns:
        if c in exclude:
            continue
        col = df[c].dropna()
        if len(col) < 5 or pd.to_numeric(col, errors="coerce").notna().mean() > 0.5:
            continue
        v = col.astype(str).str.strip().str.upper()
        if v.nunique() > max(40, 0.2 * len(v)):          # statuses repeat; descriptions / codes do not
            continue
        hit = v.map(lambda t: any(k in t for k in DE_STATUS_TOKENS)).mean()
        if hit >= 0.3 and hit > best_score:
            best, best_score = c, hit
    return best


def de_find_status(df, label, exclude, status_col=None):
    if status_col and status_col in df.columns:
        return status_col, f"{label}: column '{status_col}' (chosen by you)"
    c = de_pick(df.columns, DE_KEY_STATUS, exclude)
    if c:
        return c, f"{label}: column '{c}'"
    c = de_status_by_content(df, exclude)
    if c:
        return c, f"{label}: column '{c}' (recognised by its values - header has no 'status')"
    return None, ""


def de_first(s):
    s = [x for x in s if isinstance(x, str) and x.strip() and x.strip().lower() != "nan"]
    return s[0] if s else ""


def de_is_eol_text(t):
    t = str(t).upper()
    return any(w in t for w in DE_EOL_WORDS)


# ------------------------------ CORE ANALYSIS -----------------------------
def de_analyse_product(S, stock, eol):
    """S: branches x months (units sold). Returns dict of arrays. Flags: SO stockout, NL not listed yet,
    PR promo month normalised, BK bulk/one-off capped, EN end of supply (EOL)."""
    B, T = S.shape
    net = S.sum(axis=0)
    nz = S > 0
    n_nz = nz.sum(axis=1)
    base = np.array([np.median(S[r][nz[r]]) if n_nz[r] else 0.0 for r in range(B)])
    min_nz = min(2 if T <= 4 else 3, T)
    flags = np.full((B, T), "", dtype=object)
    cens = np.zeros((B, T), dtype=bool)

    # 1) stockout / not-listed / end-of-supply months  (excluded from the average)
    for r in range(B):
        if n_nz[r] == 0:
            continue
        first_nz, last_nz = np.where(nz[r])[0].min(), np.where(nz[r])[0].max()
        trailing = np.zeros(T, bool); trailing[last_nz + 1:] = True
        if eol[r]:                                   # supply ended: trailing zeros are not lost demand
            m = trailing & (S[r] == 0)
            cens[r] |= m; flags[r, m] = "EN"
            continue
        if n_nz[r] < min_nz:
            continue
        other = net - S[r]
        pos = other[other > 0]
        alive = (other >= DE_ALIVE_RATIO * np.median(pos)) if len(pos) else np.zeros(T, bool)
        weak = (S[r] == 0) | (S[r] < DE_LOW_FRACTION * base[r])
        m = weak & alive
        if stock[r] <= 0:                            # still out of stock today: trailing zeros are lost sales
            m |= trailing & (S[r] == 0)
        lead = np.arange(T) < first_nz
        cens[r] |= m
        flags[r, m & lead] = "NL"
        flags[r, m & ~lead] = "SO"

    valid = ~cens
    adj = S.astype(float).copy()

    # 2) promo / event months: most branches lift together vs their own normal
    elig = (base > 0) & (n_nz >= 2)
    if T >= DE_MIN_MONTHS_FOR_SPIKES and elig.sum() >= DE_MIN_BRANCHES_FOR_PROMO:
        u = np.full(T, np.nan)
        for m in range(T):
            rows = elig & valid[:, m]
            if rows.sum() >= DE_MIN_BRANCHES_FOR_PROMO:
                u[m] = np.median(S[rows, m] / base[rows])
        ok = ~np.isnan(u)
        if ok.sum() >= DE_MIN_MONTHS_FOR_SPIKES:
            med = np.median(u[ok]); mad = np.median(np.abs(u[ok] - med))
            thr = max(DE_PROMO_RATIO * med, med + DE_BULK_SIGMA * 1.4826 * mad)
            for m in (np.where(ok & (u > thr))[0] if med > 0 else []):   # intermittent items: no promo logic
                hit = valid[:, m] & (S[:, m] > 0)
                adj[hit, m] = S[hit, m] * (med / u[m])
                flags[hit, m] = "PR"

    # 3) bulk / project / one-off months in a single branch (capped)
    for r in range(B):
        idx = np.where(valid[r] & (adj[r] > 0))[0]
        if len(idx) >= DE_MIN_MONTHS_FOR_SPIKES:
            vals = adj[r, idx]
            med = np.median(vals); mad = np.median(np.abs(vals - med))
            bound = max(med + DE_BULK_SIGMA * 1.4826 * mad, 2 * med, med + 2)
            over = vals > bound
            if over.any():
                adj[r, idx[over]] = bound
                for j in idx[over]:
                    if flags[r, j] == "":
                        flags[r, j] = "BK"

    avg = np.array([adj[r, valid[r]].mean() if valid[r].any() else 0.0 for r in range(B)])
    return {
        "avg": avg, "raw": S.mean(axis=1), "used": valid.sum(axis=1), "flags": flags,
    }


def de_load_and_prepare(uploaded, exclude_cols=(), status_col=None, force_months=()):
    """Returns (df, error). df is one row per Branch x Product with clean demand. Extra tables are in df.attrs."""
    try:
        xl = pd.ExcelFile(uploaded)
        sname, tname = de_find_sheets(xl)
        sales_raw, stock_raw = de_read(xl, sname), de_read(xl, tname)
    except Exception as e:
        return None, f"Could not read the workbook: {e}"

    sb, sm = de_pick(sales_raw.columns, DE_KEY_BRANCH), de_pick(sales_raw.columns, DE_KEY_MODEL)
    tb, tm = de_pick(stock_raw.columns, DE_KEY_BRANCH), de_pick(stock_raw.columns, DE_KEY_MODEL)
    if not (sb and sm):
        return None, f"Sales sheet '{sname}': could not find Branch / Model columns. Found: {list(sales_raw.columns)}"
    if not (tb and tm):
        return None, f"Stocks sheet '{tname}': could not find Branch / Model columns. Found: {list(stock_raw.columns)}"

    s_brand = de_pick(sales_raw.columns, DE_KEY_BRAND, [sb, sm])
    s_group = de_pick(sales_raw.columns, DE_KEY_GROUP, [sb, sm, s_brand])
    idc = {c for c in (sb, sm, s_brand, s_group) if c}
    months, month_diag = de_month_cols(sales_raw, idc | set(exclude_cols), force_months)
    if not months:
        return None, f"No month columns found on '{sname}'. Columns seen: {list(sales_raw.columns)}"

    # ---- sales (any number of months) ----
    M = sales_raw[months].apply(de_num).fillna(0)
    sales = pd.DataFrame({
        "Branch": sales_raw[sb].astype(str).str.strip().str.upper(),
        "Product_Key": sales_raw[sm].astype(str).str.strip().str.upper(),
        "Model No": sales_raw[sm].astype(str).str.strip(),
        "Brand": sales_raw[s_brand].astype(str).str.strip() if s_brand else "",
        "ItemGroup1": sales_raw[s_group].astype(str).str.strip() if s_group else "",
    })
    sales = pd.concat([sales, M], axis=1)
    sales = sales[~sales["Branch"].isin(["", "NAN"]) & ~sales["Product_Key"].isin(["", "NAN"])]
    agg = {"Model No": "first", "Brand": de_first, "ItemGroup1": de_first, **{m: "sum" for m in months}}
    sales = sales.groupby(["Branch", "Product_Key"], as_index=False).agg(agg)

    # ---- stock ----
    t_brand = de_pick(stock_raw.columns, DE_KEY_BRAND, [tb, tm])
    t_group = de_pick(stock_raw.columns, DE_KEY_GROUP, [tb, tm, t_brand])
    t_status, status_src = de_find_status(stock_raw, f"Stocks sheet '{tname}'", [tb, tm, t_brand, t_group], status_col)
    sup_cols = [c for c in stock_raw.columns if "supplier" in de_clean(c)]
    t_qty = de_pick(stock_raw.columns, DE_KEY_QTY, [tb, tm, t_status, *sup_cols])
    stock = pd.DataFrame({
        "Branch": stock_raw[tb].astype(str).str.strip().str.upper(),
        "Product_Key": stock_raw[tm].astype(str).str.strip().str.upper(),
        "Model No_s": stock_raw[tm].astype(str).str.strip(),
        "Brand_s": stock_raw[t_brand].astype(str).str.strip() if t_brand else "",
        "ItemGroup1_s": stock_raw[t_group].astype(str).str.strip() if t_group else "",
        "Supplier_Status": stock_raw[t_status].astype(str).str.strip() if t_status else "",
        "Current_Stock": de_num(stock_raw[t_qty]).fillna(0) if t_qty else 1,
    })
    stock = stock[~stock["Branch"].isin(["", "NAN"]) & ~stock["Product_Key"].isin(["", "NAN"])]
    stock = stock.groupby(["Branch", "Product_Key"], as_index=False).agg(
        {"Model No_s": "first", "Brand_s": de_first, "ItemGroup1_s": de_first, "Supplier_Status": de_first, "Current_Stock": "sum"})

    full = sales.merge(stock, on=["Branch", "Product_Key"], how="outer")
    full[months] = full[months].fillna(0)
    full["Current_Stock"] = full["Current_Stock"].fillna(0)
    for a, b in (("Model No", "Model No_s"), ("Brand", "Brand_s"), ("ItemGroup1", "ItemGroup1_s")):
        full[a] = full[a].where(full[a].fillna("").astype(str).str.strip() != "", full[b]).fillna("")
    full = full.drop(columns=["Model No_s", "Brand_s", "ItemGroup1_s"])
    full["Supplier_Status"] = full["Supplier_Status"].fillna("")
    from_stock_rows = int((full["Supplier_Status"] != "").sum())
    # look the status up by item code: any branch's row, then the sales sheet, then every other sheet in the workbook
    pmap = full[full["Supplier_Status"] != ""].groupby("Product_Key")["Supplier_Status"].first().to_dict()
    sources = [status_src] if status_src else []
    lookups = [(sales_raw, sm, f"Sales sheet '{sname}'", [sb, sm, s_brand, s_group])]
    for nm in [n for n in xl.sheet_names if n not in (sname, tname)]:
        ex = de_read(xl, nm)
        mc = de_pick(ex.columns, DE_KEY_MODEL, [])
        if mc:
            lookups.append((ex, mc, f"Sheet '{nm}'", [mc]))
    for df_, mc, label, excl in lookups:
        sc, src = de_find_status(df_, label, excl, status_col)
        if not sc:
            continue
        sources.append(src + " - looked up by item code")
        keys = df_[mc].astype(str).str.strip().str.upper()
        vals = df_[sc].astype(str).str.strip()
        for k, v in zip(keys, vals):
            if v and v.lower() != "nan" and k not in ("", "NAN"):
                pmap.setdefault(k, v)
    blank = full["Supplier_Status"] == ""
    full.loc[blank, "Supplier_Status"] = full.loc[blank, "Product_Key"].map(pmap).fillna("")
    filled = int((full["Supplier_Status"] != "").sum()) - from_stock_rows
    full["Is_EOL"] = full["Supplier_Status"].map(de_is_eol_text)
    full = full.reset_index(drop=True)

    # ---- clean demand, product by product ----
    Sall = full[months].to_numpy(float).clip(min=0)
    stk, eol = full["Current_Stock"].to_numpy(float), full["Is_EOL"].to_numpy(bool)
    n, T = len(full), len(months)
    avg, raw, used = np.zeros(n), np.zeros(n), np.zeros(n, int)
    flg = np.full((n, T), "", dtype=object)
    for _, pos in full.groupby("Product_Key").indices.items():
        res = de_analyse_product(Sall[pos], stk[pos], eol[pos])
        avg[pos], raw[pos], used[pos], flg[pos] = res["avg"], res["raw"], res["used"], res["flags"]

    cnt = lambda code: (flg == code).sum(axis=1)
    full["Total_Sold"] = Sall.sum(axis=1)
    full["Months_Uploaded"] = T
    full["Months_Used"] = used
    full["Stockout_Months_Excluded"] = cnt("SO")
    full["Not_Listed_Months_Excluded"] = cnt("NL")
    full["EOL_Months_Excluded"] = cnt("EN")
    full["Promo_Months_Normalised"] = cnt("PR")
    full["Bulk_Months_Capped"] = cnt("BK")
    full["Raw_Monthly_Avg"] = raw
    full["Monthly_Avg"] = avg                      # <- the clean, availability-adjusted monthly average
    full["Confidence"] = np.where(used >= 6, "High", np.where(used >= 3, "Medium", "Low"))
    notes = []
    for i in range(n):
        p = []
        if full.at[i, "Stockout_Months_Excluded"]: p.append(f"{full.at[i, 'Stockout_Months_Excluded']} stockout mth(s) excluded")
        if full.at[i, "Not_Listed_Months_Excluded"]: p.append(f"{full.at[i, 'Not_Listed_Months_Excluded']} not-yet-listed mth(s) excluded")
        if full.at[i, "EOL_Months_Excluded"]: p.append(f"{full.at[i, 'EOL_Months_Excluded']} end-of-supply mth(s) excluded")
        if full.at[i, "Promo_Months_Normalised"]: p.append(f"{full.at[i, 'Promo_Months_Normalised']} promo mth(s) normalised")
        if full.at[i, "Bulk_Months_Capped"]: p.append(f"{full.at[i, 'Bulk_Months_Capped']} bulk mth(s) capped")
        notes.append("; ".join(p))
    full["Adjustment_Note"] = notes

    # ---- tables for download / audit ----
    ids = ["Branch", "Brand", "ItemGroup1", "Model No"]
    enriched = pd.concat([
        full[ids], full[months],
        full[["Months_Uploaded", "Stockout_Months_Excluded", "Not_Listed_Months_Excluded", "Promo_Months_Normalised",
              "Bulk_Months_Capped", "Raw_Monthly_Avg", "Monthly_Avg"]].rename(columns={"Monthly_Avg": "Clean_Monthly_Avg"}),
    ], axis=1)
    enriched["Raw_Monthly_Avg"] = enriched["Raw_Monthly_Avg"].round(2)
    enriched["Clean_Monthly_Avg"] = enriched["Clean_Monthly_Avg"].round(2)
    flags_df = pd.concat([full[ids].reset_index(drop=True), pd.DataFrame(flg, columns=months)], axis=1)

    full.attrs.update({"status_source": "; ".join(sources) if sources else "",
                       "status_rows_filled_by_lookup": filled, "stock_columns": list(stock_raw.columns),
                       "months": months, "month_diagnostics": month_diag, "sales_sheet": sname, "stock_sheet": tname,
                       "enriched": enriched, "flags": flags_df})
    return full, None


def de_compute_status(df):
    d = df.copy()
    cover = np.where(d["Monthly_Avg"] > 0, d["Current_Stock"] / d["Monthly_Avg"].where(d["Monthly_Avg"] > 0, 1), np.nan)
    d["Months_Cover"] = cover
    status = np.select(
        [d["Is_EOL"],
         (d["Current_Stock"] <= 0) & (d["Monthly_Avg"] > 0),
         (d["Current_Stock"] <= 0),
         d["Total_Sold"] <= 0,
         d["Monthly_Avg"] < DE_SLOW_UNITS_PER_MONTH,
         d["Months_Cover"] > DE_OVERSTOCK_MONTHS],
        ["EOL / Run-down", "Stockout", "No Stock / No Demand", "Dead Stock", "Slow-moving", "Overstock"],
        default="Healthy")
    d["Status"] = status
    d.attrs = dict(df.attrs)
    return d


def de_month_flag_summary(flags_df, months):
    rows = []
    for m in months:
        col = flags_df[m]
        rows.append({"Month": m, "Stockout (excluded)": int((col == "SO").sum()),
                     "Not yet listed (excluded)": int((col == "NL").sum()),
                     "Promo (normalised)": int((col == "PR").sum()),
                     "Bulk (capped)": int((col == "BK").sum())})
    return pd.DataFrame(rows)


def de_build_enriched_sales_excel(meta):
    """Sales sheet as uploaded + diagnostics + Clean_Monthly_Avg at the far end, and a Flags audit sheet.
    meta = the dict saved from df.attrs right after de_load_and_prepare()."""
    enriched, flags_df = meta["enriched"], meta["flags"]
    from openpyxl.styles import Font
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as w:
        enriched.to_excel(w, sheet_name="Sales_With_Clean_Avg", index=False)
        flags_df.to_excel(w, sheet_name="Month_Flags", index=False)
        legend = pd.DataFrame({"Code": ["SO", "NL", "EN", "PR", "BK", "(blank)"],
                               "Meaning": ["Stockout month - excluded from the average (others were selling normally)",
                                           "Not listed yet - zero before the branch first sold; excluded",
                                           "End of supply (EOL/discontinued) - trailing zeros excluded",
                                           "Promo / event month - network-wide spike normalised to normal level",
                                           "Bulk / one-off sale in this branch - capped at the normal upper bound",
                                           "Normal month - used as is"]})
        legend.to_excel(w, sheet_name="Legend", index=False)
        for ws in w.book.worksheets:
            ws.freeze_panes = "E2" if ws.title != "Legend" else "A2"
            for c in ws[1]:
                c.font = Font(bold=True)
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = 14 if ws.title != "Legend" else 70
    return bio.getvalue()



# ------------------------------ ORDER & REPLENISH PLAN --------------------
def de_plan_replenishment(df, lead_days=14, safety_days=7, review_days=30, max_cover_months=4.0, min_display=1):
    """From clean monthly demand + current stock, per branch and item:
         reorder point = demand over (lead + safety) days, at least the display minimum
         order-up-to   = demand over (lead + safety + review) days
         excess        = stock above max_cover_months of demand (all stock if there is no demand)
       Shortages are filled FIRST by transferring excess from other branches, the rest is ordered.
       EOL items are never ordered; NEW (newly listed) items are never transferred out.
       Returns (plan, transfers, branch_summary)."""
    d = df.reset_index(drop=True).copy()
    avg = d["Monthly_Avg"].to_numpy(float)
    stock = d["Current_Stock"].to_numpy(float)
    eol = d["Is_EOL"].to_numpy(bool)
    is_new = d["Supplier_Status"].astype(str).str.upper().str.startswith("NEW").to_numpy()
    daily = avg / 30.0
    mn = np.where(avg > 0, min_display, 0)
    rop = np.maximum(mn, np.ceil(daily * (lead_days + safety_days)))
    target = np.maximum(rop, np.ceil(daily * (lead_days + safety_days + review_days)))
    need = np.where((avg > 0) & (stock <= rop), np.maximum(target - stock, 0), 0.0)
    keep = np.where(avg > 0, np.maximum(np.ceil(avg * max_cover_months), mn), 0)
    excess = np.where(need > 0, 0.0, np.maximum(stock - keep, 0))
    excess[is_new] = 0

    n = len(d)
    t_in, t_out = np.zeros(n), np.zeros(n)
    from_txt = [""] * n
    transfers = []
    for _, pos in d.groupby("Product_Key").indices.items():
        donors = [i for i in pos if excess[i] > 0]
        recips = [i for i in pos if need[i] > 0]
        if not donors or not recips:
            continue
        donors.sort(key=lambda i: -excess[i])
        recips.sort(key=lambda i: -avg[i])
        left = {i: excess[i] for i in donors}
        for r in recips:
            want, parts = need[r], []
            for dn in donors:
                if want <= 0:
                    break
                q = min(left[dn], want)
                if q <= 0:
                    continue
                left[dn] -= q; want -= q
                t_in[r] += q; t_out[dn] += q
                parts.append(f"{d.at[dn, 'Branch']} x{int(q)}")
                transfers.append({"Model No": d.at[r, "Model No"], "Brand": d.at[r, "Brand"],
                                  "From Branch": d.at[dn, "Branch"], "To Branch": d.at[r, "Branch"], "Qty": int(q),
                                  "Item Status": d.at[r, "Supplier_Status"]})
            from_txt[r] = "; ".join(parts)

    order = np.where(eol, 0.0, np.maximum(need - t_in, 0))
    days_cover = np.where(avg > 0, stock / np.where(avg > 0, daily, 1), np.inf)
    action, prio = [], []
    for i in range(n):
        if need[i] > 0:
            if t_in[i] >= need[i]:
                a = "TRANSFER IN"
            elif t_in[i] > 0 and order[i] > 0:
                a = "TRANSFER IN + ORDER"
            elif eol[i]:
                a = "EOL - cannot order (clear remaining stock only)"
            else:
                a = "ORDER"
            p = "1-CRITICAL" if stock[i] <= 0 else ("2-HIGH" if days_cover[i] < lead_days else "3-NORMAL")
            if eol[i]:
                p = "4-REVIEW"          # EOL is never a stockout emergency
        elif t_out[i] > 0:
            a, p = ("TRANSFER OUT (dead stock)" if avg[i] == 0 else "TRANSFER OUT (excess)"), "3-NORMAL"
        elif excess[i] > 0:
            a = "EOL - send to sellable warehouse" if eol[i] else "EXCESS - no branch needs it yet"
            p = "4-REVIEW"
        else:
            a, p = "OK", ""
        action.append(a); prio.append(p)

    plan = pd.DataFrame({
        "Branch": d["Branch"], "Brand": d["Brand"], "ItemGroup1": d["ItemGroup1"], "Model No": d["Model No"],
        "Supplier_Status": d["Supplier_Status"], "Status": d["Status"] if "Status" in d else "",
        "Clean_Monthly_Avg": np.round(avg, 2), "Current_Stock": stock.astype(int),
        "Reorder_Point": rop.astype(int), "Target_Stock": target.astype(int), "Shortfall": need.astype(int),
        "Transfer_In": t_in.astype(int), "Transfer_From": from_txt, "ORDER_QTY": order.astype(int),
        "Excess_Qty": excess.astype(int), "Transfer_Out": t_out.astype(int),
        "Action": action, "Priority": prio, "Confidence": d["Confidence"],
    })
    plan = plan[plan["Action"] != "OK"].sort_values(["Priority", "Branch", "Clean_Monthly_Avg"],
                                                      ascending=[True, True, False]).reset_index(drop=True)
    tr = pd.DataFrame(transfers, columns=["Model No", "Brand", "From Branch", "To Branch", "Qty", "Item Status"])
    tr = tr.sort_values(["To Branch", "Model No"]).reset_index(drop=True)
    summ = plan.groupby("Branch").agg(
        Lines_Needing_Action=("Action", "size"),
        Critical_Stockouts=("Priority", lambda s: int((s == "1-CRITICAL").sum())),
        Order_Units=("ORDER_QTY", "sum"), Transfer_In_Units=("Transfer_In", "sum"),
        Transfer_Out_Units=("Transfer_Out", "sum")).reset_index().sort_values("Order_Units", ascending=False)
    return plan, tr, summ


def de_build_branch_order_book(plan, transfers, summary):
    """One workbook: Summary + Transfers + one sheet per branch (ready to send to the branch)."""
    bio = BytesIO()
    from openpyxl.styles import Font
    with pd.ExcelWriter(bio, engine="openpyxl") as w:
        summary.to_excel(w, sheet_name="Summary", index=False)
        transfers.to_excel(w, sheet_name="Transfers", index=False)
        used = {"Summary", "Transfers"}
        for b, g in plan.groupby("Branch"):
            name = re.sub(r"[\\/*?:\[\]]", "", str(b))[:28] or "Branch"
            k, base = 2, name
            while name in used:
                name = f"{base[:26]}_{k}"; k += 1
            used.add(name)
            g.drop(columns=["Branch"]).to_excel(w, sheet_name=name, index=False)
        for ws in w.book.worksheets:
            ws.freeze_panes = "A2"
            for c in ws[1]:
                c.font = Font(bold=True)
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = 16
    return bio.getvalue()



def data_analysis():
    module_header("📊🔍 Data Analysis & Insights", "Visual inventory intelligence across all branches", "analysis_back")

    uploaded = st.file_uploader("Upload Excel file (Sales + Stocks sheets) - any number of months of sales",
                                type=["xlsx", "xls"], key="analysis_upload")
    if uploaded is None:
        st.info("Upload your Sales + Stocks Excel file. Sales can cover any number of months (3, 6, 12...): one column "
                "per month, oldest on the left. No monthly-average column is needed - it is calculated for you.")
        return

    with st.expander("⚙️ Month columns detected / columns to ignore", expanded=False):
        ignore_txt = st.text_input("Columns to ignore (comma-separated, e.g. Price, Cost)", key="analysis_ignore")
        status_txt = st.text_input("Supplier Product Status column name (only if it is not found automatically)",
                                   key="analysis_status_col")
        force_txt = st.text_input("Force these columns to be treated as months (comma-separated, only if a month is missed)",
                                  key="analysis_force_months")
    force_months = [c.strip() for c in force_txt.split(",") if c.strip()] if force_txt else []
    exclude_cols = [c.strip() for c in ignore_txt.split(",") if c.strip()] if ignore_txt else []

    df, error = de_load_and_prepare(uploaded, exclude_cols=exclude_cols, status_col=(status_txt.strip() or None),
                                    force_months=force_months)
    if error:
        st.error(error)
        return

    meta = dict(df.attrs)                      # keep audit tables before further processing
    months = meta["months"]
    df = de_compute_status(df)
    df.attrs = {}                              # keep the big audit tables out of every dataframe slice

    with st.expander(f"🗓️ {len(months)} month column(s) detected - click to check", expanded=len(months) <= 2):
        st.write("Months used (oldest → newest): " + ", ".join(str(m) for m in months))
        st.dataframe(meta["month_diagnostics"], use_container_width=True, height=250)
    if len(months) <= 2:
        st.warning(f"Only {len(months)} month column(s) were detected. Open the box above to see why each column was "
                   "skipped, then type the missed month headers into 'Force these columns to be treated as months'.")

    st.caption(f"Sales sheet **{meta['sales_sheet']}** · Stock sheet **{meta['stock_sheet']}** · "
               f"**{len(months)} months** detected ({months[0]} → {months[-1]}). "
               "Monthly average is availability-adjusted: stockout months excluded, promo / bulk spikes normalised, "
               "EOL / discontinued items never counted as stockouts.")
    if meta["status_source"]:
        st.caption(f"Supplier product status taken from: {meta['status_source']} "
                   f"({meta['status_rows_filled_by_lookup']:,} rows filled by item-code lookup).")

    # ---------------- KPI Row ----------------
    in_play = df[~df["Status"].isin(["EOL / Run-down", "No Stock / No Demand"])]
    total_units_stock = int(df["Current_Stock"].sum())
    total_units_sold = int(df["Total_Sold"].sum())
    clean_per_month = float(df["Monthly_Avg"].sum())
    stockout_pct = (in_play["Status"] == "Stockout").mean() * 100 if len(in_play) else 0
    dead_pct = (in_play["Status"] == "Dead Stock").mean() * 100 if len(in_play) else 0

    k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
    k1.metric("Products", f"{df['Product_Key'].nunique():,}")
    k2.metric("Branches", f"{df['Branch'].nunique():,}")
    k3.metric("Units in Stock", f"{total_units_stock:,}")
    k4.metric(f"Units Sold ({len(months)} mths)", f"{total_units_sold:,}")
    k5.metric("Clean Units / Month", f"{clean_per_month:,.0f}")
    k6.metric("Stockout Rate", f"{stockout_pct:.1f}%")
    k7.metric("Dead Stock Rate", f"{dead_pct:.1f}%")

    st.markdown(
        '<div class="insight-banner">💡 Use the tabs below to explore stock health, '
        'branch performance, and the SKUs that matter most — the fast movers you can\'t '
        'afford to let go out of stock.</div>',
        unsafe_allow_html=True
    )

    total_branches_all = df["Branch"].nunique()

    (tab_overview, tab_bestsellers, tab_dead, tab_branch, tab_aging,
     tab_status_gaps, tab_replenish, tab_coverage, tab_quality, tab_plan) = st.tabs(
        ["📦 Stock Health Overview", "⭐ Best Sellers & Stockout Risk", "⚫ Dead & Slow Stock",
         "🏬 Branch Performance", "⏳ Stock Aging", "🏷️ Availability Gaps", "🔁 Replenishment Monitor",
         "📶 Branch Coverage", "🧪 Demand Quality", "🛒 Order & Replenish"]
    )

    # ---- Overview ----
    with tab_overview:
        status_counts = df["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]

        col1, col2 = st.columns([1, 1.4])
        with col1:
            fig_pie = px.pie(
                status_counts, names="Status", values="Count", hole=0.45,
                title="Stock Status Distribution (SKU-Branch level)",
                color="Status", color_discrete_map=DE_STATUS_COLORS
            )
            fig_pie.update_layout(margin=dict(t=60, b=10, l=10, r=10))
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            by_branch_status = df.groupby(["Branch", "Status"]).size().reset_index(name="Count")
            fig_stack = px.bar(
                by_branch_status, x="Branch", y="Count", color="Status", barmode="stack",
                title="Stock Status by Branch", color_discrete_map=DE_STATUS_COLORS
            )
            fig_stack.update_layout(margin=dict(t=60, b=10, l=10, r=10), xaxis_tickangle=-35)
            st.plotly_chart(fig_stack, use_container_width=True)

    # ---- Best Sellers & Stockout Risk ----
    with tab_bestsellers:
        product_summary = df.groupby(["Product_Key", "Brand", "ItemGroup1", "Model No"], as_index=False).agg(
            Total_Sold=("Total_Sold", "sum"),
            Clean_Monthly_Avg=("Monthly_Avg", "sum"),
            Total_Stock=("Current_Stock", "sum"),
            Branches_Stocked=("Current_Stock", lambda s: int((s > 0).sum()))
        )
        product_summary["Clean_Monthly_Avg"] = product_summary["Clean_Monthly_Avg"].round(1)
        product_summary["Branches_at_Stockout"] = df[df["Status"] == "Stockout"].groupby("Product_Key")["Branch"].nunique().reindex(product_summary["Product_Key"]).fillna(0).values

        top_n = st.slider("Show top N best sellers", 5, 30, 15, key="topn_bestsellers")
        top_sellers = product_summary.sort_values("Clean_Monthly_Avg", ascending=False).head(top_n)

        fig_top = px.bar(
            top_sellers.sort_values("Clean_Monthly_Avg"), x="Clean_Monthly_Avg", y="Model No", orientation="h",
            color="Branches_at_Stockout", color_continuous_scale="Reds",
            title=f"Top {top_n} Best-Selling SKUs by clean monthly sales (colour = branches currently stocked out)",
            hover_data=["Brand", "ItemGroup1", "Total_Sold", "Total_Stock"]
        )
        fig_top.update_layout(margin=dict(t=60, b=10, l=10, r=10))
        st.plotly_chart(fig_top, use_container_width=True)

        st.markdown("#### 🚨 Best Sellers That Can't Afford a Stockout")
        st.caption("High-selling SKUs that are currently out of stock in one or more branches. "
                   "EOL / discontinued items are never listed here.")
        risk = top_sellers[top_sellers["Branches_at_Stockout"] > 0].sort_values(
            ["Branches_at_Stockout", "Clean_Monthly_Avg"], ascending=[False, False]
        )
        if len(risk) == 0:
            st.success("None of your top sellers are currently at risk of stockout. 🎉")
        else:
            st.dataframe(
                risk[["Brand", "ItemGroup1", "Model No", "Clean_Monthly_Avg", "Total_Sold", "Total_Stock",
                      "Branches_Stocked", "Branches_at_Stockout"]],
                use_container_width=True, height=350
            )
            st.download_button(
                "⬇️ Download Stockout-Risk Best Sellers",
                data=to_excel_bytes({"Risk_Best_Sellers": risk}),
                file_name=f"Best_Sellers_At_Risk_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # ---- Dead & Slow Stock ----
    with tab_dead:
        dead_df = df[df["Status"].isin(["Dead Stock", "Slow-moving"])]
        by_brand = dead_df.groupby(["Brand", "Status"], as_index=False)["Current_Stock"].sum()

        col1, col2 = st.columns(2)
        with col1:
            fig_dead_brand = px.bar(
                by_brand.sort_values("Current_Stock", ascending=False), x="Brand", y="Current_Stock", color="Status",
                title="Dead / Slow-moving Units by Brand",
                color_discrete_map={"Dead Stock": "#374151", "Slow-moving": "#f59e0b"}
            )
            fig_dead_brand.update_layout(margin=dict(t=60, b=10, l=10, r=10), xaxis_tickangle=-35)
            st.plotly_chart(fig_dead_brand, use_container_width=True)
        with col2:
            by_branch_dead = dead_df.groupby("Branch", as_index=False)["Current_Stock"].sum().sort_values("Current_Stock", ascending=False)
            fig_dead_branch = px.bar(
                by_branch_dead, x="Branch", y="Current_Stock",
                title="Dead / Slow-moving Units by Branch", color_discrete_sequence=["#7c3aed"]
            )
            fig_dead_branch.update_layout(margin=dict(t=60, b=10, l=10, r=10), xaxis_tickangle=-35)
            st.plotly_chart(fig_dead_branch, use_container_width=True)

        st.dataframe(
            dead_df[["Branch", "Brand", "ItemGroup1", "Model No", "Current_Stock", "Total_Sold", "Monthly_Avg",
                     "Months_Cover", "Status"]]
            .sort_values("Current_Stock", ascending=False),
            use_container_width=True, height=350
        )

    # ---- Branch Performance ----
    with tab_branch:
        branch_summary = df.groupby("Branch", as_index=False).agg(
            Total_Sold=("Total_Sold", "sum"),
            Clean_Monthly_Avg=("Monthly_Avg", "sum"),
            Current_Stock=("Current_Stock", "sum"),
            Stockouts=("Status", lambda s: (s == "Stockout").sum()),
            Dead_Stock=("Status", lambda s: (s == "Dead Stock").sum())
        ).sort_values("Total_Sold", ascending=False)
        branch_summary["Clean_Monthly_Avg"] = branch_summary["Clean_Monthly_Avg"].round(1)

        fig_branch_sales = px.bar(
            branch_summary, x="Branch", y="Total_Sold", title="Total Units Sold by Branch",
            color="Total_Sold", color_continuous_scale="Teal"
        )
        fig_branch_sales.update_layout(margin=dict(t=60, b=10, l=10, r=10), xaxis_tickangle=-35)
        st.plotly_chart(fig_branch_sales, use_container_width=True)

        st.dataframe(branch_summary, use_container_width=True, height=350)
        st.download_button(
            "⬇️ Download Branch Performance Summary",
            data=to_excel_bytes({"Branch_Performance": branch_summary}),
            file_name=f"Branch_Performance_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # ---- Stock Aging ----
    with tab_aging:
        aging_df = df[(df["Monthly_Avg"] > 0) & (~df["Is_EOL"])].copy()
        aging_df["Months_Cover_Capped"] = aging_df["Months_Cover"].clip(upper=24)

        fig_hist = px.histogram(
            aging_df, x="Months_Cover_Capped", nbins=30,
            title="Distribution of Months of Cover (capped at 24 for readability)",
            color_discrete_sequence=["#0d9488"]
        )
        fig_hist.update_layout(margin=dict(t=60, b=10, l=10, r=10))
        st.plotly_chart(fig_hist, use_container_width=True)

        st.caption("SKU-branches sitting far to the right are aging heavily relative to their own clean sales — "
                   "good candidates for the Aged Stock Transfer module. EOL items are shown in the "
                   "'EOL / Run-down' status instead.")

    # ---- Availability Gaps (active supplier-status SKUs missing from some branches) ----
    with tab_status_gaps:
        st.markdown("#### Active items with registered sales that aren't stocked in every branch")
        st.caption(
            "Filters by the 'Supplier Product Status' column on your Stocks sheet (e.g. Available / REG / New / "
            "Repl), then flags any of those items that have sold before but currently sit at zero stock in one "
            "or more branches. EOL / discontinued items are always left out."
        )

        known_statuses = sorted([s for s in df["Supplier_Status"].unique() if s])

        if not known_statuses:
            st.info(
                "No supplier product status could be found on any sheet (looked at the Stocks sheet, the Sales "
                "sheet and every other sheet, by header and by values). Columns seen on your Stocks sheet: "
                + ", ".join(str(c) for c in meta["stock_columns"])
                + ". Type the exact status column name in the '⚙️ Month columns detected' box at the top and it will be used."
            )
        else:
            default_selected = [s for s in known_statuses if not df.loc[df["Supplier_Status"] == s, "Is_EOL"].any()]

            selected_status = st.multiselect(
                "Include supplier statuses", known_statuses,
                default=default_selected if default_selected else known_statuses
            )

            filtered = df[df["Supplier_Status"].isin(selected_status) & (~df["Is_EOL"])]

            if len(filtered) == 0:
                st.warning("No rows match the selected supplier status.")
            else:
                prod = filtered.groupby(
                    ["Product_Key", "Brand", "ItemGroup1", "Model No", "Supplier_Status"], as_index=False
                ).agg(
                    Total_Sold=("Total_Sold", "sum"),
                    Clean_Monthly_Avg=("Monthly_Avg", "sum"),
                    Branches_With_Stock=("Current_Stock", lambda s: int((s > 0).sum())),
                    Branches_Total=("Branch", "nunique")
                )
                prod["Clean_Monthly_Avg"] = prod["Clean_Monthly_Avg"].round(1)
                prod["Branches_Without_Stock"] = prod["Branches_Total"] - prod["Branches_With_Stock"]

                missing_map = (
                    filtered[filtered["Current_Stock"] <= 0]
                    .groupby("Product_Key")["Branch"]
                    .apply(lambda s: ", ".join(sorted(set(s))))
                    .rename("Branches_Missing_Stock")
                )
                prod = prod.merge(missing_map, on="Product_Key", how="left")
                prod["Branches_Missing_Stock"] = prod["Branches_Missing_Stock"].fillna("")

                gaps = prod[(prod["Total_Sold"] > 0) & (prod["Branches_Without_Stock"] > 0)].sort_values(
                    ["Branches_Without_Stock", "Clean_Monthly_Avg"], ascending=[False, False]
                )

                m1, m2, m3 = st.columns(3)
                m1.metric("Active SKUs Selected", f"{prod['Product_Key'].nunique():,}")
                m2.metric("SKUs With Coverage Gaps", f"{gaps['Product_Key'].nunique():,}")
                m3.metric("Branch-Slots Missing Stock", f"{int(gaps['Branches_Without_Stock'].sum()):,}")

                if len(gaps) == 0:
                    st.success("All selected active SKUs with sales history are stocked in every branch. 🎉")
                else:
                    fig_gap = px.bar(
                        gaps.head(20).sort_values("Branches_Without_Stock"),
                        x="Branches_Without_Stock", y="Model No", orientation="h",
                        color="Supplier_Status",
                        title="Top 20 Active SKUs Missing From The Most Branches",
                        hover_data=["Brand", "ItemGroup1", "Total_Sold", "Clean_Monthly_Avg"]
                    )
                    fig_gap.update_layout(margin=dict(t=60, b=10, l=10, r=10))
                    st.plotly_chart(fig_gap, use_container_width=True)

                    st.dataframe(
                        gaps[["Brand", "ItemGroup1", "Model No", "Supplier_Status", "Clean_Monthly_Avg", "Total_Sold",
                              "Branches_With_Stock", "Branches_Without_Stock", "Branches_Total",
                              "Branches_Missing_Stock"]],
                        use_container_width=True, height=400
                    )
                    st.download_button(
                        "⬇️ Download Availability Gaps Report",
                        data=to_excel_bytes({"Availability_Gaps": gaps}),
                        file_name=f"Availability_Gaps_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    # ---- Replenishment Monitor ----
    with tab_replenish:
        st.markdown("#### Branches that sold out and haven't been replenished")
        st.caption(
            "Flags branch-SKUs that are currently at zero stock but have a clean monthly demand (they sold "
            "through), while the same item is still available with stock in at least one other branch — "
            "a sign that branch isn't being replenished. EOL / discontinued items are excluded."
        )

        stock_by_product = df[df["Current_Stock"] > 0].groupby("Product_Key")["Branch"].nunique()

        candidates = df[(df["Current_Stock"] <= 0) & (df["Monthly_Avg"] > 0) & (~df["Is_EOL"])].copy()
        candidates = candidates[candidates["Product_Key"].isin(stock_by_product.index)]
        candidates = candidates.merge(
            stock_by_product.rename("Branches_With_Stock_Elsewhere"), on="Product_Key", how="left"
        )
        candidates["Monthly_Avg"] = candidates["Monthly_Avg"].round(1)

        if len(candidates) == 0:
            st.success("No un-replenished, sold-out branch-SKUs detected. 🎉")
        else:
            candidates = candidates.sort_values(
                ["Monthly_Avg", "Branches_With_Stock_Elsewhere"], ascending=[False, False]
            )

            m1, m2 = st.columns(2)
            m1.metric("Sold-Out & Un-replenished Rows", f"{len(candidates):,}")
            m2.metric("Distinct SKUs Affected", f"{candidates['Product_Key'].nunique():,}")

            fig_replenish = px.bar(
                candidates.head(20).sort_values("Monthly_Avg"),
                x="Monthly_Avg", y="Model No", orientation="h", color="Branch",
                title="Top 20 Sold-Out, Un-replenished Branch-SKUs (by clean monthly sales)",
                hover_data=["Brand", "ItemGroup1", "Branches_With_Stock_Elsewhere"]
            )
            fig_replenish.update_layout(margin=dict(t=60, b=10, l=10, r=10))
            st.plotly_chart(fig_replenish, use_container_width=True)

            display_cols = ["Branch", "Brand", "ItemGroup1", "Model No", "Supplier_Status",
                            "Monthly_Avg", "Total_Sold", "Branches_With_Stock_Elsewhere"]
            st.dataframe(candidates[display_cols], use_container_width=True, height=400)
            st.download_button(
                "⬇️ Download Replenishment Monitor Report",
                data=to_excel_bytes({"Replenishment_Monitor": candidates[display_cols]}),
                file_name=f"Replenishment_Monitor_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # ---- Branch Coverage ----
    with tab_coverage:
        st.markdown("#### SKUs stocked in only a handful of branches")
        default_threshold = min(24, max(1, total_branches_all - 1))
        threshold = st.slider(
            f"Flag items stocked in fewer than N of your {total_branches_all} branches",
            1, total_branches_all, default_threshold
        )

        coverage = df.groupby(
            ["Product_Key", "Brand", "ItemGroup1", "Model No", "Supplier_Status"], as_index=False
        ).agg(
            Branches_With_Stock=("Current_Stock", lambda s: int((s > 0).sum())),
            Total_Sold=("Total_Sold", "sum")
        )
        coverage["Total_Branches"] = total_branches_all

        low_coverage = coverage[coverage["Branches_With_Stock"] < threshold].sort_values(
            "Branches_With_Stock", ascending=True
        )

        m1, m2, m3 = st.columns(3)
        m1.metric("Total SKUs", f"{coverage['Product_Key'].nunique():,}")
        m2.metric(f"SKUs Stocked in < {threshold} Branches", f"{len(low_coverage):,}")
        m3.metric("Total Branches in File", f"{total_branches_all}")

        if len(low_coverage) == 0:
            st.success(f"Every SKU is stocked in at least {threshold} branches. 🎉")
        else:
            fig_cov = px.histogram(
                coverage, x="Branches_With_Stock", nbins=total_branches_all,
                title="How Many Branches Each SKU Is Stocked In (all products)",
                color_discrete_sequence=["#0d9488"]
            )
            fig_cov.add_vline(x=threshold, line_dash="dash", line_color="#dc2626")
            fig_cov.update_layout(margin=dict(t=60, b=10, l=10, r=10))
            st.plotly_chart(fig_cov, use_container_width=True)

            st.dataframe(
                low_coverage[["Brand", "ItemGroup1", "Model No", "Supplier_Status",
                              "Branches_With_Stock", "Total_Branches", "Total_Sold"]],
                use_container_width=True, height=400
            )
            st.download_button(
                "⬇️ Download Low Branch-Coverage Report",
                data=to_excel_bytes({"Low_Branch_Coverage": low_coverage}),
                file_name=f"Low_Branch_Coverage_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # ---- Demand Quality (new): shows exactly what the engine adjusted ----
    with tab_quality:
        st.markdown("#### How the clean monthly average was built")
        st.caption(
            "Stockout months (others still selling normally) and not-yet-listed months are excluded. Network-wide "
            "promo months are normalised to normal level. One-off bulk sales in a single branch are capped. "
            "EOL / discontinued items only lose their trailing zero months and are never flagged as stockouts."
        )
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Months of sales uploaded", f"{len(months)}")
        q2.metric("Rows with stockout months excluded", f"{int((df['Stockout_Months_Excluded'] > 0).sum()):,}")
        q3.metric("Rows with promo months normalised", f"{int((df['Promo_Months_Normalised'] > 0).sum()):,}")
        q4.metric("Rows with bulk sales capped", f"{int((df['Bulk_Months_Capped'] > 0).sum()):,}")

        fs = de_month_flag_summary(meta["flags"], months)
        fs_long = fs.melt(id_vars="Month", var_name="Adjustment", value_name="Branch-SKUs")
        fig_flags = px.bar(fs_long, x="Month", y="Branch-SKUs", color="Adjustment", barmode="group",
                           title="Adjustments applied per month (count of branch-SKU cells)",
                           category_orders={"Month": months})
        fig_flags.update_layout(margin=dict(t=60, b=10, l=10, r=10))
        st.plotly_chart(fig_flags, use_container_width=True)

        top_c = (df.groupby(["Product_Key", "Model No"], as_index=False)
                   .agg(Raw=("Raw_Monthly_Avg", "sum"), Clean=("Monthly_Avg", "sum"))
                   .sort_values("Clean", ascending=False).head(20))
        top_long = top_c.melt(id_vars=["Product_Key", "Model No"], value_vars=["Raw", "Clean"],
                              var_name="Average", value_name="Units / month")
        fig_rc = px.bar(top_long, x="Model No", y="Units / month", color="Average", barmode="group",
                        title="Top 20 items: raw average vs clean average (units / month)")
        fig_rc.update_layout(margin=dict(t=60, b=10, l=10, r=10), xaxis_tickangle=-35)
        st.plotly_chart(fig_rc, use_container_width=True)

        adj = df[df["Adjustment_Note"] != ""].copy()
        adj["Change_%"] = np.where(adj["Raw_Monthly_Avg"] > 0,
                                   (adj["Monthly_Avg"] / adj["Raw_Monthly_Avg"] - 1) * 100, 0).round(0)
        adj = adj.sort_values("Change_%", key=lambda s: s.abs(), ascending=False)
        st.markdown("#### Items where the adjustment changed the average the most")
        st.dataframe(
            adj[["Branch", "Model No", "Supplier_Status", "Raw_Monthly_Avg", "Monthly_Avg", "Change_%",
                 "Months_Used", "Confidence", "Adjustment_Note"]].round(2),
            use_container_width=True, height=400
        )
        st.download_button(
            "⬇️ Download Sales Sheet With Clean Monthly Average (+ month-by-month flags)",
            data=de_build_enriched_sales_excel(meta),
            file_name=f"Sales_With_Clean_Avg_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # ---- Order & Replenish (new): what to order / move per branch from the clean history ----
    with tab_plan:
        st.markdown("#### What to order and replenish, per branch")
        st.caption(
            "Built from each item's clean monthly average and current stock. Shortages are filled first by moving "
            "excess stock from other branches; only the remainder is ordered. EOL / discontinued items are never "
            "ordered and NEW listings are never moved out."
        )
        c1, c2, c3, c4, c5 = st.columns(5)
        lead = c1.number_input("Supplier lead time (days)", 0, 180, 14, key="plan_lead")
        safety = c2.number_input("Safety days", 0, 90, 7, key="plan_safety")
        review = c3.number_input("Order cycle (days)", 1, 120, 30, key="plan_review")
        maxcov = c4.number_input("Excess above (months of cover)", 1.0, 24.0, 4.0, step=0.5, key="plan_maxcov")
        mindisp = c5.number_input("Min display qty (selling items)", 0, 5, 1, key="plan_mindisp")

        plan, transfers_df, plan_summary = de_plan_replenishment(df, lead, safety, review, maxcov, mindisp)

        if len(plan) == 0:
            st.success("Nothing to order or move with these settings. 🎉")
        else:
            sel = st.selectbox("Branch", ["All branches"] + sorted(plan["Branch"].unique()), key="plan_branch")
            view = plan if sel == "All branches" else plan[plan["Branch"] == sel]
            tview = transfers_df if sel == "All branches" else transfers_df[
                (transfers_df["From Branch"] == sel) | (transfers_df["To Branch"] == sel)]

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Lines needing action", f"{len(view):,}")
            m2.metric("Units to ORDER", f"{int(view['ORDER_QTY'].sum()):,}")
            m3.metric("Units to TRANSFER", f"{int(view['Transfer_In'].sum()):,}")
            m4.metric("Critical (out of stock, selling)", f"{int((view['Priority'] == '1-CRITICAL').sum()):,}")

            chart_df = plan_summary.head(25).melt(id_vars="Branch", value_vars=["Order_Units", "Transfer_In_Units"],
                                                  var_name="Type", value_name="Units")
            fig_plan = px.bar(chart_df, x="Branch", y="Units", color="Type", barmode="group",
                              title="Units to order vs transfer in, by branch (top 25 by order units)")
            fig_plan.update_layout(margin=dict(t=60, b=10, l=10, r=10), xaxis_tickangle=-35)
            st.plotly_chart(fig_plan, use_container_width=True)

            st.markdown("##### 🛒 Order list")
            st.dataframe(view[view["ORDER_QTY"] > 0][["Branch", "Brand", "ItemGroup1", "Model No", "Supplier_Status",
                                                      "Clean_Monthly_Avg", "Current_Stock", "Reorder_Point",
                                                      "Target_Stock", "Transfer_In", "ORDER_QTY", "Priority"]],
                         use_container_width=True, height=300)
            st.markdown("##### 🔁 Transfers (move excess stock to branches that need it)")
            st.dataframe(tview, use_container_width=True, height=250)
            st.markdown("##### 📋 Full plan")
            st.dataframe(view, use_container_width=True, height=350)
            st.markdown("##### 🏬 Branch summary")
            st.dataframe(plan_summary, use_container_width=True, height=250)

            d1, d2 = st.columns(2)
            d1.download_button(
                "⬇️ Download Order & Replenish Plan (all branches)",
                data=to_excel_bytes({"Orders": plan[plan["ORDER_QTY"] > 0], "Transfers": transfers_df,
                                     "Full_Plan": plan, "Branch_Summary": plan_summary}),
                file_name=f"Order_Replenish_Plan_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            d2.download_button(
                "⬇️ Download One Sheet Per Branch",
                data=de_build_branch_order_book(plan, transfers_df, plan_summary),
                file_name=f"Branch_Order_Sheets_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
