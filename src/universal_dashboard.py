from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(
    page_title="Universal Analytics Studio",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SUPPORTED = {".csv", ".xlsx", ".xls", ".json"}
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Keep the UI lightweight: avoid external font downloads and expensive CSS effects.
st.markdown("""
<style>
html, body, [class*="css"] { font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; }
.stApp { background: radial-gradient(circle at 85% 0%,rgba(105,76,255,.13),transparent 30%), linear-gradient(135deg,#070d1c,#0c1730 65%,#111b35); color:#edf2ff; }
[data-testid="stHeader"] { background:rgba(7,13,28,.85); }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#111f3d,#0a1429); border-right:1px solid #273657; }
[data-testid="stMetric"] { background:linear-gradient(135deg,#1b2c50,#131f38); padding:14px; border:1px solid #2a3a5d; border-radius:14px; }
.hero { padding:26px 30px; border-radius:20px; border:1px solid #344574; background:linear-gradient(110deg,rgba(27,48,91,.96),rgba(44,30,91,.86)); margin:8px 0 20px; }
.hero h1 { color:white; font-size:2.1rem; font-weight:800; margin:0; }
.hero p { color:#bdcbed; margin:8px 0 0; }
.eyebrow { color:#a9b8ff; font-size:.72rem; letter-spacing:2px; font-weight:800; }
.stButton>button,.stDownloadButton>button { border-radius:10px; border:1px solid #6576ff; background:linear-gradient(100deg,#4c65ed,#7847e8); color:white; font-weight:700; min-height:40px; }
div[data-testid="stTextInput"] input { border-radius:10px!important; border:1px solid #38496e!important; background:#111d34!important; color:#fff!important; }
.section { font-size:1.08rem; font-weight:800; margin:18px 0 10px; }
.source-card { border:1px solid #2d3d62; border-radius:14px; background:linear-gradient(140deg,#172746,#111a31); padding:16px; min-height:125px; }
[data-testid="stDataFrame"] { border:1px solid #2d3d62; border-radius:10px; }
</style>
""", unsafe_allow_html=True)


def json_df(payload):
    if isinstance(payload, list):
        if payload and all(isinstance(x, dict) for x in payload):
            return pd.json_normalize(payload, max_level=1)
        return pd.DataFrame({"value": payload})
    if isinstance(payload, dict):
        for key in ("data", "results", "records", "items", "products", "users", "posts"):
            value = payload.get(key)
            if isinstance(value, list) and value and all(isinstance(x, dict) for x in value):
                return pd.json_normalize(value, max_level=1)
        for value in payload.values():
            if isinstance(value, list) and value and all(isinstance(x, dict) for x in value):
                return pd.json_normalize(value, max_level=1)
        return pd.json_normalize(payload, max_level=1)
    return pd.DataFrame({"value": [payload]})


def normalize(df):
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.duplicated()]
    # Only inspect object columns; avoid a Python-level map over numeric columns.
    for col in df.select_dtypes(include=["object"]).columns:
        sample = df[col].dropna()
        if not sample.empty and sample.map(lambda x: isinstance(x, (dict, list))).any():
            df[col] = df[col].map(
                lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else x
            )
    return df


@st.cache_data(show_spinner=False, max_entries=24)
def read_file_cached(path_string: str, modified_ns: int, file_size: int):
    """Cache file parsing; mtime/size make changed files invalidate the cache."""
    path = Path(path_string)
    ext = path.suffix.lower()
    if ext == ".csv":
        frame = pd.read_csv(path, low_memory=False)
    elif ext in {".xlsx", ".xls"}:
        frame = pd.read_excel(path)
    elif ext == ".json":
        frame = normalize(json_df(json.loads(path.read_text(encoding="utf-8"))))
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    return normalize(frame)


def read_file(path: Path):
    stat = path.stat()
    return read_file_cached(str(path), stat.st_mtime_ns, stat.st_size)


@st.cache_data(show_spinner=False, ttl=300, max_entries=12)
def fetch_api_cached(url: str):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Enter a complete http:// or https:// URL.")
    response = requests.get(
        url,
        timeout=(4, 15),
        headers={"Accept": "application/json", "User-Agent": "UniversalAnalyticsStudio/1.0"},
    )
    response.raise_for_status()
    try:
        payload = response.json()
    except requests.exceptions.JSONDecodeError as exc:
        raise ValueError("This URL did not return JSON. Use a JSON API endpoint.") from exc
    frame = normalize(json_df(payload))
    if frame.empty or len(frame.columns) == 0:
        raise ValueError("The API returned JSON, but no tabular records were detected.")
    return frame


def scan_files():
    try:
        return {
            path.name: path
            for path in sorted(DATA_DIR.iterdir())
            if path.is_file() and path.suffix.lower() in SUPPORTED
        }
    except OSError:
        return {}


