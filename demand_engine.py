"""
demand_engine.py
Clean demand calculation + replenishment planning for StockFlow Retail.
Used exclusively by the Data Analysis & Insights module.
"""

from __future__ import annotations

import math
import re
from io import BytesIO
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from openpyxl.styles import Font

# ---------------------------------------------------------------------------
# Tunable constants
# ---------------------------------------------------------------------------
ALIVE_RATIO = 0.5
LOW_FRACTION = 0.25
PROMO_RATIO = 1.5
BULK_SIGMA = 3.0
MIN_BRANCHES_FOR_PROMO = 3
MIN_MONTHS_FOR_SPIKES = 4
OVERSTOCK_MONTHS = 6
SLOW_UNITS_PER_MONTH = 0.5

EOL_WORDS = [
    "EOL", "DISC", "OBSOLETE", "DELIST", "STOP", "DEAD", "PHASE", "NLA",
    "RUN DOWN", "RUN-DOWN", "END OF LIFE", "NO LONGER", "DISCONTINUED",
]

STATUS_COLORS = {
    "Healthy": "#16a34a",
    "Stockout": "#dc2626",
    "Dead Stock": "#374151",
    "Overstock": "#ea580c",
    "Slow-moving": "#f59e0b",
    "EOL / Run-down": "#6b7280",
    "No Stock / No Demand": "#cbd5e1",
}

KEY_BRANCH = ["branch", "store", "outlet", "shop", "location", "site", "showroom"]
KEY_MODEL = ["model no", "modelno", "model number", "model", "item code", "sku",
             "product code", "material", "code"]
KEY_BRAND = ["brand", "make", "manufacturer"]
KEY_GROUP = ["itemgroup1", "item group 1", "item group", "itemgroup",
             "product group", "category", "group"]
KEY_STATUS = ["supplier product status", "product status", "item status",
              "supplier status", "status"]
KEY_QTY = ["current stock", "stock on hand", "on hand", "soh", "quantity",
           "qty", "balance", "units", "stock"]
