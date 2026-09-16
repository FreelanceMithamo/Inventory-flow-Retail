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
    c4, c5 = st.columns(2, gap="large")

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
    # "Supplier Product Status" (or similar) — e.g. Available / REG / New / Repl / Discontinued
    s_status = next((stock_cols[k] for k in stock_cols if "status" in k), None)

    if not all([s_brand, s_model]):
        return None, f"Stocks sheet missing columns. Found: {list(df_stock.columns)}"

    id_vars = [s_brand]
    if s_group: id_vars.append(s_group)
    if s_model: id_vars.append(s_model)
    if s_status: id_vars.append(s_status)

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

# -------------------------------------------------
# MODULE 4: Data Analysis & Insights
# -------------------------------------------------
def data_analysis():
    module_header("📊🔍 Data Analysis & Insights", "Visual inventory intelligence across all branches", "analysis_back")

    uploaded = st.file_uploader("Upload Excel file (Sales + Stocks sheets)", type=["xlsx", "xls"], key="analysis_upload")

    if uploaded is None:
        st.info("Upload your Sales + Stocks Excel file.")
        return

    df, error = load_and_prepare(uploaded)
    if error:
        st.error(error)
        return

    df = compute_status(df)

    # ---------------- KPI Row ----------------
    total_units_stock = int(df["Current_Stock"].sum())
    total_units_sold = int(df["Total_Sold"].sum())
    stockout_pct = (df["Status"] == "Stockout").mean() * 100
    dead_pct = (df["Status"] == "Dead Stock").mean() * 100

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Products", f"{df['Product_Key'].nunique():,}")
    k2.metric("Branches", f"{df['Branch'].nunique():,}")
    k3.metric("Units in Stock", f"{total_units_stock:,}")
    k4.metric("Units Sold (period)", f"{total_units_sold:,}")
    k5.metric("Stockout Rate", f"{stockout_pct:.1f}%")
    k6.metric("Dead Stock Rate", f"{dead_pct:.1f}%")

    st.markdown(
        '<div class="insight-banner">💡 Use the tabs below to explore stock health, '
        'branch performance, and the SKUs that matter most — the fast movers you can\'t '
        'afford to let go out of stock.</div>',
        unsafe_allow_html=True
    )

    total_branches_all = df["Branch"].nunique()

    (tab_overview, tab_bestsellers, tab_dead, tab_branch, tab_aging,
     tab_status_gaps, tab_replenish, tab_coverage) = st.tabs(
        ["📦 Stock Health Overview", "⭐ Best Sellers & Stockout Risk", "⚫ Dead & Slow Stock",
         "🏬 Branch Performance", "⏳ Stock Aging", "🏷️ Availability Gaps", "🔁 Replenishment Monitor",
         "📶 Branch Coverage"]
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
                color="Status",
                color_discrete_map={
                    "Healthy": "#16a34a", "Stockout": "#dc2626",
                    "Dead Stock": "#374151", "Overstock": "#ea580c", "Slow-moving": "#f59e0b"
                }
            )
            fig_pie.update_layout(margin=dict(t=60, b=10, l=10, r=10))
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            by_branch_status = df.groupby(["Branch", "Status"]).size().reset_index(name="Count")
            fig_stack = px.bar(
                by_branch_status, x="Branch", y="Count", color="Status", barmode="stack",
                title="Stock Status by Branch",
                color_discrete_map={
                    "Healthy": "#16a34a", "Stockout": "#dc2626",
                    "Dead Stock": "#374151", "Overstock": "#ea580c", "Slow-moving": "#f59e0b"
                }
            )
            fig_stack.update_layout(margin=dict(t=60, b=10, l=10, r=10), xaxis_tickangle=-35)
            st.plotly_chart(fig_stack, use_container_width=True)

    # ---- Best Sellers & Stockout Risk ----
    with tab_bestsellers:
        product_summary = df.groupby(["Product_Key", "Brand", "ItemGroup1", "Model No"], as_index=False).agg(
            Total_Sold=("Total_Sold", "sum"),
            Total_Stock=("Current_Stock", "sum"),
            Branches_Stocked=("Branch", "nunique")
        )
        product_summary["Branches_at_Stockout"] = df[df["Status"] == "Stockout"].groupby("Product_Key")["Branch"].nunique().reindex(product_summary["Product_Key"]).fillna(0).values

        top_n = st.slider("Show top N best sellers", 5, 30, 15, key="topn_bestsellers")
        top_sellers = product_summary.sort_values("Total_Sold", ascending=False).head(top_n)

        fig_top = px.bar(
            top_sellers.sort_values("Total_Sold"), x="Total_Sold", y="Model No", orientation="h",
            color="Branches_at_Stockout", color_continuous_scale="Reds",
            title=f"Top {top_n} Best-Selling SKUs (colour = branches currently stocked out)",
            hover_data=["Brand", "ItemGroup1", "Total_Stock"]
        )
        fig_top.update_layout(margin=dict(t=60, b=10, l=10, r=10))
        st.plotly_chart(fig_top, use_container_width=True)

        st.markdown("#### 🚨 Best Sellers That Can't Afford a Stockout")
        st.caption("High-selling SKUs that are currently out of stock (or nearly out) in one or more branches.")
        risk = top_sellers[top_sellers["Branches_at_Stockout"] > 0].sort_values(
            ["Branches_at_Stockout", "Total_Sold"], ascending=[False, False]
        )
        if len(risk) == 0:
            st.success("None of your top sellers are currently at risk of stockout. 🎉")
        else:
            st.dataframe(
                risk[["Brand", "ItemGroup1", "Model No", "Total_Sold", "Total_Stock", "Branches_Stocked", "Branches_at_Stockout"]],
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
            dead_df[["Branch", "Brand", "ItemGroup1", "Model No", "Current_Stock", "Total_Sold", "Months_Cover", "Status"]]
            .sort_values("Current_Stock", ascending=False),
            use_container_width=True, height=350
        )

    # ---- Branch Performance ----
    with tab_branch:
        branch_summary = df.groupby("Branch", as_index=False).agg(
            Total_Sold=("Total_Sold", "sum"),
            Current_Stock=("Current_Stock", "sum"),
            Stockouts=("Status", lambda s: (s == "Stockout").sum()),
            Dead_Stock=("Status", lambda s: (s == "Dead Stock").sum())
        ).sort_values("Total_Sold", ascending=False)

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
        aging_df = df[df["Monthly_Avg"] > 0].copy()
        aging_df["Months_Cover_Capped"] = aging_df["Months_Cover"].clip(upper=24)

        fig_hist = px.histogram(
            aging_df, x="Months_Cover_Capped", nbins=30,
            title="Distribution of Months of Cover (capped at 24 for readability)",
            color_discrete_sequence=["#0d9488"]
        )
        fig_hist.update_layout(margin=dict(t=60, b=10, l=10, r=10))
        st.plotly_chart(fig_hist, use_container_width=True)

        st.caption("SKU-branches sitting far to the right are aging heavily relative to their own sales — good candidates for the Aged Stock Transfer module.")

    # ---- Availability Gaps (active supplier-status SKUs missing from some branches) ----
    with tab_status_gaps:
        st.markdown("#### Active items with registered sales that aren't stocked in every branch")
        st.caption(
            "Filters by the 'Supplier Product Status' column on your Stocks sheet (e.g. Available / REG / New / "
            "Repl), then flags any of those items that have sold before but currently sit at zero stock in one "
            "or more branches."
        )

        known_statuses = sorted([s for s in df["Supplier_Status"].unique() if s])

        if not known_statuses:
            st.info(
                "No 'Supplier Product Status' column was detected on your Stocks sheet. Add a column with a "
                "header containing the word 'Status' (e.g. 'Supplier Product Status') listing values like "
                "Available, REG, New, Repl, Discontinued, etc. to unlock this report."
            )
        else:
            exclude_keywords = ["DISC", "EOL", "OBSOLETE", "DELIST", "STOP", "DEAD"]
            default_selected = [s for s in known_statuses if not any(k in s.upper() for k in exclude_keywords)]

            selected_status = st.multiselect(
                "Include supplier statuses", known_statuses,
                default=default_selected if default_selected else known_statuses
            )

            filtered = df[df["Supplier_Status"].isin(selected_status)]

            if len(filtered) == 0:
                st.warning("No rows match the selected supplier status.")
            else:
                prod = filtered.groupby(
                    ["Product_Key", "Brand", "ItemGroup1", "Model No", "Supplier_Status"], as_index=False
                ).agg(
                    Total_Sold=("Total_Sold", "sum"),
                    Branches_With_Stock=("Current_Stock", lambda s: int((s > 0).sum())),
                    Branches_Total=("Branch", "nunique")
                )
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
                    ["Branches_Without_Stock", "Total_Sold"], ascending=[False, False]
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
                        hover_data=["Brand", "ItemGroup1", "Total_Sold"]
                    )
                    fig_gap.update_layout(margin=dict(t=60, b=10, l=10, r=10))
                    st.plotly_chart(fig_gap, use_container_width=True)

                    st.dataframe(
                        gaps[["Brand", "ItemGroup1", "Model No", "Supplier_Status", "Total_Sold",
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
            "Flags branch-SKUs that are currently at zero stock but have registered sales (meaning they did "
            "sell through), while the same item is still available with stock in at least one other branch — "
            "a sign that branch isn't being replenished."
        )

        stock_by_product = df[df["Current_Stock"] > 0].groupby("Product_Key")["Branch"].nunique()

        candidates = df[(df["Current_Stock"] <= 0) & (df["Total_Sold"] > 0)].copy()
        candidates = candidates[candidates["Product_Key"].isin(stock_by_product.index)]
        candidates = candidates.merge(
            stock_by_product.rename("Branches_With_Stock_Elsewhere"), on="Product_Key", how="left"
        )

        if len(candidates) == 0:
            st.success("No un-replenished, sold-out branch-SKUs detected. 🎉")
        else:
            candidates = candidates.sort_values(
                ["Total_Sold", "Branches_With_Stock_Elsewhere"], ascending=[False, False]
            )

            m1, m2 = st.columns(2)
            m1.metric("Sold-Out & Un-replenished Rows", f"{len(candidates):,}")
            m2.metric("Distinct SKUs Affected", f"{candidates['Product_Key'].nunique():,}")

            fig_replenish = px.bar(
                candidates.head(20).sort_values("Total_Sold"),
                x="Total_Sold", y="Model No", orientation="h", color="Branch",
                title="Top 20 Sold-Out, Un-replenished Branch-SKUs (by units sold)",
                hover_data=["Brand", "ItemGroup1", "Branches_With_Stock_Elsewhere"]
            )
            fig_replenish.update_layout(margin=dict(t=60, b=10, l=10, r=10))
            st.plotly_chart(fig_replenish, use_container_width=True)

            display_cols = ["Branch", "Brand", "ItemGroup1", "Model No", "Supplier_Status",
                             "Total_Sold", "Branches_With_Stock_Elsewhere"]
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

# -------------------------------------------------
# MODULE 5: Aged Stock Transfer
# -------------------------------------------------
def aged_stock_transfer():
    module_header(
        "🕰️📦 Aged Stock Transfer",
        "Redeploys aged stock from slow branches to branches with strong, consistent sell-out — regardless of item group",
        "aged_back"
    )

    uploaded = st.file_uploader("Upload Excel file (Sales + Stocks sheets)", type=["xlsx", "xls"], key="aged_upload")

    if uploaded is None:
        st.info("Upload your Sales + Stocks Excel file.")
        return

    df, error = load_and_prepare(uploaded)
    if error:
        st.error(error)
        return

    df = compute_status(df)

    st.markdown("### Aging & Priority Settings")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        months_cover_threshold = st.slider(
            "Treat stock as 'aged' when Months of Cover ≥", 1.0, 12.0, 3.0, 0.5,
            help="A branch's stock for a product is considered aged if it would take this many months (or more) to sell through at that branch's own average pace."
        )
    with col_b:
        include_dead_as_aged = st.checkbox("Also treat zero-sales (dead) stock as aged", value=True)
    with col_c:
        min_keep = st.number_input("Minimum units a donor branch must keep", 0, 5, 1)

    st.caption(
        "Receivers are ranked purely by their own average monthly sell-out — a branch with strong sales but "
        "**zero current stock** is prioritized as a receiver ahead of everyone else, no matter whether the "
        "item is LDA, SDA or MDA."
    )

    # ---- Identify aged stock (potential donors) ----
    is_aged = df["Months_Cover"] >= months_cover_threshold
    if include_dead_as_aged:
        is_aged = is_aged | (df["Status"] == "Dead Stock")
    df["Is_Aged"] = is_aged & (df["Current_Stock"] > min_keep)

    transfers = []

    for product, group in df.groupby("Product_Key"):
        # Receivers: branches with zero (or near-zero) stock but real sales history for this product,
        # ranked highest-sales-first — irrespective of ItemGroup1.
        receivers = group[
            (group["Current_Stock"] <= 0) &
            (group["Monthly_Avg"] > 0)
        ].sort_values("Monthly_Avg", ascending=False)

        if len(receivers) == 0:
            continue

        receiver_branches = set(receivers["Branch"])

        donors = group[
            (group["Is_Aged"]) &
            (~group["Branch"].isin(receiver_branches))
        ].sort_values("Monthly_Avg", ascending=True).copy()  # weakest-performing branches donate first

        if len(donors) == 0:
            continue

        donors["Available"] = (donors["Current_Stock"] - min_keep).clip(lower=0)

        for _, rec in receivers.iterrows():
            needed = max(2, int(math.ceil(rec["Monthly_Avg"] * 2)))
            remaining = needed

            for idx, don in donors.iterrows():
                if remaining <= 0:
                    break
                can_give = donors.at[idx, "Available"]
                if can_give <= 0:
                    continue

                give = min(remaining, can_give)
                if give > 0:
                    transfers.append({
                        "Receiver Branch": rec["Branch"],
                        "Brand": rec.get("Brand", ""),
                        "ItemGroup1": rec.get("ItemGroup1", ""),
                        "Model No": rec.get("Model No", ""),
                        "Receiver Monthly Avg Sales": round(float(rec["Monthly_Avg"]), 2),
                        "Receiver Current Stock": int(rec["Current_Stock"]),
                        "Donor Branch": don["Branch"],
                        "Donor Months Cover (aged)": round(float(don["Months_Cover"]), 1) if don["Months_Cover"] != 999 else "Never sold",
                        "Suggested Transfer Qty": int(give)
                    })
                    donors.at[idx, "Available"] -= give
                    remaining -= give

    report = pd.DataFrame(transfers)

    if len(report) == 0:
        st.warning("No aged-stock transfers available with current settings. Try lowering the Months of Cover threshold.")
        return

    # Global priority: receivers with the strongest sales get ranked first, regardless of item group.
    report = report.sort_values(
        by=["Receiver Monthly Avg Sales", "Suggested Transfer Qty"],
        ascending=[False, False]
    ).reset_index(drop=True)
    report.insert(0, "Priority Rank", report.index + 1)

    st.success(
        f"**{len(report)}** aged-stock transfer recommendations • "
        f"Total units to move: **{report['Suggested Transfer Qty'].sum()}**"
    )

    top_receivers = report.groupby("Receiver Branch", as_index=False)["Suggested Transfer Qty"].sum().sort_values(
        "Suggested Transfer Qty", ascending=False
    )
    fig = px.bar(
        top_receivers, x="Receiver Branch", y="Suggested Transfer Qty",
        title="Aged Stock Units Recommended to Receive, by Branch",
        color_discrete_sequence=["#d97706"]
    )
    fig.update_layout(margin=dict(t=60, b=10, l=10, r=10), xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(report, use_container_width=True, height=480)

    st.download_button(
        "⬇️ Download Aged Stock Transfer Report",
        data=to_excel_bytes({"Aged_Stock_Transfers": report}),
        file_name=f"Aged_Stock_Transfers_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
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
    elif st.session_state.module == "analysis":
        data_analysis()
    elif st.session_state.module == "aged":
        aged_stock_transfer()