@st.cache_data(show_spinner=False, max_entries=24)
def prepare_cached(frame: pd.DataFrame):
    df = frame.copy()
    nums = df.select_dtypes(include="number").columns.tolist()
    dates = []

    for col in df.columns:
        if col not in nums and any(word in col.lower() for word in ("date", "time", "created", "updated", "timestamp")):
            parsed = pd.to_datetime(df[col], errors="coerce")
            if len(parsed) and parsed.notna().mean() >= 0.7:
                df[col] = parsed
                dates.append(col)

    for col in df.columns:
        if col not in nums and col not in dates and (
            pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col])
        ):
            nonempty = df[col].notna().sum()
            if nonempty:
                parsed = pd.to_numeric(df[col], errors="coerce")
                if parsed.notna().sum() / nonempty >= 0.9:
                    df[col] = parsed
                    nums.append(col)

    max_categories = min(100, max(15, int(len(df) * 0.5)))
    cats = [
        col for col in df.columns
        if col not in nums and col not in dates
        and df[col].nunique(dropna=True) <= max_categories
    ]
    return df, nums, dates, cats


def layout(fig, height=330):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e3eaff", family="Inter"),
        margin=dict(l=10, r=10, t=46, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="rgba(150,170,220,.12)"),
        yaxis=dict(gridcolor="rgba(150,170,220,.12)"),
    )
    return fig


def make_catalog(file_map, uploads, api_datasets):
    catalog, errors = {}, {}
    for name, path in file_map.items():
        try:
            catalog[name] = read_file(path)
        except Exception as exc:
            errors[name] = str(exc)

    for upload in uploads or []:
        try:
            upload.seek(0)
            if upload.name.lower().endswith(".csv"):
                frame = pd.read_csv(upload, low_memory=False)
            elif upload.name.lower().endswith((".xlsx", ".xls")):
                frame = pd.read_excel(upload)
            else:
                frame = json_df(json.load(upload))
            catalog[f"Upload · {upload.name}"] = normalize(frame)
        except Exception as exc:
            errors[upload.name] = str(exc)

    catalog.update(api_datasets)
    return catalog, errors


if "page" not in st.session_state:
    st.session_state.page = "source"
if "chosen_source" not in st.session_state:
    st.session_state.chosen_source = None
if "api_datasets" not in st.session_state:
    st.session_state.api_datasets = {}

# Scan the directory once per rerun, not repeatedly in the sidebar and page.
file_map = scan_files()