AVG_WORDS = ["avg", "average", "mean", "total", "sum", "monthly", "per month", "grand"]
HEADER_WORDS = ["branch", "store", "model", "brand", "group", "stock", "status",
                "qty", "quantity", "item", "code", "sku"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _clean(c) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", str(c).lower()).strip()


def _pick(cols, options: Sequence[str], used=()) -> Optional[str]:
    low = {c: _clean(c) for c in cols if c not in used}
    for o in options:
        for c, l in low.items():
            if l == o:
                return c
    for o in options:
        for c, l in low.items():
            if o in l:
                return c
    return None


def _label(c) -> str:
    if isinstance(c, pd.Timestamp) or hasattr(c, "strftime"):
        return c.strftime("%b-%y")
    return str(c).strip()


def _first(s):
    vals = [x for x in s if isinstance(x, str) and x.strip() and x.strip().lower() != "nan"]
    return vals[0] if vals else ""


def _is_eol_text(t) -> bool:
    t = str(t).upper()
    return any(w in t for w in EOL_WORDS)


def _read_sheet(xl: pd.ExcelFile, sheet: str) -> pd.DataFrame:
    raw = xl.parse(sheet, header=None, dtype=object)
    best, score = 0, -1
    for i in range(min(15, len(raw))):
        s = sum(
            isinstance(c, str) and any(w in str(c).lower() for w in HEADER_WORDS)
            for c in raw.iloc[i]
        )
        if s > score:
            best, score = i, s
    df = raw.iloc[best + 1:].copy()
    labels, seen = [], {}
    for c in raw.iloc[best]:
        l = _label(c)
        seen[l] = seen.get(l, 0) + 1
        labels.append(l if seen[l] == 1 else f"{l}_{seen[l]}")
    df.columns = labels
    df = df.loc[:, [c for c in df.columns if c and str(c).lower() != "nan"]]
    return df.dropna(how="all")


def _find_sheets(xl: pd.ExcelFile) -> Tuple[str, str]:
    names = xl.sheet_names
    sales = [n for n in names if "sale" in n.lower()]
    stock = [
        n for n in names
        if ("stock" in n.lower() or "inventory" in n.lower()) and "supplier" not in n.lower()
    ]
    if sales and stock:
        return sales[0], stock[0]
    if len(names) >= 2:
        return names[0], names[1]
    raise ValueError("The workbook needs a Sales sheet and a Stocks sheet.")


def _month_cols(df: pd.DataFrame, id_cols, force_months: Sequence[str] = ()) -> Tuple[List[str], pd.DataFrame]:
    """Return (list of month columns, diagnostics dataframe)."""
    diagnostics = []
    cands = []
    force_set = {_clean(m) for m in force_months}

    for c in df.columns:
        cl = _clean(c)
        reason = ""
        if c in id_cols:
            reason = "id / key column"
        elif any(w in cl for w in AVG_WORDS) and cl not in force_set:
            reason = "looks like average / total"
        elif cl in force_set:
            cands.append(c)
            diagnostics.append({"Column": c, "Accepted": "Yes (forced)", "Reason": "user forced"})
            continue
        else:
            numeric_share = pd.to_numeric(df[c], errors="coerce").notna().mean()
            if numeric_share < 0.6:
                reason = f"only {numeric_share:.0%} numeric"
            else:
                cands.append(c)
                diagnostics.append({"Column": c, "Accepted": "Yes", "Reason": f"{numeric_share:.0%} numeric"})
                continue
        diagnostics.append({"Column": c, "Accepted": "No", "Reason": reason})

    # Drop trailing monthly-average column if present
    if len(cands) >= 3:
        M = df[cands[:-1]].apply(pd.to_numeric, errors="coerce").fillna(0)
        last = pd.to_numeric(df[cands[-1]], errors="coerce").fillna(0)
        active = (M.sum(axis=1) > 0) | (last > 0)
        if active.sum() >= 20:
            close = (np.abs(M.mean(axis=1) - last) <= 0.51)[active].mean()
            decimals = ((last % 1) != 0)[active].mean()
            if close >= 0.9 and decimals >= 0.2:
                dropped = cands.pop()
                for d in diagnostics:
                    if d["Column"] == dropped:
                        d["Accepted"] = "No"
                        d["Reason"] = "trailing monthly-average column"

    diag_df = pd.DataFrame(diagnostics)
    return cands, diag_df


# ---------------------------------------------------------------------------
# Core demand cleaning (product-by-product)
# ---------------------------------------------------------------------------
def _analyse_product(S: np.ndarray, stock: np.ndarray, eol: np.ndarray) -> Dict:
    """S: branches × months. Returns avg, raw, used, flags."""
    B, T = S.shape
    net = S.sum(axis=0)
    nz = S > 0
    n_nz = nz.sum(axis=1)
    base = np.array([np.median(S[r][nz[r]]) if n_nz[r] else 0.0 for r in range(B)])
    min_nz = min(2 if T <= 4 else 3, T)
    flags = np.full((B, T), "", dtype=object)
    cens = np.zeros((B, T), dtype=bool)

    # 1) stockout / not-listed / end-of-supply
    for r in range(B):
        if n_nz[r] == 0:
            continue
        first_nz = np.where(nz[r])[0].min()
        last_nz = np.where(nz[r])[0].max()
        trailing = np.zeros(T, bool)
        trailing[last_nz + 1:] = True

        if eol[r]:
            m = trailing & (S[r] == 0)
            cens[r] |= m
            flags[r, m] = "EN"
            continue

        if n_nz[r] < min_nz:
            continue

        other = net - S[r]
        pos = other[other > 0]
        alive = (other >= ALIVE_RATIO * np.median(pos)) if len(pos) else np.zeros(T, bool)
        weak = (S[r] == 0) | (S[r] < LOW_FRACTION * base[r])
        m = weak & alive
        if stock[r] <= 0:
            m |= trailing & (S[r] == 0)
        lead = np.arange(T) < first_nz
        cens[r] |= m
        flags[r, m & lead] = "NL"
        flags[r, m & ~lead] = "SO"

    valid = ~cens
    adj = S.astype(float).copy()

    # 2) promo / event months
    elig = (base > 0) & (n_nz >= 2)
    if T >= MIN_MONTHS_FOR_SPIKES and elig.sum() >= MIN_BRANCHES_FOR_PROMO:
        u = np.full(T, np.nan)
        for m in range(T):
            rows = elig & valid[:, m]
            if rows.sum() >= MIN_BRANCHES_FOR_PROMO:
                u[m] = np.median(S[rows, m] / base[rows])
        ok = ~np.isnan(u)
        if ok.sum() >= MIN_MONTHS_FOR_SPIKES:
            med = np.median(u[ok])
            mad = np.median(np.abs(u[ok] - med))
            thr = max(PROMO_RATIO * med, med + BULK_SIGMA * 1.4826 * mad)
            for m in (np.where(ok & (u > thr))[0] if med > 0 else []):
                hit = valid[:, m] & (S[:, m] > 0)
                adj[hit, m] = S[hit, m] * (med / u[m])
                flags[hit, m] = "PR"

    # 3) bulk / one-off spikes in a single branch
    for r in range(B):
        idx = np.where(valid[r] & (adj[r] > 0))[0]
        if len(idx) >= MIN_MONTHS_FOR_SPIKES:
            vals = adj[r, idx]
            med = np.median(vals)
            mad = np.median(np.abs(vals - med))
            bound = max(med + BULK_SIGMA * 1.4826 * mad, 2 * med, med + 2)
            over = vals > bound
            if over.any():
                adj[r, idx[over]] = bound
                for j in idx[over]:
                    if flags[r, j] == "":
                        flags[r, j] = "BK"

    avg = np.array([adj[r, valid[r]].mean() if valid[r].any() else 0.0 for r in range(B)])
    return {
        "avg": avg,
        "raw": S.mean(axis=1),
        "used": valid.sum(axis=1),
        "flags": flags,
    }


# ---------------------------------------------------------------------------
# Public: load & prepare
# ---------------------------------------------------------------------------
def load_and_prepare_v2(
    uploaded,
    exclude_cols: Sequence[str] = (),
    status_col: Optional[str] = None,
    force_months: Sequence[str] = (),
):
    """
    Returns (df, error_string_or_None).
    df has one row per Branch × Product with a clean Monthly_Avg.
    Audit tables live in df.attrs.
    """
    try:
        xl = pd.ExcelFile(uploaded)
        sname, tname = _find_sheets(xl)
        sales_raw = _read_sheet(xl, sname)
        stock_raw = _read_sheet(xl, tname)
    except Exception as e:
        return None, f"Could not read the workbook: {e}"

    sb = _pick(sales_raw.columns, KEY_BRANCH)
    sm = _pick(sales_raw.columns, KEY_MODEL)
    tb = _pick(stock_raw.columns, KEY_BRANCH)   # may be None for wide format
    tm = _pick(stock_raw.columns, KEY_MODEL)

    if not (sb and sm):
        return None, (
            f"Sales sheet '{sname}': could not find Branch / Model columns. "
            f"Found: {list(sales_raw.columns)}"
        )
    if not tm:
        return None, (
            f"Stocks sheet '{tname}': could not find a Model / SKU column. "
            f"Found: {list(stock_raw.columns)}"
        )

    s_brand = _pick(sales_raw.columns, KEY_BRAND, [sb, sm])
    s_group = _pick(sales_raw.columns, KEY_GROUP, [sb, sm, s_brand])
    idc = {c for c in (sb, sm, s_brand, s_group) if c}
    months, month_diag = _month_cols(sales_raw, idc | set(exclude_cols), force_months=force_months)

    if not months:
        return None, (
            f"No month columns found on '{sname}'. Columns seen: {list(sales_raw.columns)}. "
            "Use the 'Force these columns…' box if a month was missed."
        )

    # ---- Sales ----
    M = sales_raw[months].apply(pd.to_numeric, errors="coerce").fillna(0)
    sales = pd.DataFrame({
        "Branch": sales_raw[sb].astype(str).str.strip().str.upper(),
        "Product_Key": sales_raw[sm].astype(str).str.strip().str.upper(),
        "Model No": sales_raw[sm].astype(str).str.strip(),
        "Brand": sales_raw[s_brand].astype(str).str.strip() if s_brand else "",
        "ItemGroup1": sales_raw[s_group].astype(str).str.strip() if s_group else "",
    })
    sales = pd.concat([sales, M], axis=1)
    sales = sales[~sales["Branch"].isin(["", "NAN"]) & ~sales["Product_Key"].isin(["", "NAN"])]
    agg = {"Model No": "first", "Brand": _first, "ItemGroup1": _first, **{m: "sum" for m in months}}
    sales = sales.groupby(["Branch", "Product_Key"], as_index=False).agg(agg)

    # ---- Stock ----
    # Support BOTH long format (has a Branch column) and wide format (branch names as columns).
    t_brand = _pick(stock_raw.columns, KEY_BRAND, [tm] if tm else [])
    t_group = _pick(stock_raw.columns, KEY_GROUP, [c for c in (tm, t_brand) if c])

    # Status: user override → auto-detect → search other sheets
    t_status = None
    status_source = ""
    if status_col and status_col in stock_raw.columns:
        t_status = status_col
        status_source = f"Stocks sheet column '{status_col}' (user override)"
    else:
        t_status = _pick(stock_raw.columns, KEY_STATUS, [c for c in (tm, t_brand) if c])
        if t_status:
            status_source = f"Stocks sheet column '{t_status}'"

    # Fall back: look for a status column on any other sheet
    if t_status is None:
        for sh in xl.sheet_names:
            if sh in (sname, tname):
                continue
            try:
                other = _read_sheet(xl, sh)
                cand = _pick(other.columns, KEY_STATUS)
                if cand:
                    om = _pick(other.columns, KEY_MODEL)
                    if om:
                        tmp = other[[om, cand]].copy()
                        tmp[om] = tmp[om].astype(str).str.strip().str.upper()
                        tmp[cand] = tmp[cand].astype(str).str.strip()
                        status_map = (
                            tmp[tmp[cand] != ""]
                            .groupby(om)[cand]
                            .first()
                            .to_dict()
                        )
                        stock_raw["_status_lookup"] = (
                            stock_raw[tm].astype(str).str.strip().str.upper().map(status_map).fillna("")
                        )
                        t_status = "_status_lookup"
                        status_source = f"sheet '{sh}' column '{cand}' (lookup by model)"
                        break
            except Exception:
                continue

    # Detect wide vs long format
    has_branch_col = tb is not None
    # Also treat as long if a clear quantity column exists alongside Branch
    sup_cols = [c for c in stock_raw.columns if "supplier" in _clean(c)]
    t_qty = _pick(
        stock_raw.columns,
        KEY_QTY,
        [c for c in (tb, tm, t_status, *sup_cols) if c],
    )

    if has_branch_col and t_qty:
        # ----- LONG FORMAT -----
        stock = pd.DataFrame({
            "Branch": stock_raw[tb].astype(str).str.strip().str.upper(),
            "Product_Key": stock_raw[tm].astype(str).str.strip().str.upper(),
            "Model No_s": stock_raw[tm].astype(str).str.strip(),
            "Brand_s": stock_raw[t_brand].astype(str).str.strip() if t_brand else "",
            "ItemGroup1_s": stock_raw[t_group].astype(str).str.strip() if t_group else "",
            "Supplier_Status": (
                stock_raw[t_status].astype(str).str.strip() if t_status else ""
            ),
            "Current_Stock": pd.to_numeric(stock_raw[t_qty], errors="coerce").fillna(0),
        })
    else:
        # ----- WIDE FORMAT (branch names as columns) -----
        id_vars = [tm]
        if t_brand:
            id_vars.append(t_brand)
        if t_group:
            id_vars.append(t_group)
        if t_status and t_status in stock_raw.columns:
            id_vars.append(t_status)

        branch_cols = [
            c for c in stock_raw.columns
            if c not in id_vars
            and "total" not in str(c).lower()
            and not str(c).lower().startswith("unnamed")
            and "status" not in _clean(c)
            and "warehouse" not in _clean(c)
            and "display" not in _clean(c)
        ]
        if not branch_cols:
            return None, (
                f"Stocks sheet '{tname}': could not find branch stock columns. "
                f"Found: {list(stock_raw.columns)}"
            )

        wide = stock_raw.copy()
        rename = {tm: "Model No_s"}
        if t_brand:
            rename[t_brand] = "Brand_s"
        if t_group:
            rename[t_group] = "ItemGroup1_s"
        if t_status and t_status in wide.columns:
            rename[t_status] = "Supplier_Status"
        wide = wide.rename(columns=rename)
        if "Brand_s" not in wide.columns:
            wide["Brand_s"] = ""
        if "ItemGroup1_s" not in wide.columns:
            wide["ItemGroup1_s"] = ""
        if "Supplier_Status" not in wide.columns:
            wide["Supplier_Status"] = ""

        for col in ["Model No_s", "Brand_s", "ItemGroup1_s", "Supplier_Status"]:
            wide[col] = wide[col].fillna("").astype(str).str.strip()

        wide["Product_Key"] = wide["Model No_s"].str.upper()

        stock = wide.melt(
            id_vars=["Product_Key", "Model No_s", "Brand_s", "ItemGroup1_s", "Supplier_Status"],
            value_vars=branch_cols,
            var_name="Branch",
            value_name="Current_Stock",
        )
        stock["Branch"] = stock["Branch"].astype(str).str.strip().str.upper()
        stock["Current_Stock"] = (
            pd.to_numeric(
                stock["Current_Stock"].replace(r"^\s*-\s*$", 0, regex=True),
                errors="coerce",
            )
            .fillna(0)
            .clip(lower=0)
        )
        # Drop residual "Total" style columns that slipped through
        stock = stock[~stock["Branch"].str.contains("TOTAL", case=False, na=False)]

    stock = stock[~stock["Branch"].isin(["", "NAN"]) & ~stock["Product_Key"].isin(["", "NAN"])]
    stock = stock.groupby(["Branch", "Product_Key"], as_index=False).agg({
        "Model No_s": "first",
        "Brand_s": _first,
        "ItemGroup1_s": _first,
        "Supplier_Status": _first,
        "Current_Stock": "sum",
    })

    # Normalise Product_Key on sales side the same way (model only) so wide/long both match
    # (Brand + Group can differ slightly between sheets)
    sales["Product_Key"] = sales["Model No"].astype(str).str.strip().str.upper()

    full = sales.merge(stock, on=["Branch", "Product_Key"], how="outer")
    full[months] = full[months].fillna(0)
    full["Current_Stock"] = full["Current_Stock"].fillna(0)

    for a, b in (("Model No", "Model No_s"), ("Brand", "Brand_s"), ("ItemGroup1", "ItemGroup1_s")):
        full[a] = full[a].where(full[a].fillna("").astype(str).str.strip() != "", full[b]).fillna("")
    full = full.drop(columns=["Model No_s", "Brand_s", "ItemGroup1_s"], errors="ignore")
    full["Supplier_Status"] = full["Supplier_Status"].fillna("").astype(str).str.strip()
    full.loc[full["Supplier_Status"].str.lower().isin(["nan", "none", ""]), "Supplier_Status"] = ""

    # Propagate non-blank status by Product_Key
    pmap = full[full["Supplier_Status"] != ""].groupby("Product_Key")["Supplier_Status"].first()
    blank = full["Supplier_Status"] == ""
    filled = blank.sum()
    full.loc[blank, "Supplier_Status"] = full.loc[blank, "Product_Key"].map(pmap).fillna("")
    full["Is_EOL"] = full["Supplier_Status"].map(_is_eol_text)
    full = full.reset_index(drop=True)

    # ---- Clean demand ----
    Sall = full[months].to_numpy(float).clip(min=0)
    stk = full["Current_Stock"].to_numpy(float)
    eol = full["Is_EOL"].to_numpy(bool)
    n, T = len(full), len(months)
    avg = np.zeros(n)
    raw = np.zeros(n)
    used = np.zeros(n, int)
    flg = np.full((n, T), "", dtype=object)

    for _, pos in full.groupby("Product_Key").indices.items():
        res = _analyse_product(Sall[pos], stk[pos], eol[pos])
        avg[pos] = res["avg"]
        raw[pos] = res["raw"]
        used[pos] = res["used"]
        flg[pos] = res["flags"]

    def _cnt(code):
        return (flg == code).sum(axis=1)

    full["Total_Sold"] = Sall.sum(axis=1)
    full["Months_Uploaded"] = T
    full["Months_Used"] = used
    full["Stockout_Months_Excluded"] = _cnt("SO")
    full["Not_Listed_Months_Excluded"] = _cnt("NL")
    full["EOL_Months_Excluded"] = _cnt("EN")
    full["Promo_Months_Normalised"] = _cnt("PR")
    full["Bulk_Months_Capped"] = _cnt("BK")
    full["Raw_Monthly_Avg"] = raw
    full["Monthly_Avg"] = avg
    full["Confidence"] = np.where(used >= 6, "High", np.where(used >= 3, "Medium", "Low"))

    notes = []
    for i in range(n):
        p = []
        if full.at[i, "Stockout_Months_Excluded"]:
            p.append(f"{full.at[i, 'Stockout_Months_Excluded']} stockout mth(s) excluded")
        if full.at[i, "Not_Listed_Months_Excluded"]:
            p.append(f"{full.at[i, 'Not_Listed_Months_Excluded']} not-yet-listed mth(s) excluded")
        if full.at[i, "EOL_Months_Excluded"]:
            p.append(f"{full.at[i, 'EOL_Months_Excluded']} end-of-supply mth(s) excluded")
        if full.at[i, "Promo_Months_Normalised"]:
            p.append(f"{full.at[i, 'Promo_Months_Normalised']} promo mth(s) normalised")
        if full.at[i, "Bulk_Months_Capped"]:
            p.append(f"{full.at[i, 'Bulk_Months_Capped']} bulk mth(s) capped")
        notes.append("; ".join(p))
    full["Adjustment_Note"] = notes

    # Audit tables
    ids = ["Branch", "Brand", "ItemGroup1", "Model No"]
    enriched = pd.concat([
        full[ids],
        full[months],
        full[[
            "Months_Uploaded", "Stockout_Months_Excluded", "Not_Listed_Months_Excluded",
            "Promo_Months_Normalised", "Bulk_Months_Capped", "Raw_Monthly_Avg", "Monthly_Avg",
        ]].rename(columns={"Monthly_Avg": "Clean_Monthly_Avg"}),
    ], axis=1)
    enriched["Raw_Monthly_Avg"] = enriched["Raw_Monthly_Avg"].round(2)
    enriched["Clean_Monthly_Avg"] = enriched["Clean_Monthly_Avg"].round(2)
    flags_df = pd.concat([full[ids].reset_index(drop=True), pd.DataFrame(flg, columns=months)], axis=1)

    full.attrs.update({
        "months": months,
        "sales_sheet": sname,
        "stock_sheet": tname,
        "enriched": enriched,
        "flags": flags_df,
        "month_diagnostics": month_diag,
        "stock_columns": list(stock_raw.columns),
        "status_source": status_source,
        "status_rows_filled_by_lookup": int(filled),
    })
    return full, None


# ---------------------------------------------------------------------------
# Status computation
# ---------------------------------------------------------------------------
def compute_status_v2(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    cover = np.where(
        d["Monthly_Avg"] > 0,
        d["Current_Stock"] / d["Monthly_Avg"].where(d["Monthly_Avg"] > 0, 1),
        np.nan,
    )
    d["Months_Cover"] = cover
    status = np.select(
        [
            d["Is_EOL"],
            (d["Current_Stock"] <= 0) & (d["Monthly_Avg"] > 0),
            (d["Current_Stock"] <= 0),
            d["Total_Sold"] <= 0,
            d["Monthly_Avg"] < SLOW_UNITS_PER_MONTH,
            d["Months_Cover"] > OVERSTOCK_MONTHS,
        ],
        ["EOL / Run-down", "Stockout", "No Stock / No Demand", "Dead Stock", "Slow-moving", "Overstock"],
        default="Healthy",
    )
    d["Status"] = status
    d.attrs = dict(df.attrs)
    return d


def month_flag_summary(flags_df: pd.DataFrame, months: Sequence[str]) -> pd.DataFrame:
    rows = []
    for m in months:
        col = flags_df[m]
        rows.append({
            "Month": m,
            "Stockout (excluded)": int((col == "SO").sum()),
            "Not yet listed (excluded)": int((col == "NL").sum()),
            "Promo (normalised)": int((col == "PR").sum()),
            "Bulk (capped)": int((col == "BK").sum()),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Excel export helpers
# ---------------------------------------------------------------------------
def build_enriched_sales_excel(meta: dict) -> bytes:
    enriched = meta["enriched"]
    flags_df = meta["flags"]
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as w:
        enriched.to_excel(w, sheet_name="Sales_With_Clean_Avg", index=False)
        flags_df.to_excel(w, sheet_name="Month_Flags", index=False)
        legend = pd.DataFrame({
            "Code": ["SO", "NL", "EN", "PR", "BK", "(blank)"],
            "Meaning": [
                "Stockout month – excluded from the average (others were selling normally)",
                "Not listed yet – zero before the branch first sold; excluded",
                "End of supply (EOL/discontinued) – trailing zeros excluded",
                "Promo / event month – network-wide spike normalised to normal level",
                "Bulk / one-off sale in this branch – capped at the normal upper bound",
                "Normal month – used as is",
            ],
        })
        legend.to_excel(w, sheet_name="Legend", index=False)
        for ws in w.book.worksheets:
            ws.freeze_panes = "E2" if ws.title != "Legend" else "A2"
            for c in ws[1]:
                c.font = Font(bold=True)
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = 14 if ws.title != "Legend" else 70
    return bio.getvalue()


# ---------------------------------------------------------------------------
# Replenishment / order planning
# ---------------------------------------------------------------------------
def plan_replenishment(
    df: pd.DataFrame,
    lead_days: float = 14,
    safety_days: float = 7,
    review_days: float = 30,
    max_cover_months: float = 4.0,
    min_display: int = 1,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Returns (plan, transfers_df, plan_summary).

    Logic:
    - Target cover = lead + safety + review (in days) → converted to units via clean Monthly_Avg.
    - Excess = stock above max_cover_months of demand (or display minimum for sellers).
    - Shortages are filled first by transferring excess from other branches.
    - Only the residual shortage becomes ORDER_QTY.
    - EOL items are never ordered; NEW listings (very low history) are never donors.
    """
    d = df.copy()
    daily = d["Monthly_Avg"] / 30.0
    cover_days = lead_days + safety_days + review_days
    d["Reorder_Point"] = (daily * (lead_days + safety_days)).apply(lambda x: math.ceil(x) if x > 0 else 0)
    d["Target_Stock"] = (daily * cover_days).apply(lambda x: math.ceil(x) if x > 0 else 0)
    d["Max_Stock"] = (daily * max_cover_months * 30).apply(lambda x: math.ceil(x) if x > 0 else 0)

    # Ensure sellers keep at least min_display
    sellers = d["Monthly_Avg"] > 0
    d.loc[sellers, "Target_Stock"] = np.maximum(d.loc[sellers, "Target_Stock"], min_display)
    d.loc[sellers, "Max_Stock"] = np.maximum(d.loc[sellers, "Max_Stock"], min_display)

    d["Need"] = np.maximum(0, d["Target_Stock"] - d["Current_Stock"]).astype(int)
    d["Excess"] = np.where(
        d["Is_EOL"] | (d["Months_Used"] < 2),
        0,
        np.maximum(0, d["Current_Stock"] - d["Max_Stock"]),
    ).astype(int)

    # Build transfer recommendations (greedy: highest need first, lowest excess first)
    transfers = []
    excess_pool = d[d["Excess"] > 0][["Product_Key", "Branch", "Excess", "Brand", "ItemGroup1", "Model No"]].copy()
    need_pool = d[(d["Need"] > 0) & (~d["Is_EOL"])][
        ["Product_Key", "Branch", "Need", "Brand", "ItemGroup1", "Model No", "Monthly_Avg"]
    ].copy()

    for key, need_grp in need_pool.groupby("Product_Key"):
        donors = excess_pool[excess_pool["Product_Key"] == key].sort_values("Excess", ascending=False)
        if donors.empty:
            continue
        receivers = need_grp.sort_values("Monthly_Avg", ascending=False)
        for _, rec in receivers.iterrows():
            remaining = int(rec["Need"])
            for didx, don in donors.iterrows():
                if remaining <= 0:
                    break
                can = int(donors.at[didx, "Excess"])
                if can <= 0:
                    continue
                give = min(remaining, can)
                if give > 0:
                    transfers.append({
                        "From Branch": don["Branch"],
                        "To Branch": rec["Branch"],
                        "Brand": rec["Brand"],
                        "ItemGroup1": rec["ItemGroup1"],
                        "Model No": rec["Model No"],
                        "Qty": give,
                        "Receiver Monthly Avg": round(float(rec["Monthly_Avg"]), 2),
                    })
                    donors.at[didx, "Excess"] -= give
                    excess_pool.loc[didx, "Excess"] -= give
                    remaining -= give
            # update need after transfers
            d.loc[
                (d["Product_Key"] == key) & (d["Branch"] == rec["Branch"]),
                "Need",
            ] = remaining

    transfers_df = pd.DataFrame(transfers)
    if transfers_df.empty:
        transfers_df = pd.DataFrame(columns=[
            "From Branch", "To Branch", "Brand", "ItemGroup1", "Model No", "Qty", "Receiver Monthly Avg"
        ])

    # Transfer_In / Transfer_Out aggregates
    tin = transfers_df.groupby("To Branch").agg(Transfer_In=("Qty", "sum")) if len(transfers_df) else pd.DataFrame()
    tout = transfers_df.groupby("From Branch").agg(Transfer_Out=("Qty", "sum")) if len(transfers_df) else pd.DataFrame()

    # After transfers, residual need becomes order qty
    d["Transfer_In"] = 0
    d["Transfer_Out"] = 0
    if len(transfers_df):
        tin_map = transfers_df.groupby(["To Branch", "Brand", "ItemGroup1", "Model No"])["Qty"].sum()
        tout_map = transfers_df.groupby(["From Branch", "Brand", "ItemGroup1", "Model No"])["Qty"].sum()
        for idx, row in d.iterrows():
            k = (row["Branch"], row["Brand"], row["ItemGroup1"], row["Model No"])
            d.at[idx, "Transfer_In"] = int(tin_map.get(k, 0))
            d.at[idx, "Transfer_Out"] = int(tout_map.get(k, 0))

    d["ORDER_QTY"] = np.where(
        d["Is_EOL"],
        0,
        np.maximum(0, d["Need"] - d["Transfer_In"]).astype(int),
    )

    # Priority
    def _prio(r):
        if r["Current_Stock"] <= 0 and r["Monthly_Avg"] > 0 and r["ORDER_QTY"] + r["Transfer_In"] > 0:
            return "1-CRITICAL"
        if r["Current_Stock"] <= r["Reorder_Point"] and r["Monthly_Avg"] > 0:
            return "2-HIGH"
        if r["ORDER_QTY"] > 0:
            return "3-NORMAL"
        if r["Transfer_In"] > 0 or r["Transfer_Out"] > 0:
            return "4-TRANSFER ONLY"
        return "5-OK"

    d["Priority"] = d.apply(_prio, axis=1)
    d["Clean_Monthly_Avg"] = d["Monthly_Avg"].round(2)

    plan_cols = [
        "Branch", "Brand", "ItemGroup1", "Model No", "Supplier_Status",
        "Clean_Monthly_Avg", "Current_Stock", "Reorder_Point", "Target_Stock",
        "Transfer_In", "Transfer_Out", "ORDER_QTY", "Priority", "Status",
    ]
    plan = d[d["ORDER_QTY"] + d["Transfer_In"] + d["Transfer_Out"] > 0][plan_cols].copy()
    plan = plan.sort_values(["Priority", "Clean_Monthly_Avg"], ascending=[True, False]).reset_index(drop=True)

    # Branch summary
    if len(plan):
        plan_summary = plan.groupby("Branch", as_index=False).agg(
            Order_Lines=("ORDER_QTY", lambda s: (s > 0).sum()),
            Order_Units=("ORDER_QTY", "sum"),
            Transfer_In_Units=("Transfer_In", "sum"),
            Transfer_Out_Units=("Transfer_Out", "sum"),
            Critical_Lines=("Priority", lambda s: (s == "1-CRITICAL").sum()),
        ).sort_values("Order_Units", ascending=False)
    else:
        plan_summary = pd.DataFrame(columns=[
            "Branch", "Order_Lines", "Order_Units", "Transfer_In_Units",
            "Transfer_Out_Units", "Critical_Lines",
        ])

    return plan, transfers_df, plan_summary


def build_branch_order_book(plan: pd.DataFrame, transfers_df: pd.DataFrame, plan_summary: pd.DataFrame) -> bytes:
    """One Excel sheet per branch + a summary sheet."""
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as w:
        plan_summary.to_excel(w, sheet_name="Summary", index=False)
        if len(transfers_df):
            transfers_df.to_excel(w, sheet_name="All_Transfers", index=False)

        branches = sorted(plan["Branch"].unique()) if len(plan) else []
        for br in branches:
            safe = re.sub(r"[^\w\s-]", "", str(br))[:28] or "Branch"
            sheet_name = safe
            # avoid collisions
            i = 1
            while sheet_name in w.book.sheetnames:
                sheet_name = f"{safe[:25]}_{i}"
                i += 1

            br_plan = plan[plan["Branch"] == br]
            br_plan.to_excel(w, sheet_name=sheet_name, index=False)

            # also append transfers involving this branch
            if len(transfers_df):
                br_t = transfers_df[
                    (transfers_df["From Branch"] == br) | (transfers_df["To Branch"] == br)
                ]
                if len(br_t):
                    start = len(br_plan) + 3
                    br_t.to_excel(w, sheet_name=sheet_name, index=False, startrow=start)

        for ws in w.book.worksheets:
            for c in ws[1]:
                c.font = Font(bold=True)
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = 14
    return bio.getvalue()