with st.sidebar:
    st.markdown("## 🧭 ANALYTICS WORKSPACE")
    st.caption("One engine for files and JSON APIs")
    if st.button("① Choose data source", use_container_width=True):
        st.session_state.page = "source"
        st.rerun()
    if st.button("② Open analytics dashboard", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()

    st.divider()
    st.markdown("### 📁 Local datasets")
    st.caption(f"Folder: {DATA_DIR}")
    if st.button("↻ Refresh local files", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.write(f"**{len(file_map)} file(s) detected**")
    st.caption("CSV · XLSX · XLS · JSON")
    uploads = st.file_uploader(
        "Add files for this session",
        type=["csv", "xlsx", "xls", "json"],
        accept_multiple_files=True,
    )

    st.divider()
    st.markdown("### 🌐 JSON API source")
    api_url = st.text_input(
        "API endpoint URL",
        key="api_url",
        placeholder="https://dummyjson.com/products?limit=100",
        help="Must return JSON. A normal webpage URL is not enough.",
    )
    if st.button("⚡ Fetch API data", use_container_width=True):
        if not api_url.strip():
            st.error("Paste an API URL first.")
        else:
            try:
                with st.spinner("Connecting to API…"):
                    frame = fetch_api_cached(api_url.strip())
                    source_name = f"API · {api_url.strip()}"
                    st.session_state.api_datasets[source_name] = frame
                    st.session_state.chosen_source = source_name
                    st.session_state.page = "dashboard"
                st.success(f"Loaded {len(frame):,} records.")
                st.rerun()
            except Exception as exc:
                st.error(f"API error: {exc}")
    if st.session_state.api_datasets:
        st.caption(f"{len(st.session_state.api_datasets)} API dataset(s) loaded this session")

catalog, errors = make_catalog(file_map, uploads, st.session_state.api_datasets)

if st.session_state.page == "source":
    st.markdown(
        '<div class="hero"><div class="eyebrow">MULTI-SOURCE DATA INTELLIGENCE</div>'
        '<h1>📊 Universal Analytics Studio</h1>'
        '<p>Choose a source once. Explore it on a dedicated analytics page.</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section">01 / Choose your data source</div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    with a:
        st.markdown('<div class="source-card"><h3>📄 File dataset</h3><p>CSV, Excel or JSON files from your data folder or uploader.</p></div>', unsafe_allow_html=True)
        if st.button("Use a local file →", key="localgo", use_container_width=True):
            st.session_state.source_mode = "file"
    with b:
        st.markdown('<div class="source-card"><h3>🌐 JSON API</h3><p>Fetch records from a JSON endpoint and explore them automatically.</p></div>', unsafe_allow_html=True)
        if st.button("Use an API →", key="apigo", use_container_width=True):
            st.session_state.source_mode = "api"
    with c:
        st.markdown('<div class="source-card"><h3>🧩 Universal engine</h3><p>Automatic profiling, data quality, filters, charts and downloads.</p></div>', unsafe_allow_html=True)
        if st.button("Explore available data →", key="explorego", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

    mode = st.session_state.get("source_mode", "file")
    if mode == "api":
        st.info("Enter a JSON API URL in the sidebar and click **Fetch API data**.")
    else:
        st.markdown('<div class="section">02 / Available datasets</div>', unsafe_allow_html=True)
        if not catalog:
            st.info(f"No dataset found. Add a file to `{DATA_DIR}` or upload one in the sidebar.")
        else:
            names = list(catalog)
            current = st.session_state.chosen_source
            index = names.index(current) if current in names else 0
            picked = st.selectbox("Select a dataset to analyse", names, index=index)
            st.session_state.chosen_source = picked
            preview = catalog[picked]
            x, y, z = st.columns(3)
            x.metric("Records", f"{len(preview):,}")
            y.metric("Fields", f"{len(preview.columns):,}")
            z.metric("Missing cells", f"{int(preview.isna().sum().sum()):,}")
            st.dataframe(preview.head(8), use_container_width=True, hide_index=True)
            if st.button("Open analytics dashboard →", type="primary", use_container_width=True):
                st.session_state.page = "dashboard"
                st.rerun()
    st.stop()

st.markdown(
    '<div class="hero"><div class="eyebrow">LIVE DATA EXPLORATION · AUTOMATIC PROFILING</div>'
    '<h1>📊 Analytics Dashboard</h1>'
    '<p>Dynamic metrics · Interactive visualizations · Data quality · Export</p></div>',
    unsafe_allow_html=True,
)
for name, message in errors.items():
    st.warning(f"Could not read {name}: {message}")
if not catalog:
    st.warning("No dataset is loaded. Choose a file or fetch a JSON API.")
    st.stop()

names = list(catalog)
preferred = st.session_state.chosen_source
if preferred not in catalog:
    preferred = names[0]
selected = st.selectbox("Active dataset", names, index=names.index(preferred), key="active_dataset")
st.session_state.chosen_source = selected
raw = catalog[selected]
if raw.empty or not len(raw.columns):
    st.warning("This dataset has no tabular rows or columns.")
    st.stop()

df, nums, dates, cats = prepare_cached(raw)

with st.sidebar:
    st.divider()
    st.markdown("### 🔎 Explore & filter")
    search = st.text_input("Search across every field", key=f"search_{selected}", placeholder="⌕ Search names, values, IDs…")
    filter_cols = st.multiselect("Filter by category", cats, key=f"filtercols_{selected}")

filtered = df
if search:
    # Build a single mask without repeatedly converting the entire frame in each column operation.
    search_mask = pd.Series(False, index=df.index)
    for col in df.columns:
        search_mask |= df[col].astype("string").str.contains(search, case=False, na=False, regex=False)
    filtered = df.loc[search_mask]

for col in filter_cols:
    options = sorted(filtered[col].dropna().astype(str).unique().tolist())
    chosen = st.sidebar.multiselect(f"{col} values", options, key=f"values_{selected}_{col}")
    if chosen:
        filtered = filtered[filtered[col].astype(str).isin(chosen)]

st.caption(f"📌 Active dataset: **{selected}** · Showing **{len(filtered):,}** of **{len(df):,}** rows")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total records", f"{len(filtered):,}", delta=f"{len(filtered)-len(df):,} vs full" if len(filtered) != len(df) else None)
m2.metric("Fields", f"{len(df.columns):,}")
m3.metric("Missing cells", f"{int(filtered.isna().sum().sum()):,}")
m4.metric("Duplicate rows", f"{int(filtered.duplicated().sum()):,}")
m5.metric("Numeric fields", f"{len(nums):,}")

st.markdown('<div class="section">📊 Executive overview</div>', unsafe_allow_html=True)
left, right = st.columns(2)
with left:
    if cats:
        pie_col = st.selectbox("Composition / category", cats, key=f"pie_{selected}")
        pie = filtered[pie_col].fillna("Missing").astype(str).value_counts().head(8).rename_axis(pie_col).reset_index(name="Records")
        if not pie.empty:
            fig = px.pie(pie, names=pie_col, values="Records", hole=0.55, title=f"{pie_col} composition",
                         color_discrete_sequence=px.colors.qualitative.Bold)
            fig.update_traces(textposition="inside", textinfo="percent+label", sort=False)
            st.plotly_chart(layout(fig, 360), use_container_width=True, config={"displayModeBar": False, "responsive": True})
    else:
        st.info("No categorical field suitable for a pie chart was detected.")

with right:
    if nums:
        metric = st.selectbox("Key metric", nums, key=f"keymetric_{selected}")
        vals = pd.to_numeric(filtered[metric], errors="coerce").dropna()
        if not vals.empty:
            k1, k2, k3 = st.columns(3)
            k1.metric("Total", f"{vals.sum():,.2f}")
            k2.metric("Average", f"{vals.mean():,.2f}")
            k3.metric("Median", f"{vals.median():,.2f}")
            if cats:
                group = st.selectbox("Break down metric by", cats, key=f"groupmetric_{selected}")
                agg = filtered.groupby(group, dropna=False, observed=True)[metric].sum().nlargest(12).reset_index()
                fig = px.bar(agg, x=group, y=metric, title=f"{metric} by {group}",
                             color=group, color_discrete_sequence=px.colors.qualitative.Bold)
                fig.update_layout(showlegend=False)
                st.plotly_chart(layout(fig, 300), use_container_width=True, config={"displayModeBar": False, "responsive": True})
            else:
                # Sample very large frames for rendering; metrics above still use all filtered rows.
                plot_data = filtered[[metric]].dropna()
                if len(plot_data) > 5000:
                    plot_data = plot_data.sample(5000, random_state=7)
                fig = px.histogram(plot_data, x=metric, title=f"Distribution of {metric}",
                                   color_discrete_sequence=["#8b5cf6"])
                st.plotly_chart(layout(fig, 300), use_container_width=True, config={"displayModeBar": False, "responsive": True})
        else:
            st.info("No numeric values remain after filtering.")
    else:
        st.info("No numeric fields detected in this dataset.")

if len(nums) >= 2:
    st.markdown('<div class="section">🔗 Relationship explorer</div>', unsafe_allow_html=True)
    q1, q2 = st.columns(2)
    with q1:
        xcol = st.selectbox("Horizontal axis", nums, key=f"x_{selected}")
    with q2:
        y_options = [col for col in nums if col != xcol]
        ycol = st.selectbox("Vertical axis", y_options, key=f"y_{selected}")
    plot = filtered[[xcol, ycol]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(plot) > 5000:
        plot = plot.sample(5000, random_state=7)
    if not plot.empty:
        fig = px.scatter(plot, x=xcol, y=ycol, title=f"{ycol} vs {xcol}",
                         color_discrete_sequence=["#2dd4bf"])
        st.plotly_chart(layout(fig, 360), use_container_width=True, config={"displayModeBar": False, "responsive": True})

if dates:
    st.markdown('<div class="section">🗓️ Time trends</div>', unsafe_allow_html=True)
    dcol = st.selectbox("Date/time field", dates, key=f"date_{selected}")
    timeline = filtered[dcol].dropna()
    if not timeline.empty:
        periods = timeline.dt.to_period("M").astype(str)
        counts = periods.value_counts().sort_index().rename_axis("Period").reset_index(name="Records")
        fig = px.line(counts, x="Period", y="Records", markers=True, title="Records over time",
                      color_discrete_sequence=["#a78bfa"])
        st.plotly_chart(layout(fig, 310), use_container_width=True, config={"displayModeBar": False, "responsive": True})

with st.expander("🧹 Data quality profile", expanded=False):
    quality = pd.DataFrame({
        "Field": df.columns,
        "Data type": [str(df[col].dtype) for col in df.columns],
        "Missing": [int(df[col].isna().sum()) for col in df.columns],
        "Missing %": [round(float(df[col].isna().mean() * 100), 2) for col in df.columns],
        "Unique values": [int(df[col].nunique(dropna=True)) for col in df.columns],
    })
    st.dataframe(quality, use_container_width=True, hide_index=True)

with st.expander("📋 Searchable data table", expanded=True):
    # Limit the initial display for very large datasets, while retaining a full CSV export.
    if len(filtered) > 20000:
        st.caption("Large dataset: showing the first 20,000 rows here for responsiveness. The CSV export includes all filtered rows.")
        st.dataframe(filtered.head(20000), use_container_width=True, hide_index=True)
    else:
        st.dataframe(filtered, use_container_width=True, hide_index=True)
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Export filtered results as CSV",
        csv_bytes,
        file_name=f'{Path(selected.split(" · ")[-1]).stem[:60]}_filtered.csv',
        mime="text/csv",
        use_container_width=True,
    )

st.caption("Universal Analytics Studio · CSV · Excel · JSON · JSON APIs · Pandas · Plotly")
